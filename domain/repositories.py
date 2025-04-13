# domain/repositories.py
from typing import Protocol, List, Optional, TypeVar, Generic
from .models import BookDomain, ReviewDomain

T = TypeVar('T')

# Update the RepositoryProtocol in domain/repositories.py

class RepositoryProtocol(Protocol, Generic[T]):
    """Base repository protocol that defines common operations."""
    
    async def get_by_id(self, id: int) -> Optional[T]:
        """Retrieve an entity by its ID."""
        ...
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Retrieve all entities with pagination."""
        ...
    
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        ...
    
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        ...
    
    async def delete(self, id: int) -> bool:
        """Delete an entity by its ID."""
        ...



class BookRepositoryProtocol(RepositoryProtocol[BookDomain]):
    """Protocol for Book repository operations."""
    
    async def get_by_title_and_author(self, title: str, author: str) -> Optional[BookDomain]:
        """Get a book by its title and author."""
        ...
    
    async def get_by_genre(self, genre: str) -> List[BookDomain]:
        """Get all books of a specific genre."""
        ...
    
    async def get_by_year(self, year: int) -> List[BookDomain]:
        """Get all books published in a specific year."""
        ...


class ReviewRepositoryProtocol(RepositoryProtocol[ReviewDomain]):
    """Protocol for Review repository operations."""
    
    async def get_by_book_id(self, book_id: int) -> List[ReviewDomain]:
        """Get all reviews for a specific book."""
        ...
    
    async def get_by_user_id(self, user_id: int) -> List[ReviewDomain]:
        """Get all reviews by a specific user."""
        ...
    
    async def get_average_rating_for_book(self, book_id: int) -> float:
        """Get the average rating for a specific book."""
        ...
class LlmRepositoryProtocol(Protocol):
    """Protocol for LLM-based operations."""
    
    async def generate_summary(self, text: str) -> str:
        """Generate a summary for the given text."""
        ...
    
    async def generate_book_summary(self, book_title: str, book_content: str) -> str:
        """Generate a summary specifically for a book."""
        ...
    
    async def generate_review_summary(self, reviews: List[str]) -> str:
        """Generate a summary of multiple reviews."""
        ...