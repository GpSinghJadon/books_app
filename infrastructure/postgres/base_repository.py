# infrastructure/postgres/base_repository.py
from typing import TypeVar, Generic, List, Optional, Type, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete, update
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)
M = TypeVar('M')  # SQLAlchemy model type

class BasePostgresRepository(Generic[T, M]):
    """Base repository implementation with common CRUD operations."""
    
    def __init__(self, session: AsyncSession, model: Type[M], domain_model: Type[T]):
        self.session = session
        self.model = model
        self.domain_model = domain_model
    
    def _to_domain(self, db_model: Optional[M]) -> Optional[T]:
        """Convert a database model to a domain model."""
        if db_model is None:
            return None
        return self.domain_model.from_orm(db_model)
    
    def _to_domain_list(self, db_models: List[M]) -> List[T]:
        """Convert a list of database models to domain models."""
        return [self._to_domain(model) for model in db_models]
    
    def _to_db_model(self, domain_model: T) -> M:
        """Convert a domain model to a database model."""
        data = domain_model.dict(exclude_unset=True)
        if domain_model.id:
            # Update existing model
            instance = self.model(**data)
            instance.id = domain_model.id
            return instance
        else:
            # Create new model
            if 'id' in data:
                del data['id']  # Remove None id for new instances
            return self.model(**data)
    
    async def get_by_id(self, id: int) -> Optional[T]:
        """Retrieve an entity by its ID."""
        query = select(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        db_model = result.scalars().first()
        return self._to_domain(db_model)
    
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Retrieve all entities with pagination."""
        query = select(self.model).offset(skip).limit(limit)
        result = await self.session.execute(query)
        db_models = result.scalars().all()
        return self._to_domain_list(db_models)
    
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        db_model = self._to_db_model(entity)
        self.session.add(db_model)
        await self.session.commit()
        await self.session.refresh(db_model)
        return self._to_domain(db_model)
    
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        if not entity.id:
            raise ValueError("Cannot update entity without ID")
        
        # First, get the existing entity from the database
        query = select(self.model).where(self.model.id == entity.id)
        result = await self.session.execute(query)
        db_model = result.scalars().first()
        
        if not db_model:
            raise ValueError(f"Entity with ID {entity.id} not found")
        
        # Update the model with new values
        entity_data = entity.dict(exclude_unset=True)
        for key, value in entity_data.items():
            if hasattr(db_model, key):
                setattr(db_model, key, value)
        
        # Commit the changes
        await self.session.commit()
        await self.session.refresh(db_model)
        
        return self._to_domain(db_model)

    
    async def delete(self, id: int) -> bool:
        """Delete an entity by its ID."""
        query = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount > 0
