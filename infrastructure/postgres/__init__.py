# infrastructure/postgres/__init__.py
from .book_repository import PostgresBookRepository
from .review_repository import PostgresReviewRepository

__all__ = [
    'PostgresBookRepository',
    'PostgresReviewRepository',
]
