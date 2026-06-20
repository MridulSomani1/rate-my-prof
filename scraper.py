# =============================================================================
# scraper.py
# -----------------------------------------------------------------------------
# This file is responsible for COLLECTING the raw review data.
#
# Rate My Professors loads its reviews with JavaScript and actively blocks
# automated scraping (it returns 403 errors / empty pages to bots). Because of
# that, by default we use a built-in MOCK dataset of 50 realistic-looking fake
# reviews spread across 10 professors and 4 departments. This keeps the whole
# app working and looking real without depending on a site that blocks us.
#
# Each review is a simple dictionary:
#   {"professor": "...", "department": "...", "text": "..."}
#
# -----------------------------------------------------------------------------
# HOW TO SWAP IN REAL SCRAPING LATER
# -----------------------------------------------------------------------------
# 1. Find a professor page on https://www.ratemyprofessors.com/
# 2. Use the scrape_real_reviews() function below as a starting template.
#    It already imports requests + BeautifulSoup and sends a browser-like
#    User-Agent header (RMP blocks the default Python user agent).
# 3. RMP's reviews are rendered from a JSON "props" blob and/or a GraphQL API.
#    You will likely need to:
#       - inspect the page in your browser's DevTools (Network tab)
#       - find the request that returns the review JSON
#       - parse that JSON instead of HTML, OR parse the embedded
#         <script id="__NEXT_DATA__"> tag with BeautifulSoup + json.loads
# 4. Once scrape_real_reviews() returns a non-empty list of the same dict
#    shape, change get_reviews() to call it and fall back to the mock data
#    only when it returns nothing.
# =============================================================================

import requests
from bs4 import BeautifulSoup


# -----------------------------------------------------------------------------
# The mock dataset: 50 reviews, 10 professors, 4 departments.
# Sentiment is intentionally mixed so the charts look interesting.
# -----------------------------------------------------------------------------
MOCK_REVIEWS = [
    # ---- Computer Science --------------------------------------------------
    {"professor": "Dr. Alan Turing", "department": "Computer Science",
     "text": "Absolutely brilliant lecturer. His explanations of algorithms made everything click. Best professor I've ever had!"},
    {"professor": "Dr. Alan Turing", "department": "Computer Science",
     "text": "Tough course but incredibly rewarding. He genuinely cares about students learning."},
    {"professor": "Dr. Alan Turing", "department": "Computer Science",
     "text": "Exams were fair and the lectures were engaging. Highly recommend taking his class."},
    {"professor": "Dr. Alan Turing", "department": "Computer Science",
     "text": "A bit fast-paced at times, but office hours were super helpful and he's very approachable."},
    {"professor": "Dr. Alan Turing", "department": "Computer Science",
     "text": "Loved every minute. Inspiring, clear, and passionate about the subject."},

    {"professor": "Dr. Grace Hopper", "department": "Computer Science",
     "text": "Fantastic teacher who makes complex topics simple. Always encouraging and positive."},
    {"professor": "Dr. Grace Hopper", "department": "Computer Science",
     "text": "Great real-world examples. I actually looked forward to coming to class."},
    {"professor": "Dr. Grace Hopper", "department": "Computer Science",
     "text": "The labs were okay. Nothing special but not bad either."},
    {"professor": "Dr. Grace Hopper", "department": "Computer Science",
     "text": "Helpful and organized. Grading was a little strict but fair overall."},
    {"professor": "Dr. Grace Hopper", "department": "Computer Science",
     "text": "One of the most supportive professors in the department. Truly cares."},

    {"professor": "Dr. Edsger Dijkstra", "department": "Computer Science",
     "text": "Lectures were dry and hard to follow. I struggled the entire semester."},
    {"professor": "Dr. Edsger Dijkstra", "department": "Computer Science",
     "text": "Way too much homework and very little explanation. Disappointing experience."},
    {"professor": "Dr. Edsger Dijkstra", "department": "Computer Science",
     "text": "He knows his stuff but is not great at teaching beginners. Confusing at times."},
    {"professor": "Dr. Edsger Dijkstra", "department": "Computer Science",
     "text": "Some lectures were fine, others were a mess. Inconsistent overall."},
    {"professor": "Dr. Edsger Dijkstra", "department": "Computer Science",
     "text": "Brutal exams and unclear expectations. Would not recommend."},

    # ---- Mathematics -------------------------------------------------------
    {"professor": "Dr. Katherine Johnson", "department": "Mathematics",
     "text": "Incredible professor! Patient, kind, and explains calculus beautifully."},
    {"professor": "Dr. Katherine Johnson", "department": "Mathematics",
     "text": "Made me actually enjoy math for the first time. Wonderful teacher."},
    {"professor": "Dr. Katherine Johnson", "department": "Mathematics",
     "text": "Very clear and well organized lectures. Always willing to help."},
    {"professor": "Dr. Katherine Johnson", "department": "Mathematics",
     "text": "Decent class. The pace was fine and the material was manageable."},
    {"professor": "Dr. Katherine Johnson", "department": "Mathematics",
     "text": "Truly one of the greats. Inspiring and supportive throughout the term."},

    {"professor": "Dr. Carl Gauss", "department": "Mathematics",
     "text": "Smart but arrogant. Made students feel dumb for asking questions."},
    {"professor": "Dr. Carl Gauss", "department": "Mathematics",
     "text": "The tests were unfairly hard and he rarely explained his reasoning."},
    {"professor": "Dr. Carl Gauss", "department": "Mathematics",
     "text": "Lectures were average. Not terrible, not amazing."},
    {"professor": "Dr. Carl Gauss", "department": "Mathematics",
     "text": "I found the proofs interesting but the grading was harsh and discouraging."},
    {"professor": "Dr. Carl Gauss", "department": "Mathematics",
     "text": "Brilliant mathematician but a frustrating teacher to learn from."},

    # ---- Physics -----------------------------------------------------------
    {"professor": "Dr. Marie Curie", "department": "Physics",
     "text": "Phenomenal! Her passion for physics is contagious and her labs are amazing."},
    {"professor": "Dr. Marie Curie", "department": "Physics",
     "text": "Best science professor on campus. Clear, caring, and brilliant."},
    {"professor": "Dr. Marie Curie", "department": "Physics",
     "text": "Challenging material but she breaks it down so well. Loved this class."},
    {"professor": "Dr. Marie Curie", "department": "Physics",
     "text": "Great lectures, fair exams, and genuinely enthusiastic about teaching."},
    {"professor": "Dr. Marie Curie", "department": "Physics",
     "text": "Solid course. Nothing to complain about, learned a lot."},

    {"professor": "Dr. Richard Feynman", "department": "Physics",
     "text": "Hilarious and engaging! He turns hard concepts into fun stories."},
    {"professor": "Dr. Richard Feynman", "department": "Physics",
     "text": "The most entertaining lecturer I've had. You'll never be bored."},
    {"professor": "Dr. Richard Feynman", "department": "Physics",
     "text": "Great energy, though sometimes he goes off on tangents."},
    {"professor": "Dr. Richard Feynman", "department": "Physics",
     "text": "Loved his teaching style. Made quantum mechanics approachable."},
    {"professor": "Dr. Richard Feynman", "department": "Physics",
     "text": "Fun classes but the exams were harder than expected."},

    # ---- Biology -----------------------------------------------------------
    {"professor": "Dr. Charles Darwin", "department": "Biology",
     "text": "Fascinating lectures full of great examples. Really knows his field."},
    {"professor": "Dr. Charles Darwin", "department": "Biology",
     "text": "Interesting course but a lot of memorization. Mixed feelings."},
    {"professor": "Dr. Charles Darwin", "department": "Biology",
     "text": "Pretty average class. The slides were fine and exams were okay."},
    {"professor": "Dr. Charles Darwin", "department": "Biology",
     "text": "Enjoyed the evolution unit but the lab reports were tedious."},
    {"professor": "Dr. Charles Darwin", "department": "Biology",
     "text": "Knowledgeable professor, decent lectures, reasonable workload."},

    {"professor": "Dr. Rosalind Franklin", "department": "Biology",
     "text": "Outstanding! Her genetics lectures were crystal clear and inspiring."},
    {"professor": "Dr. Rosalind Franklin", "department": "Biology",
     "text": "Extremely knowledgeable and always prepared. A fantastic mentor."},
    {"professor": "Dr. Rosalind Franklin", "department": "Biology",
     "text": "Great professor who pushes you to do your best work."},
    {"professor": "Dr. Rosalind Franklin", "department": "Biology",
     "text": "The content was dense but she made it understandable. Recommend."},
    {"professor": "Dr. Rosalind Franklin", "department": "Biology",
     "text": "Helpful, fair, and clearly an expert. Learned so much."},

    {"professor": "Dr. Barbara McClintock", "department": "Biology",
     "text": "Disorganized lectures and confusing assignments. Frustrating semester."},
    {"professor": "Dr. Barbara McClintock", "department": "Biology",
     "text": "The material was interesting but the class felt chaotic and rushed."},
    {"professor": "Dr. Barbara McClintock", "department": "Biology",
     "text": "Okay professor. Some good days, some bad days."},
    {"professor": "Dr. Barbara McClintock", "department": "Biology",
     "text": "Hard to follow and slow to respond to emails. Could be better."},
    {"professor": "Dr. Barbara McClintock", "department": "Biology",
     "text": "Not the worst, but the grading felt random and unclear."},
]


