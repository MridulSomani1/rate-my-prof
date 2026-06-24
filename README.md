---
title: Rate My Professor
emoji: 📉
colorFrom: purple
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# 🎓 Rate My Professor, Sentiment Analyzer

A full-stack web app that collects professor reviews, scores each one with
**VADER sentiment analysis**, and shows the results on an interactive dashboard
with charts, search, sorting, CSV export, and dark mode.

Built with **Python + Flask + SQLAlchemy + SQLite** on the backend and
**vanilla HTML/CSS/JS + Chart.js** on the frontend. No React, no Bootstrap, no
jQuery.

---

## ✨ Features

- Scrapes reviews (uses a built-in **mock dataset of 50 reviews / 10 professors
  / 4 departments** by default, see `scraper.py` to swap in real scraping)
- Runs VADER sentiment analysis on every review → Positive / Neutral / Negative
- Dashboard with 4 charts: Top 5, Bottom 5, sentiment donut, department averages
- Search any professor and see their full review breakdown
- Sortable reviews table (click the **Score** column header)
- Export all reviews to CSV
- Dark mode toggle (saved in your browser via `localStorage`)
- Manual refresh button that re-runs the scraper and redraws every chart

---

## 📁 Project structure

```
.
├── app.py            # Flask server + all API routes
├── models.py         # Database tables (Professor, Review)
├── database.py       # SQLite + SQLAlchemy setup
├── scraper.py        # Mock data + real-scraping template
├── analyzer.py       # VADER sentiment scoring
├── requirements.txt  # Python dependencies
├── render.yaml       # Render.com deployment config
├── .gitignore
├── static/
│   ├── style.css
│   └── script.js
└── templates/
    └── index.html
```

---

## 🔌 API routes

| Method | Route                 | What it does                                   |
|--------|-----------------------|------------------------------------------------|
| GET    | `/professors`         | All professors with average sentiment score    |
| GET    | `/professors/<name>`  | All reviews for one professor (partial match)   |
| GET    | `/stats`              | Distribution, top/bottom 5, dept averages, rows |
| POST   | `/scrape`             | Re-run the scraper and refresh the database     |
| GET    | `/export`             | Download all reviews as a CSV file              |

---

## 💻 Run it locally

You need **Python 3.10+** installed.

```bash
# 1. (Optional but recommended) create a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the app
python app.py
```

Then open **http://localhost:5000** in your browser.

The first run automatically creates `reviews.db`, scores the mock reviews, and
fills the dashboard.

---

## 🚀 Deploy live to the internet (Render.com, free)

Follow these steps in order. This gets you a public URL anyone can visit.

### Step 1 Put the code on GitHub

1. Create a free account at **https://github.com** if you don't have one.
2. Click the **+** in the top-right → **New repository**.
3. Name it `rate-my-professor-sentiment`, keep it **Public**, and click
   **Create repository**. (Don't add a README, you already have one.)
4. Open a terminal **inside this project folder** and run:

   ```bash
   git init
   git add .
   git commit -m "Initial commit - Rate My Professor sentiment analyzer"
   git branch -M main
   # Replace YOUR-USERNAME with your GitHub username:
   git remote add origin https://github.com/YOUR-USERNAME/rate-my-professor-sentiment.git
   git push -u origin main
   ```

   Refresh your GitHub page, all your files should now be there.

### Step 2 Connect the repo to Render

1. Create a free account at **https://render.com** (sign up with GitHub, it's
   easiest).
2. On the dashboard click **New +** → **Web Service**.
3. Choose **Build and deploy from a Git repository** → **Next**.
4. Find and **Connect** your `rate-my-professor-sentiment` repo. (You may need
   to click "Configure account" to give Render access to it.)

### Step 3 Configure the service

Render reads `render.yaml` automatically, so most fields fill in for you. Confirm:

- **Runtime:** Python 3
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `gunicorn app:app`
- **Instance Type:** **Free**

Then click **Create Web Service**.

### Step 4 Get your live link

1. Render now installs everything and starts the app. Watch the **Logs** tab,
   wait until you see something like `Booting worker` and the status turns
   **Live** (the first build takes a few minutes).
2. Your public URL appears at the top of the page, e.g.:

   ```
   https://rate-my-professor-sentiment.onrender.com
   ```

3. Open it, your dashboard is now live on the internet! 🎉

> **Note on the free tier:** Render free services "sleep" after ~15 minutes of
> no traffic. The next visit takes ~30–60 seconds to wake up. That's normal.
>
> Also, the SQLite database lives on the server's temporary disk, so it resets
> when the app restarts, but because the data is seeded automatically on
> startup, the dashboard always repopulates itself. Nothing breaks.

### Updating later

Any time you change the code, just push to GitHub and Render redeploys
automatically:

```bash
git add .
git commit -m "Describe your change"
git push
```

---

## 🔄 Swapping mock data for real scraping

Open `scraper.py` and read the big comment block at the top, it explains
exactly how to point `scrape_real_reviews()` at real Rate My Professors pages
and have `get_reviews()` use them, falling back to mock data if the site blocks
the request.
