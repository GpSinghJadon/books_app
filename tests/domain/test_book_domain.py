import pytest
from datetime import datetime
from domain.models.book import BookDomain

class TestBookDomain:
    def test_book_creation(self):
        """Test that a book can be created with valid attributes."""
        book = BookDomain(
            title="Test Book",
            author="Test Author",
            genre="Fiction",
            year_published=2023,
            summary="This is a test book summary."
        )
        
        assert book.title == "Test Book"
        assert book.author == "Test Author"
        assert book.genre == "Fiction"
        assert book.year_published == 2023
        assert book.summary == "This is a test book summary."
        assert book.id is None  # ID should be None until persisted
    
    def test_book_creation_with_id(self):
        """Test that a book can be created with an ID (e.g., when loaded from DB)."""
        book = BookDomain(
            id=1,
            title="Test Book",
            author="Test Author",
            genre="Fiction",
            year_published=2023,
            summary="This is a test book summary."
        )
        
        assert book.id == 1
    
    def test_book_creation_with_minimal_attributes(self):
        """Test that a book can be created with only required attributes."""
        book = BookDomain(
            title="Test Book",
            author="Test Author"
        )
        
        assert book.title == "Test Book"
        assert book.author == "Test Author"
        assert book.genre is None
        assert book.year_published is None
        assert book.summary is None
    
    def test_book_equality(self):
        """Test that two books with the same ID are considered equal."""
        book1 = BookDomain(id=1, title="Book", author="Author")
        book2 = BookDomain(id=1, title="Different Book", author="Different Author")
        book3 = BookDomain(id=2, title="Book", author="Author")
        
        assert book1 == book2  # Same ID should make them equal
        assert book1 != book3  # Different ID should make them not equal
    
    def test_book_string_representation(self):
        """Test the string representation of a book."""
        book = BookDomain(
            id=1,
            title="Test Book",
            author="Test Author"
        )
        
        # Assuming __str__ or __repr__ is implemented
        assert str(book) == "BookDomain(id=1, title='Test Book', author='Test Author')" or \
               repr(book) == "BookDomain(id=1, title='Test Book', author='Test Author')"
