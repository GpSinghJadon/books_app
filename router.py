# router.py
# Router containing all endpoints from the main application

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

import schemas
from database import get_db

# Import domain models and services
from domain.models import BookDomain, ReviewDomain
from domain.services import BookService, ReviewService, LlmService

# Import application services
from application import BookApplication, ReviewApplication

# Import infrastructure implementations
from infrastructure import PostgresBookRepository, PostgresReviewRepository, LlmRepository

# Create the router with the same tags configuration
router = APIRouter()

# --- Dependencies for Application Services ---
async def get_book_application(db: AsyncSession = Depends(get_db)):
    """Dependency to get the BookApplication instance."""
    # Create repositories
    book_repo = PostgresBookRepository(db)
    llm_repo = LlmRepository()
    
    # Create domain services
    book_service = BookService(book_repo)
    llm_service = LlmService(llm_repo)
    review_service = ReviewService(PostgresReviewRepository(db))
    
    # Create and return application service
    return BookApplication(book_service, review_service, llm_service)

async def get_review_application(db: AsyncSession = Depends(get_db)):
    """Dependency to get the ReviewApplication instance."""
    # Create repositories
    review_repo = PostgresReviewRepository(db)
    book_repo = PostgresBookRepository(db)
    llm_repo = LlmRepository()
    
    # Create domain services
    review_service = ReviewService(review_repo)
    book_service = BookService(book_repo)
    llm_service = LlmService(llm_repo)
    
    # Create and return application service
    return ReviewApplication(review_service, book_service, llm_service)

# === Book Endpoints ===

@router.post("/books", response_model=schemas.Book, status_code=201, tags=["Books"],
          summary="Add a new book",
          description="Adds a new book to the database. Optionally generates a summary using the configured AI model if `generate_summary` is true and no summary is provided.")
async def create_book(
    book_in: schemas.BookCreate,
    generate_summary: bool = False,
    app: BookApplication = Depends(get_book_application)
):
    """
    Adds a new book to the system.

    - **book_in**: The book data including title, author, etc.
    - **generate_summary**: If `true` and `book_in.summary` is missing, attempt to generate one using the AI model based on title, author, and genre.
    """
    try:
        # Convert schema to domain model
        book_domain = BookDomain(
            title=book_in.title,
            author=book_in.author,
            genre=book_in.genre,
            year_published=book_in.year_published,
            summary=book_in.summary
        )
        
        # Create book using application service
        created_book = await app.create_book(book_domain, generate_summary)
        
        # Convert back to response schema
        return schemas.Book.from_orm(created_book)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


@router.get("/books", response_model=List[schemas.Book], tags=["Books"],
         summary="Retrieve all books",
         description="Gets a list of all books, with optional pagination using `skip` and `limit` query parameters.")
async def read_books(
    skip: int = 0, 
    limit: int = 100, 
    app: BookApplication = Depends(get_book_application)
):
    """
    Retrieves a list of books with pagination.

    - **skip**: Number of books to skip from the beginning.
    - **limit**: Maximum number of books to return.
    """
    if limit > 1000:  # Add a reasonable upper limit
        limit = 1000
    
    books = await app.get_books(skip, limit)
    return [schemas.Book.from_orm(book) for book in books]


@router.get("/books/{book_id}", response_model=schemas.Book, tags=["Books"],
          summary="Retrieve a specific book by ID",
          description="Gets detailed information for a single book identified by its unique `book_id`.")
async def read_book(
    book_id: int, 
    app: BookApplication = Depends(get_book_application)
):
    """
    Retrieves a single book by its unique ID.

    - **book_id**: The integer ID of the book to retrieve.
    """
    book = await app.get_book(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")
    
    return schemas.Book.from_orm(book)


@router.put("/books/{book_id}", response_model=schemas.Book, tags=["Books"],
         summary="Update a book's information",
         description="Updates the details of an existing book identified by its `book_id`. Only provided fields are updated.")
async def update_book(
    book_id: int, 
    book_in: schemas.BookUpdate, 
    app: BookApplication = Depends(get_book_application)
):
    """
    Updates an existing book. Only fields present in the request body are updated.

    - **book_id**: The ID of the book to update.
    - **book_in**: A JSON object containing the fields to update.
    """
    try:
        # Convert schema to domain model with only the fields to update
        book_update = BookDomain(id=book_id, **book_in.dict(exclude_unset=True))
        
        # Update the book
        updated_book = await app.update_book(book_id, book_update)
        if updated_book is None:
            raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")
        
        return schemas.Book.from_orm(updated_book)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/books/{book_id}", response_model=schemas.Book, tags=["Books"],
            summary="Delete a book by ID",
            description="Removes a book and its associated reviews (due to cascade delete) from the database using its `book_id`.")
async def delete_book(
    book_id: int, 
    app: BookApplication = Depends(get_book_application)
):
    """
    Deletes a book. Associated reviews will also be deleted if cascade is set up correctly in the database model.

    - **book_id**: The ID of the book to delete.
    """
    deleted_book = await app.delete_book(book_id)
    if deleted_book is None:
        raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")
    
    return schemas.Book.from_orm(deleted_book)