def scrape_real_reviews(professor_url):
    """
    TEMPLATE for real scraping (not used by default — see the big comment at
    the top of this file). Returns a list of review dicts, or [] on failure.

    Fill in the parsing logic for the page you want to scrape, then have
    get_reviews() call this function.
    """
    # A browser-like header. RMP blocks the default "python-requests" agent.
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(professor_url, headers=headers, timeout=10)
        response.raise_for_status()  # raise an error for 4xx/5xx responses
    except requests.RequestException:
        # If the site blocks us or the network fails, return nothing so the
        # caller can fall back to the mock data.
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    # ---------------------------------------------------------------------
    # TODO (real scraping): RMP renders reviews from JSON, not plain HTML.
    # Replace the line below with logic that extracts each review's text,
    # professor name, and department, and appends a dict to `reviews`.
    # Example skeleton:
    #
    #   reviews = []
    #   for card in soup.select("div.Rating__StyledRating"):
    #       comment = card.select_one("div.Comments__StyledComments")
    #       if comment:
    #           reviews.append({
    #               "professor": "...",     # pull from the page
    #               "department": "...",    # pull from the page
    #               "text": comment.get_text(strip=True),
    #           })
    #   return reviews
    # ---------------------------------------------------------------------
    reviews = []
    return reviews


def get_reviews():
    """
    Return the list of review dictionaries the rest of the app uses.

    By default this returns the mock dataset. To use real scraping, scrape
    your target pages with scrape_real_reviews() and return those results
    when they are non-empty, e.g.:

        real = scrape_real_reviews("https://www.ratemyprofessors.com/professor/12345")
        if real:
            return real
        return MOCK_REVIEWS
    """
    return MOCK_REVIEWS
