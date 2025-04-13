# application/book_application.py
from typing import List, Optional, Tuple
from domain.models import BookDomain, ReviewDomain, BookWithReviews
from domain.services import BookService, ReviewService, LlmService

class BookApplication:
    """
    Application service that coordinates domain services for book-related operations.
    This class provides methods that correspond to the endpoints in main.py.
    """
    
    def __init__(self, book_service: BookService, review_service: ReviewService, llm_service: LlmService):
        self.book_service = book_service
        self.review_service = review_service
        self.llm_service = llm_service
    
    # === Book Operations ===
    
    async def create_book(self, book: BookDomain, generate_summary: bool = False) -> BookDomain:
        """
        Create a new book, optionally generating a summary.
        
        Args:
            book: The book domain model to create
            generate_summary: Whether to generate a summary using the LLM
            
        Returns:
            The created book domain model
        """
        # Check if book with same title and author already exists
        existing_book = await self.book_service.get_book_by_title_and_author(book.title, book.author)
        if existing_book:
            raise ValueError("Book with this title and author already exists")
        
        # Create the book first
        created_book = await self.book_service.create_book(book)
        
        # Generate summary if requested and not provided
        if generate_summary and not created_book.summary:
            try:
                # In a real scenario, you might have more book content
                book_context = f"Generate a brief summary for a book titled '{created_book.title}' by {created_book.author}. Genre: {created_book.genre or 'Unknown'}."
                summary = await self.llm_service.generate_text_summary(book_context)
                
                # Update the book with the generated summary
                created_book.summary = summary
                created_book = await self.book_service.update_book(created_book)
            except Exception as e:
                # Log the error but don't fail the book creation
                print(f"Error generating summary for '{created_book.title}': {e}")
                # You could store an error message or leave summary empty
        
        return created_book
    
    async def get_books(self, skip: int = 0, limit: int = 100) -> List[BookDomain]:
        """
        Get a list of books with pagination.
        
        Args:
            skip: Number of books to skip
            limit: Maximum number of books to return
            
        Returns:
            List of book domain models
        """
        return await self.book_service.get_books(skip, limit)
    
    async def get_book(self, book_id: int) -> Optional[BookDomain]:
        """
        Get a book by its ID.
        
        Args:
            book_id: The ID of the book to retrieve
            
        Returns:
            The book domain model if found, None otherwise
        """
        return await self.book_service.get_book(book_id)
    
    async def update_book(self, book_id: int, book_update: BookDomain) -> Optional[BookDomain]:
        """
        Update a book's information.
        
        Args:
            book_id: The ID of the book to update
            book_update: The book domain model with updated fields
            
        Returns:
            The updated book domain model if found, None otherwise
        """
        # Get the existing book
        existing_book = await self.book_service.get_book(book_id)
        if not existing_book:
            return None
        
        # Check for title/author conflicts if those fields are being updated
        if book_update.title and book_update.author:
            conflict_check = await self.book_service.get_book_by_title_and_author(
                book_update.title, book_update.author
            )
            if conflict_check and conflict_check.id != book_id:
                raise ValueError("Another book with this title and author already exists")
        
        # Update the existing book with the new values
        for field, value in book_update.dict(exclude_unset=True).items():
            if value is not None:  # Only update non-None values
                setattr(existing_book, field, value)
        
        # Save the updated book
        updated_book = await self.book_service.update_book(existing_book)
        return updated_book
    
    async def delete_book(self, book_id: int) -> Optional[BookDomain]:
        """
        Delete a book by its ID.
        
        Args:
            book_id: The ID of the book to delete
            
        Returns:
            The deleted book domain model if found, None otherwise
        """
        # Get the book first to return its data after deletion
        book = await self.book_service.get_book(book_id)
        if not book:
            return None
        
        # Delete the book
        success = await self.book_service.delete_book(book_id)
        if success:
            return book
        return None
    
    # === Review Operations ===
    
    async def create_review(self, book_id: int, review: ReviewDomain) -> Optional[ReviewDomain]:
        """
        Create a new review for a book.
        
        Args:
            book_id: The ID of the book being reviewed
            review: The review domain model to create
            
        Returns:
            The created review domain model if the book exists, None otherwise
        """
        # Verify the book exists
        book = await self.book_service.get_book(book_id)
        if not book:
            return None
        
        # Ensure the review is for the correct book
        review.book_id = book_id
        
        # Create the review
        created_review = await self.review_service.create_review(review)
        return created_review
    
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
    
    # === AI Feature Operations ===
    
    async def get_book_with_ai_summary(self, book_id: int) -> Optional[BookDomain]:
        """
        Get a book by ID and generate an AI summary if it doesn't have one.
        
        Args:
            book_id: The ID of the book to retrieve
            
        Returns:
            The book domain model with summary if found, None otherwise
        """
        book = await self.book_service.get_book(book_id)
        if book and not book.summary:
            # This is a simplified example. In a real application, you would need
            # to have the book content available or fetch it from somewhere.
            book_content = f"This is a placeholder for the content of '{book.title}' by {book.author}."
            summary = await self.llm_service.generate_book_summary(book.title, book_content)
            
            # Update the book with the generated summary
            book.summary = summary
            book = await self.book_service.update_book(book)
        
        return book
    
    async def get_book_summary_and_rating(self, book_id: int) -> Optional[Tuple[str, float]]:
        """
        Get a book's summary and average rating.
        
        Args:
            book_id: The ID of the book
            
        Returns:
            Tuple of (summary, average_rating) if the book exists, None otherwise
        """
        # Get the book
        book = await self.book_service.get_book(book_id)
        if not book:
            return None
        
        # Get the average rating
        average_rating = await self.review_service.get_average_rating(book_id)
        
        return (book.summary, average_rating)
    
    async def get_recommendations(self, user_id: int, limit: int = 5) -> List[BookDomain]:
        """
        Get book recommendations for a user.
        
        Args:
            user_id: The ID of the user for whom to get recommendations
            limit: Maximum number of recommendations to return
            
        Returns:
            List of recommended book domain models
        """
        # This is a placeholder implementation
        # In a real application, you would implement recommendation logic based on:
        # - User's reading history
        # - User's ratings
        # - Similar users' preferences
        # - Popular books in genres the user likes
        # - etc.
        
        # For now, just return the most recent books
        return await self.book_service.get_books(skip=0, limit=limit)
    
    async def generate_summary(self, text: str) -> str:
        """
        Generate a summary for arbitrary text.
        
        Args:
            text: The text to summarize
            
        Returns:
            The generated summary
        """
        return await self.llm_service.generate_text_summary(text)