# === Review Endpoints ===

@router.post("/books/{book_id}/reviews", response_model=schemas.Review, status_code=201, tags=["Reviews"],
          summary="Add a review for a book",
          description="Adds a new review (including text and rating) for a specific book identified by `book_id`.")
async def create_review_for_book(
    book_id: int, 
    review_in: schemas.ReviewCreate, 
    app: ReviewApplication = Depends(get_review_application)
):
    """
    Adds a review for a specific book.

    - **book_id**: The ID of the book being reviewed.
    - **review_in**: The review details including `user_id`, `review_text`, and `rating`.
    """
    # Convert schema to domain model
    review_domain = ReviewDomain(
        book_id=book_id,
        user_id=review_in.user_id,
        review_text=review_in.review_text,
        rating=review_in.rating
    )
    
    # Create the review
    created_review = await app.create_review(review_domain)
    if created_review is None:
        raise HTTPException(status_code=404, detail=f"Cannot add review: Book with ID {book_id} not found")
    
    return schemas.Review.from_orm(created_review)


@router.get("/books/{book_id}/reviews", response_model=List[schemas.Review], tags=["Reviews"],
         summary="Retrieve all reviews for a book",
         description="Gets all reviews associated with a specific book ID, with optional pagination.")
async def read_reviews_for_book(
    book_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    app: ReviewApplication = Depends(get_review_application)
):
    """
    Retrieves reviews for a specific book with pagination.

    - **book_id**: The ID of the book whose reviews are to be retrieved.
    - **skip**: Number of reviews to skip.
    - **limit**: Maximum number of reviews to return.
    """
    if limit > 1000:  # Add a reasonable upper limit
        limit = 1000
    
    reviews = await app.get_book_reviews(book_id, skip, limit)
    if not reviews and book_id:
        # Check if the book exists
        book_app = await get_book_application(next(get_db()))
        book = await book_app.get_book(book_id)
        if book is None:
            raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")
    
    return [schemas.Review.from_orm(review) for review in reviews]


# === AI Feature Endpoints ===

@router.get("/books/{book_id}/summary", response_model=schemas.BookSummary, tags=["AI Features", "Books"],
          summary="Get summary and aggregated rating",
          description="Retrieves the book's stored summary and calculates its average rating based on all submitted reviews.")
async def get_book_summary_and_rating(
    book_id: int, 
    book_app: BookApplication = Depends(get_book_application),
    review_app: ReviewApplication = Depends(get_review_application)
):
    """
    Gets a book's stored summary and calculates its average rating from reviews.

    - **book_id**: The ID of the book.
    """
    # Get the book
    book = await book_app.get_book(book_id)
    if book is None:
        raise HTTPException(status_code=404, detail=f"Book with ID {book_id} not found")
    
    # Get the average rating
    average_rating = await review_app.get_average_rating(book_id)
    
    # Format the rating nicely (e.g., 2 decimal places) if it exists
    formatted_rating = round(average_rating, 2) if average_rating is not None else None
    
    return schemas.BookSummary(
        summary=book.summary,
        average_rating=formatted_rating
    )


@router.get("/recommendations", response_model=List[schemas.Book], tags=["AI Features"],
         summary="Get book recommendations (Placeholder)",
         description="Provides book recommendations based on user preferences. **Note: This endpoint currently returns a simple list of recent books and requires actual recommendation logic implementation.**")
async def get_recommendations(
    user_id: int, 
    app: BookApplication = Depends(get_book_application)
):
    """
    Gets book recommendations for a specific user.
    **Requires implementation of actual recommendation logic.**

    - **user_id**: The ID of the user for whom to get recommendations.
    """
    recommended_books = await app.get_recommendations(user_id)
    return [schemas.Book.from_orm(book) for book in recommended_books]


@router.post("/generate-summary", response_model=schemas.GeneratedSummary, tags=["AI Features"],
          summary="Generate a summary for arbitrary text",
          description="Uses the configured AI model (e.g., Llama3) to generate a summary for the provided text content.")
async def generate_summary_endpoint(
    content: schemas.SummaryRequest,
    app: BookApplication = Depends(get_book_application)
):
    """
    Generates a summary for arbitrary text content using the AI model.

    - **content**: A JSON object containing the `text_content` to summarize.
    """
    if not content.text_content or len(content.text_content) < 10:  # Basic validation
        raise HTTPException(status_code=400, detail="Text content is missing or too short for summarization.")
    
    try:
        # Generate the summary
        summary = await app.generate_summary(content.text_content)
        return schemas.GeneratedSummary(generated_summary=summary)
    except Exception as e:
        # Catch potential errors from the LLM interaction
        print(f"Error in /generate-summary endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate summary due to an internal error: {str(e)}")


# --- Utility Endpoints ---
@router.get("/health", status_code=200, tags=["Utilities"],
         summary="Health Check",
         description="Simple health check endpoint to verify the API is running.")
async def health_check():
    """Returns a simple JSON response indicating the service is operational."""
    return {"status": "ok", "message": "Book Management API is running"}
