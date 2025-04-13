# infrastructure/postgres/review_repository.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from domain.models import ReviewDomain
from domain.repositories import ReviewRepositoryProtocol
from .models import Review
from .base_repository import BasePostgresRepository

class PostgresReviewRepository(BasePostgresRepository[ReviewDomain, Review], ReviewRepositoryProtocol):
    """PostgreSQL implementation of the Review repository."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Review, ReviewDomain)
    
    async def get_by_book_id(self, book_id: int) -> List[ReviewDomain]:
        """Get all reviews for a specific book."""
        query = select(self.model).where(self.model.book_id == book_id)
        result = await self.session.execute(query)
        db_models = result.scalars().all()
        return self._to_domain_list(db_models)
    
    async def get_by_user_id(self, user_id: int) -> List[ReviewDomain]:
        """Get all reviews by a specific user."""
        query = select(self.model).where(self.model.user_id == user_id)
        result = await self.session.execute(query)
        db_models = result.scalars().all()
        return self._to_domain_list(db_models)
    
    async def get_average_rating_for_book(self, book_id: int) -> float:
        """Get the average rating for a specific book."""
        query = select(func.avg(self.model.rating)).where(self.model.book_id == book_id)
        result = await self.session.execute(query)
        avg_rating = result.scalar()
        return avg_rating or 0.0
