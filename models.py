# =============================================================================
# models.py
# -----------------------------------------------------------------------------
# Here we define the "shape" of our database tables as Python classes.
# Each class = one table. Each attribute = one column.
# We have two tables:
#   1. Professor  -> one row per professor
#   2. Review     -> one row per review (each review belongs to a professor)
# =============================================================================

from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


# -----------------------------------------------------------------------------
# Professor table
# -----------------------------------------------------------------------------
class Professor(Base):
    __tablename__ = "professors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    department = Column(String, nullable=False, index=True)

    # A professor has many reviews. This "relationship" lets us write
    # professor.reviews to get a list of all their Review objects.
    # cascade="all, delete-orphan" means deleting a professor also deletes
    # their reviews (handy when we refresh the data).
    reviews = relationship(
        "Review",
        back_populates="professor",
        cascade="all, delete-orphan",
    )

    def average_score(self):
        """Return the average sentiment score across all this prof's reviews."""
        if not self.reviews:
            return 0.0
        total = sum(review.sentiment_score for review in self.reviews)
        return round(total / len(self.reviews), 3)

    def to_dict(self):
        """Convert this professor into a plain dictionary so Flask can send
        it back to the frontend as JSON."""
        return {
            "id": self.id,
            "name": self.name,
            "department": self.department,
            "review_count": len(self.reviews),
            "average_score": self.average_score(),
        }


# -----------------------------------------------------------------------------
# Review table
# -----------------------------------------------------------------------------
class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)

    # Link back to the professor this review belongs to.
    professor_id = Column(Integer, ForeignKey("professors.id"), nullable=False)

    text = Column(Text, nullable=False)              # the review comment
    sentiment_score = Column(Float, nullable=False)  # VADER compound score (-1..1)
    sentiment_label = Column(String, nullable=False) # "Positive"/"Neutral"/"Negative"

    # The other side of the relationship defined on Professor above.
    professor = relationship("Professor", back_populates="reviews")

    def to_dict(self):
        """Convert this review into a dictionary for JSON responses."""
        return {
            "id": self.id,
            "professor": self.professor.name if self.professor else "Unknown",
            "department": self.professor.department if self.professor else "Unknown",
            "text": self.text,
            "sentiment_score": round(self.sentiment_score, 3),
            "sentiment_label": self.sentiment_label,
        }
