# infrastructure/postgres/book_repository.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from domain.models import BookDomain
from domain.repositories import BookRepositoryProtocol
from .models import Book
from .base_repository import BasePostgresRepository

class PostgresBookRepository(BasePostgresRepository[BookDomain, Book], BookRepositoryProtocol):
    """PostgreSQL implementation of the Book repository."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Book, BookDomain)
    
    async def get_by_title_and_author(self, title: str, author: str) -> Optional[BookDomain]:
        """Get a book by its title and author."""
        query = select(self.model).where(self.model.title == title, self.model.author == author)
        result = await self.session.execute(query)
        db_model = result.scalars().first()
        return self._to_domain(db_model)
    
    async def get_by_genre(self, genre: str) -> List[BookDomain]:
        """Get all books of a specific genre."""
        query = select(self.model).where(self.model.genre == genre)
        result = await self.session.execute(query)
        db_models = result.scalars().all()
        return self._to_domain_list(db_models)
    
    async def get_by_year(self, year: int) -> List[BookDomain]:
        """Get all books published in a specific year."""
        query = select(self.model).where(self.model.year_published == year)
        result = await self.session.execute(query)
        db_models = result.scalars().all
