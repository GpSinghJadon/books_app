# domain/models.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional

class BookDomain(BaseModel):
    """Domain model for Book entity."""
    id: Optional[int] = None
    title: str
    author: str
    genre: Optional[str] = None
    year_published: Optional[int] = None
    summary: Optional[str] = None
    
    @validator('year_published')
    def validate_year(cls, v):
        if v is not None and (v < 0 or v > 2100):
            raise ValueError('Year published must be between 0 and 2100')
        return v
    
    class Config:
        orm_mode = True

class ReviewDomain(BaseModel):
    """Domain model for Review entity."""
    id: Optional[int] = None
    book_id: int
    user_id: int
    review_text: Optional[str] = None
    rating: float = Field(..., ge=0.0, le=5.0)
    
    class Config:
        orm_mode = True

class BookWithReviews(BookDomain):
    """Domain model for Book with its reviews."""
    reviews: List[ReviewDomain] = []
