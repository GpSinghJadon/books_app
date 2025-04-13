# infrastructure/postgres/models.py
from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, Float,
    UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from database import Base  # Import the Base declarative base from database.py

class Book(Base):
    """
    SQLAlchemy ORM model for the 'books' table.
    """
    __tablename__ = "books"

    # --- Columns ---
    id = Column(Integer, primary_key=True, index=True, comment="Unique identifier for the book")
    title = Column(String(255), index=True, nullable=False, comment="Title of the book")
    author = Column(String(255), index=True, nullable=False, comment="Author(s) of the book")
    genre = Column(String(100), index=True, comment="Genre of the book")
    year_published = Column(Integer, comment="Year the book was published")
    summary = Column(Text, nullable=True, comment="Synopsis or summary of the book (can be AI-generated)")

    # --- Relationships ---
    reviews = relationship(
        "Review",
        back_populates="book",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin"
    )

    # --- Constraints and Indexes ---
    __table_args__ = (
        UniqueConstraint('title', 'author', name='uq_book_title_author'),
        Index('ix_book_genre_year', 'genre', 'year_published'),
        {'comment': 'Stores information about books in the library'}
    )

    def __repr__(self):
        """String representation for debugging."""
        return f"<Book(id={self.id}, title='{self.title}', author='{self.author}')>"


class Review(Base):
    """
    SQLAlchemy ORM model for the 'reviews' table.
    """
    __tablename__ = "reviews"

    # --- Columns ---
    id = Column(Integer, primary_key=True, index=True, comment="Unique identifier for the review")
    book_id = Column(Integer, ForeignKey("books.id", ondelete="CASCADE"), nullable=False, index=True, comment="Foreign key referencing the reviewed book")
    user_id = Column(Integer, index=True, nullable=False, comment="Identifier for the user who wrote the review (assuming external user system)")
    review_text = Column(Text, nullable=True, comment="The text content of the review")
    rating = Column(Float, nullable=False, comment="User's rating for the book (e.g., 0.0 to 5.0)")

    # --- Relationships ---
    book = relationship(
        "Book",
        back_populates="reviews",
        lazy="joined"
    )

    # --- Constraints and Indexes ---
    __table_args__ = (
        CheckConstraint('rating >= 0 AND rating <= 5', name='chk_review_rating_range'),
        Index('ix_review_user_id', 'user_id'),
        {'comment': 'Stores user reviews and ratings for books'}
    )

    def __repr__(self):
        """String representation for debugging."""
        return f"<Review(id={self.id}, book_id={self.book_id}, user_id={self.user_id}, rating={self.rating})>"
