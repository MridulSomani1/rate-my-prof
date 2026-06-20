# =============================================================================
# analyzer.py
# -----------------------------------------------------------------------------
# This file runs the actual sentiment analysis using VADER.
# VADER (Valence Aware Dictionary and sEntiment Reasoner) is a tool that is
# great at scoring short pieces of text like reviews, tweets, and comments.
#
# For each review it gives us a "compound" score between -1 and +1:
#   -1.0  = extremely negative
#    0.0  = neutral
#   +1.0  = extremely positive
# =============================================================================

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Create ONE analyzer object and reuse it (it's a little expensive to build,
# so we don't want to recreate it for every single review).
_analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(text):
    """
    Take a piece of review text and return a tuple of (score, label).

    score  -> the VADER compound score (a float from -1 to 1)
    label  -> a human-friendly category: "Positive", "Neutral", or "Negative"
    """
    # polarity_scores returns a dictionary like:
    # {'neg': 0.0, 'neu': 0.5, 'pos': 0.5, 'compound': 0.6}
    scores = _analyzer.polarity_scores(text)
    compound = scores["compound"]

    # These thresholds are the standard VADER recommendation.
    if compound >= 0.05:
        label = "Positive"
    elif compound <= -0.05:
        label = "Negative"
    else:
        label = "Neutral"

    return compound, label
