# domain/services.py
from typing import List, Optional
from .models import BookDomain, ReviewDomain
from .repositories import BookRepositoryProtocol, ReviewRepositoryProtocol, LlmRepositoryProtocol

class BookService:
    """Service for handling book-related business logic."""
    
    def __init__(self, book_repository: BookRepositoryProtocol):
        self.book_repository = book_repository
    
    async def get_book(self, book_id: int) -> Optional[BookDomain]:
        """Get a book by its ID."""
        return await self.book_repository.get_by_id(book_id)
    
    async def get_books(self, skip: int = 0, limit: int = 100) -> List[BookDomain]:
        """Get all books with pagination."""
        return await self.book_repository.get_all(skip, limit)
    
    async def create_book(self, book: BookDomain) -> BookDomain:
        """Create a new book."""
        return await self.book_repository.create(book)
    
    async def update_book(self, book: BookDomain) -> BookDomain:
        """Update an existing book."""
        return await self.book_repository.update(book)
    
    async def delete_book(self, book_id: int) -> bool:
        """Delete a book by its ID."""
        return await self.book_repository.delete(book_id)
    
    async def get_books_by_genre(self, genre: str) -> List[BookDomain]:
        """Get all books of a specific genre."""
        return await self.book_repository.get_by_genre(genre)
    
    async def get_book_by_title_and_author(self, title: str, author: str) -> Optional[BookDomain]:
        """Get a book by its title and author."""
        return await self.book_repository.get_by_title_and_author(title, author)


class ReviewService:
    """Service for handling review-related business logic."""
    
    def __init__(self, review_repository: ReviewRepositoryProtocol):
        self.review_repository = review_repository
    
    async def get_review(self, review_id: int) -> Optional[ReviewDomain]:
        """Get a review by its ID."""
        return await self.review_repository.get_by_id(review_id)
    
    async def create_review(self, review: ReviewDomain) -> ReviewDomain:
        """Create a new review."""
        return await self.review_repository.create(review)
    
    async def get_book_reviews(self, book_id: int, skip: int = 0, limit: int = 100) -> List[ReviewDomain]:
        """Get all reviews for a specific book with pagination."""
        reviews = await self.review_repository.get_by_book_id(book_id)
        # Apply pagination manually if the repository doesn't support it
        return reviews[skip:skip+limit]
    
    async def get_user_reviews(self, user_id: int) -> List[ReviewDomain]:
        """Get all reviews by a specific user."""
        return await self.review_repository.get_by_user_id(user_id)
    
    async def get_average_rating(self, book_id: int) -> float:
        """Get the average rating for a book."""
        return await self.review_repository.get_average_rating_for_book(book_id)


class LlmService:
    """Service for handling LLM-related operations."""
    
    def __init__(self, llm_repository: LlmRepositoryProtocol):
        self.llm_repository = llm_repository
    
    async def generate_book_summary(self, book_title: str, book_content: str) -> str:
        """Generate a summary for a book."""
        return await self.llm_repository.generate_book_summary(book_title, book_content)
    
    async def generate_text_summary(self, text: str) -> str:
        """Generate a summary for any text."""
        return await self.llm_repository.generate_summary(text)
    
    async def summarize_reviews(self, reviews: List[str]) -> str:
        """Generate a summary of multiple reviews."""
        return await self.llm_repository.generate_review_summary(reviews)