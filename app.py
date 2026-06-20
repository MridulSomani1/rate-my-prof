# =============================================================================
# app.py
# -----------------------------------------------------------------------------
# This is the MAIN file — it starts the Flask web server, defines all the API
# routes the frontend talks to, and serves the HTML page.
#
# Flow of the whole app:
#   scraper.py   -> gets raw reviews
#   analyzer.py  -> scores each review with VADER
#   models.py    -> defines the database tables
#   database.py  -> connects to SQLite
#   app.py       -> ties it all together and serves it on the web
# =============================================================================

import io
import csv

from flask import Flask, jsonify, render_template, Response, abort
from flask_cors import CORS

from database import SessionLocal, init_db
from models import Professor, Review
from analyzer import analyze_sentiment
from scraper import get_reviews

# -----------------------------------------------------------------------------
# Create the Flask application.
# -----------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)  # allow the frontend to call our API (handy during development)


# -----------------------------------------------------------------------------
# Helper: load reviews from the scraper, score them, and store them in the DB.
# Called on first startup and whenever the user clicks "Refresh".
# -----------------------------------------------------------------------------
def populate_database():
    """Clear existing data, re-scrape, re-score, and save everything."""
    db = SessionLocal()
    try:
        # 1. Wipe old data so a refresh starts clean.
        db.query(Review).delete()
        db.query(Professor).delete()
        db.commit()

        # 2. Keep a small cache so we only create each professor once.
        professors_by_name = {}

        # 3. Go through every raw review from the scraper.
        for raw in get_reviews():
            name = raw["professor"]
            department = raw["department"]
            text = raw["text"]

            # Create the professor row the first time we see this name.
            if name not in professors_by_name:
                professor = Professor(name=name, department=department)
                db.add(professor)
                db.flush()  # flush so the professor gets an id we can use
                professors_by_name[name] = professor

            professor = professors_by_name[name]

            # 4. Run VADER sentiment analysis on the review text.
            score, label = analyze_sentiment(text)

            # 5. Save the scored review.
            review = Review(
                professor_id=professor.id,
                text=text,
                sentiment_score=score,
                sentiment_label=label,
            )
            db.add(review)

        db.commit()

        # Return how many reviews we stored (used by the /scrape response).
        return db.query(Review).count()
    finally:
        db.close()


# -----------------------------------------------------------------------------
# ROUTE: the homepage. Serves our single HTML page.
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# -----------------------------------------------------------------------------
# ROUTE: GET /professors
# Return every professor with their average sentiment score.
# -----------------------------------------------------------------------------
@app.route("/professors")
def get_professors():
    db = SessionLocal()
    try:
        professors = db.query(Professor).all()
        # Sort highest-rated first so the list reads nicely.
        data = sorted(
            [p.to_dict() for p in professors],
            key=lambda p: p["average_score"],
            reverse=True,
        )
        return jsonify(data)
    finally:
        db.close()


# -----------------------------------------------------------------------------
# ROUTE: GET /professors/<name>
# Return all individual reviews for one professor (used by the search bar).
# -----------------------------------------------------------------------------
@app.route("/professors/<name>")
def get_professor_reviews(name):
    db = SessionLocal()
    try:
        # Case-insensitive partial match so "turing" finds "Dr. Alan Turing".
        professor = (
            db.query(Professor)
            .filter(Professor.name.ilike(f"%{name}%"))
            .first()
        )
        if professor is None:
            abort(404, description=f"No professor found matching '{name}'.")

        return jsonify({
            "professor": professor.to_dict(),
            "reviews": [r.to_dict() for r in professor.reviews],
        })
    finally:
        db.close()


# -----------------------------------------------------------------------------
# ROUTE: GET /stats
# The big one — powers the dashboard charts.
# Returns: overall sentiment breakdown, top 5, bottom 5, department averages,
# and the full list of reviews for the table.
# -----------------------------------------------------------------------------
@app.route("/stats")
def get_stats():
    db = SessionLocal()
    try:
        professors = db.query(Professor).all()
        reviews = db.query(Review).all()

        # --- Overall sentiment distribution (for the donut chart) ----------
        distribution = {"Positive": 0, "Neutral": 0, "Negative": 0}
        for review in reviews:
            distribution[review.sentiment_label] += 1

        # --- Professors ranked by average score ----------------------------
        prof_dicts = [p.to_dict() for p in professors if p.reviews]
        ranked = sorted(prof_dicts, key=lambda p: p["average_score"], reverse=True)
        top_5 = ranked[:5]
        bottom_5 = ranked[-5:][::-1]  # lowest first

        # --- Department averages (for the horizontal bar chart) ------------
        dept_totals = {}   # department -> [sum_of_scores, count]
        for review in reviews:
            dept = review.professor.department
            if dept not in dept_totals:
                dept_totals[dept] = [0.0, 0]
            dept_totals[dept][0] += review.sentiment_score
            dept_totals[dept][1] += 1

        department_averages = [
            {"department": dept, "average_score": round(total / count, 3)}
            for dept, (total, count) in dept_totals.items()
        ]
        department_averages.sort(key=lambda d: d["average_score"], reverse=True)

        # --- Bundle everything up for the frontend -------------------------
        return jsonify({
            "total_reviews": len(reviews),
            "total_professors": len(professors),
            "distribution": distribution,
            "top_5": top_5,
            "bottom_5": bottom_5,
            "department_averages": department_averages,
            "reviews": [r.to_dict() for r in reviews],
        })
    finally:
        db.close()


# -----------------------------------------------------------------------------
# ROUTE: POST /scrape
# Re-run the scraper + analyzer and refresh the database.
# -----------------------------------------------------------------------------
@app.route("/scrape", methods=["POST"])
def scrape():
    count = populate_database()
    return jsonify({
        "status": "success",
        "message": f"Refreshed data. Analyzed {count} reviews.",
        "review_count": count,
    })


# -----------------------------------------------------------------------------
# ROUTE: GET /export
# Build a CSV file in memory and send it as a download.
# -----------------------------------------------------------------------------
@app.route("/export")
def export_csv():
    db = SessionLocal()
    try:
        reviews = db.query(Review).all()

        # Write CSV rows into an in-memory text buffer.
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["Professor", "Department", "Review", "Score", "Sentiment"])
        for r in reviews:
            writer.writerow([
                r.professor.name,
                r.professor.department,
                r.text,
                round(r.sentiment_score, 3),
                r.sentiment_label,
            ])

        # Send the buffer back as a downloadable file.
        return Response(
            buffer.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=reviews.csv"},
        )
    finally:
        db.close()


# -----------------------------------------------------------------------------
# Startup: make sure the database exists and has data the first time we run.
# This runs whether we start with Flask locally OR gunicorn in production.
# -----------------------------------------------------------------------------
def bootstrap():
    init_db()
    db = SessionLocal()
    try:
        has_data = db.query(Review).count() > 0
    finally:
        db.close()
    if not has_data:
        populate_database()


# Run the bootstrap as soon as the module is imported (gunicorn imports it).
bootstrap()


# -----------------------------------------------------------------------------
# Only used when running locally with `python app.py`.
# In production, gunicorn imports the `app` object directly and ignores this.
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
