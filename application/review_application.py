# application/review_application.py
from typing import List, Optional, Dict, Any
from domain.models import ReviewDomain
from domain.services import ReviewService, BookService, LlmService

class ReviewApplication:
    """
    Application service that coordinates domain services for review-related operations.
    """
    
    def __init__(self, review_service: ReviewService, book_service: BookService, llm_service: LlmService):
        self.review_service = review_service
        self.book_service = book_service
        self.llm_service = llm_service
    
    async def create_review(self, review: ReviewDomain) -> Optional[ReviewDomain]:
        """
        Create a new review.
        
        Args:
            review: The review domain model to create
            
        Returns:
            The created review domain model if the book exists, None otherwise
        """
        # Verify the book exists
        book = await self.book_service.get_book(review.book_id)
        if not book:
            return None
        
        # Create the review
        created_review = await self.review_service.create_review(review)
        return created_review
    
    async def get_review(self, review_id: int) -> Optional[ReviewDomain]:
        """
        Get a review by its ID.
        
        Args:
            review_id: The ID of the review to retrieve
            
        Returns:
            The review domain model if found, None otherwise
        """
        return await self.review_service.get_review(review_id)
    
    async def get_book_reviews(self, book_id: int, skip: int = 0, limit: int = 100) -> List[ReviewDomain]:
        """
        Get all reviews for a book with pagination.
        
        Args:
            book_id: The ID of the book whose reviews to retrieve
            skip: Number of reviews to skip
            limit: Maximum number of reviews to return
            
        Returns:
            List of review domain models
        """
        # Verify the book exists
        book = await self.book_service.get_book(book_id)
        if not book:
            return []
        
        # Get the reviews
        return await self.review_service.get_book_reviews(book_id, skip, limit)
    
    async def get_user_reviews(self, user_id: int, skip: int = 0, limit: int = 100) -> List[ReviewDomain]:
        """
        Get all reviews by a user with pagination.
        
        Args:
            user_id: The ID of the user whose reviews to retrieve
            skip: Number of reviews to skip
            limit: Maximum number of reviews to return
            
        Returns:
            List of review domain models
        """
        reviews = await self.review_service.get_user_reviews(user_id)
        # Apply pagination manually
        return reviews[skip:skip+limit]
    
    async def get_average_rating(self, book_id: int) -> float:
        """
        Get the average rating for a book.
        
        Args:
            book_id: The ID of the book
            
        Returns:
            The average rating as a float (0.0 if no ratings)
        """
        # Verify the book exists
        book = await self.book_service.get_book(book_id)
        if not book:
            return 0.0
        
        return await self.review_service.get_average_rating(book_id)
    
    async def summarize_book_reviews(self, book_id: int) -> Optional[str]:
        """
        Generate a summary of all reviews for a book.
        
        Args:
            book_id: The ID of the book
            
        Returns:
            A summary of the reviews if the book exists and has reviews, None otherwise
        """
        # Verify the book exists
        book = await self.book_service.get_book(book_id)
        if not book:
            return None
        
        # Get all reviews for the book
        reviews = await self.review_service.get_book_reviews(book_id)
        if not reviews:
            return "No reviews available for this book."
        
        # Extract the review texts
        review_texts = [review.review_text for review in reviews if review.review_text]
        if not review_texts:
            return "No text content available in the reviews for this book."
        
        # Generate a summary of the reviews
        return await self.llm_service.summarize_reviews(review_texts)
    
    async def get_book_review_statistics(self, book_id: int) -> Optional[Dict[str, Any]]:
        """
        Get statistics about a book's reviews.
        
        Args:
            book_id: The ID of the book
            
        Returns:
            A dictionary with review statistics if the book exists, None otherwise
        """
        # Verify the book exists
        book = await self.book_service.get_book(book_id)
        if not book:
            return None
        
        # Get all reviews for the book
        reviews = await self.review_service.get_book_reviews(book_id)
        
        # Calculate statistics
        total_reviews = len(reviews)
        if total_reviews == 0:
            return {
                "total_reviews": 0,
                "average_rating": 0.0,
                "rating_distribution": {
                    "1": 0, "2": 0, "3": 0, "4": 0, "5": 0
                }
            }
        
        # Calculate average rating
        average_rating = sum(review.rating for review in reviews) / total_reviews
        
        # Calculate rating distribution
        rating_distribution = {
            "1": 0, "2": 0, "3": 0, "4": 0, "5": 0
        }
        
        for review in reviews:
            # Round to nearest integer for distribution
            rounded_rating = round(review.rating)
            # Ensure it's within our 1-5 range
            rounded_rating = max(1, min(5, rounded_rating))
            rating_distribution[str(rounded_rating)] += 1
        
        return {
            "total_reviews": total_reviews,
            "average_rating": round(average_rating, 2),
            "rating_distribution": rating_distribution
        }
