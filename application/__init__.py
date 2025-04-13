# application/__init__.py
from .book_application import BookApplication
from .review_application import ReviewApplication

__all__ = [
    'BookApplication',
    'ReviewApplication',
]
