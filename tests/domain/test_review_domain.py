import pytest
from datetime import datetime
from domain.models.review import ReviewDomain

class TestReviewDomain:
    def test_review_creation(self):
        """Test that a review can be created with valid attributes."""
        review = ReviewDomain(
            book_id=1,
            user_id=2,
            rating=4,
            text="This is a test review.",
            created_at=datetime(2023, 1, 1, 12, 0, 0)
        )
        
        assert review.book_id == 1
        assert review.user_id == 2
        assert review.rating == 4
        assert review.text == "This is a test review."
        assert review.created_at == datetime(2023, 1, 1, 12, 0, 0)
        assert review.id is None  # ID should be None until persisted
    
    def test_review_creation_with_id(self):
        """Test that a review can be created with an ID (e.g., when loaded from DB)."""
        review = ReviewDomain(
            id=1,
            book_id=1,
            user_id=2,
            rating=4,
            text="This is a test review."
        )
        
        assert review.id == 1
    
    def test_review_creation_with_minimal_attributes(self):
        """Test that a review can be created with only required attributes."""
        review = ReviewDomain(
            book_id=1,
            user_id=2,
            rating=4
        )
        
        assert review.book_id == 1
        assert review.user_id == 2
        assert review.rating == 4
        assert review.text is None
        # created_at might be auto-generated with current time
    
    def test_review_rating_validation(self):
        """Test that review rating is validated to be between 1 and 5."""
        # Test valid ratings
        for rating in range(1, 6):
            review = ReviewDomain(book_id=1, user_id=1, rating=rating)
            assert review.rating == rating
        
        # Test invalid ratings
        with pytest.raises(ValueError):
            ReviewDomain(book_id=1, user_id=1, rating=0)
        
        with pytest.raises(ValueError):
            ReviewDomain(book_id=1, user_id=1, rating=6)
    
    def test_review_equality(self):
        """Test that two reviews with the same ID are considered equal."""
        review1 = ReviewDomain(id=1, book_id=1, user_id=1, rating=4)
        review2 = ReviewDomain(id=1, book_id=2, user_id=2, rating=5)
        review3 = ReviewDomain(id=2, book_id=1, user_id=1, rating=4)
        
        assert review1 == review2  # Same ID should make them equal
        assert review1 != review3  # Different ID should make them not equal
    
    def test_review_string_representation(self):
        """Test the string representation of a review."""
        review = ReviewDomain(
            id=1,
            book_id=1,
            user_id=2,
            rating=4,
            text="Good book"
        )
        
        # Assuming __str__ or __repr__ is implemented
        assert str(review) == "ReviewDomain(id=1, book_id=1, user_id=2, rating=4)" or \
               repr(review) == "ReviewDomain(id=1, book_id=1, user_id=2, rating=4)"
