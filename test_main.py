# test_main.py
# Contains automated tests for the FastAPI application using pytest and httpx.
# Focuses on testing API endpoints, including success cases, error handling, and validation.

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment variables from a .env file (especially for TEST_ASYNC_DATABASE_URL)
load_dotenv()

# --- Test Database Configuration ---
# CRITICAL: Use a SEPARATE database for testing to avoid data corruption.
TEST_ASYNC_DATABASE_URL = os.getenv("TEST_ASYNC_DATABASE_URL")

if not TEST_ASYNC_DATABASE_URL:
    # Fallback only if absolutely necessary for local dev, but strongly discouraged.
    # Best practice is to fail the tests if the test DB URL isn't configured.
    print("ERROR: TEST_ASYNC_DATABASE_URL environment variable not set. Tests require a separate database.")
    # pytest.exit("TEST_ASYNC_DATABASE_URL not set. Exiting tests.", returncode=1)
    # Or use a predictable default if you MUST, e.g., for CI environments that set it up:
    TEST_ASYNC_DATABASE_URL = "postgresql+asyncpg://test_user:test_password@localhost:5432/test_book_db"
    print(f"Warning: Using default test database URL: {TEST_ASYNC_DATABASE_URL}")

# --- Test Engine and Session ---
# Create a new engine and session factory specifically for testing.
test_engine = create_async_engine(TEST_ASYNC_DATABASE_URL, echo=False) # Disable SQL echo for tests
TestAsyncSessionFactory = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

# --- Import Application and Dependencies ---
# Import Base from database AFTER setting up the test engine if models depend on it implicitly.
# A better pattern is using an app factory to inject settings.
from database import Base, get_db
# Import the FastAPI app instance
from main import app
# Import models for potential direct DB manipulation in tests if needed
import models
import schemas # Import schemas for validating responses

# --- Test Fixtures ---

@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """
    Pytest fixture (run once per session) to initialize the test database.
    Drops and recreates all tables defined in models.Base.
    WARNING: Ensures a clean state but DELETES ALL DATA in the test database.
    """
    async with test_engine.begin() as conn:
        print(f"\n--- Setting up test database: {TEST_ASYNC_DATABASE_URL} ---")
        print("Dropping all tables...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("--- Test database setup complete ---")
    yield # Let the tests run
    # Optional: Teardown after all tests in the session are done
    # async with test_engine.begin() as conn:
    #     print("\n--- Tearing down test database ---")
    #     await conn.run_sync(Base.metadata.drop_all)
    # print("--- Test database teardown complete ---")


@pytest.fixture
async def db_session() -> AsyncSession:
    """
    Pytest fixture (run per test function) providing a clean database session.
    Uses the TestAsyncSessionFactory and rolls back changes after the test.
    """
    async with TestAsyncSessionFactory() as session:
        try:
            yield session
        finally:
            # Rollback any changes made during the test to keep tests isolated
            await session.rollback()
            await session.close()


@pytest.fixture
async def async_client(db_session: AsyncSession) -> AsyncClient:
    """
    Pytest fixture providing an HTTPX AsyncClient configured to talk to the test app.
    Overrides the `get_db` dependency to use the isolated `db_session` fixture.
    """
    # Override the application's database dependency to use the test session
    def override_get_db():
        try:
            yield db_session
        finally:
            # The db_session fixture handles rollback/close
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Create the async client pointing to the test app
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client

    # Clean up the dependency override after the test
    del app.dependency_overrides[get_db]


# --- Test Cases ---

@pytest.mark.asyncio
class TestBookEndpoints:
    """Groups tests related to the /books endpoints."""

    async def test_create_book_success(self, async_client: AsyncClient):
        """Test successfully creating a new book."""
        book_data = {
            "title": "The Test Book", "author": "Tester T. Author",
            "genre": "Testing", "year_published": 2025, "summary": "A book created during testing."
        }
        response = await async_client.post("/books", json=book_data)
        assert response.status_code == 201
        data = response.json()
        # Validate response against the schema
        schemas.Book(**data)
        assert data["title"] == book_data["title"]
        assert data["author"] == book_data["author"]
        assert data["id"] is not None

    async def test_create_book_duplicate(self, async_client: AsyncClient):
        """Test creating a book that already exists (title/author unique constraint)."""
        book_data = {"title": "Duplicate Test Book", "author": "Duplicate Author"}
        # Create it once
        response1 = await async_client.post("/books", json=book_data)
        assert response1.status_code == 201
        # Try creating it again
        response2 = await async_client.post("/books", json=book_data)
        assert response2.status_code == 400 # Expect Bad Request
        assert "already exists" in response2.json()["detail"]

    async def test_create_book_invalid_data(self, async_client: AsyncClient):
        """Test creating a book with missing required fields (e.g., title)."""
        invalid_data = {"author": "Author Only"} # Missing title
        response = await async_client.post("/books", json=invalid_data)
        assert response.status_code == 422 # Unprocessable Entity (validation error)

    async def test_get_book_not_found(self, async_client: AsyncClient):
        """Test retrieving a book with an ID that doesn't exist."""
        response = await async_client.get("/books/999999")
        assert response.status_code == 404

    async def test_get_books_list(self, async_client: AsyncClient):
        """Test retrieving the list of books."""
        # Create a book first to ensure the list isn't empty
        await async_client.post("/books", json={"title": "List Test Book", "author": "Lister"})
        response = await async_client.get("/books")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0 # Should contain the book created above (and potentially others)
        # Validate items in the list against the schema
        for item in data:
            schemas.Book(**item)

    async def test_get_specific_book(self, async_client: AsyncClient):
        """Test creating a book and then retrieving it by its ID."""
        book_data = {"title": "Specific Get Test", "author": "Getter"}
        create_response = await async_client.post("/books", json=book_data)
        assert create_response.status_code == 201
        book_id = create_response.json()["id"]

        get_response = await async_client.get(f"/books/{book_id}")
        assert get_response.status_code == 200
        data = get_response.json()
        schemas.Book(**data)
        assert data["id"] == book_id
        assert data["title"] == book_data["title"]

    async def test_update_book(self, async_client: AsyncClient):
        """Test creating a book and then updating its details."""
        book_data = {"title": "Update Me", "author": "Updater", "genre": "Old Genre"}
        create_response = await async_client.post("/books", json=book_data)
        book_id = create_response.json()["id"]

        update_payload = {"genre": "New Genre", "summary": "Updated Summary"}
        update_response = await async_client.put(f"/books/{book_id}", json=update_payload)
        assert update_response.status_code == 200
        data = update_response.json()
        schemas.Book(**data)
        assert data["id"] == book_id
        assert data["title"] == book_data["title"] # Title wasn't updated
        assert data["genre"] == update_payload["genre"] # Genre should be updated
        assert data["summary"] == update_payload["summary"] # Summary should be updated

    async def test_update_book_not_found(self, async_client: AsyncClient):
        """Test updating a book that doesn't exist."""
        update_payload = {"title": "Ghost Title"}
        response = await async_client.put("/books/999999", json=update_payload)
        assert response.status_code == 404

    async def test_delete_book(self, async_client: AsyncClient):
        """Test creating a book and then deleting it."""
        book_data = {"title": "Delete Me", "author": "Deleter"}
        create_response = await async_client.post("/books", json=book_data)
        book_id = create_response.json()["id"]

        # Delete the book
        delete_response = await async_client.delete(f"/books/{book_id}")
        assert delete_response.status_code == 200
        # Verify the returned data matches the deleted book
        deleted_data = delete_response.json()
        schemas.Book(**deleted_data)
        assert deleted_data["id"] == book_id
        assert deleted_data["title"] == book_data["title"]

        # Try to get the deleted book, should be 404
        get_response = await async_client.get(f"/books/{book_id}")
        assert get_response.status_code == 404

    async def test_delete_book_not_found(self, async_client: AsyncClient):
        """Test deleting a book that doesn't exist."""
        response = await async_client.delete("/books/999999")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestReviewEndpoints:
    """Groups tests related to the /books/{book_id}/reviews endpoints."""

    @pytest.fixture(scope="class")
    async def test_book(self, async_client: AsyncClient):
        """Fixture to create a book available for all tests in this class."""
        book_data = {"title": "Review Test Book", "author": "Reviewer"}
        response = await async_client.post("/books", json=book_data)
        assert response.status_code == 201
        return response.json() # Return the created book data (including ID)

    async def test_create_review_success(self, async_client: AsyncClient, test_book):
        """Test successfully creating a review for an existing book."""
        book_id = test_book["id"]
        review_data = {"user_id": 123, "rating": 4.5, "review_text": "Great book for testing!"}
        response = await async_client.post(f"/books/{book_id}/reviews", json=review_data)
        assert response.status_code == 201
        data = response.json()
        schemas.Review(**data) # Validate response schema
        assert data["book_id"] == book_id
        assert data["user_id"] == review_data["user_id"]
        assert data["rating"] == review_data["rating"]
        assert data["review_text"] == review_data["review_text"]
        assert data["id"] is not None

    async def test_create_review_for_nonexistent_book(self, async_client: AsyncClient):
        """Test creating a review for a book ID that doesn't exist."""
        review_data = {"user_id": 456, "rating": 3.0}
        response = await async_client.post("/books/999999/reviews", json=review_data)
        assert response.status_code == 404 # Expect Not Found for the book

    async def test_create_review_invalid_rating(self, async_client: AsyncClient, test_book):
        """Test creating a review with an invalid rating (e.g., > 5)."""
        book_id = test_book["id"]
        invalid_review = {"user_id": 789, "rating": 6.0} # Rating out of range
        response = await async_client.post(f"/books/{book_id}/reviews", json=invalid_review)
        assert response.status_code == 422 # Validation error

    async def test_get_reviews_for_book(self, async_client: AsyncClient, test_book):
        """Test retrieving reviews for a specific book."""
        book_id = test_book["id"]
        # Add a review first
        await async_client.post(f"/books/{book_id}/reviews", json={"user_id": 101, "rating": 5.0})

        response = await async_client.get(f"/books/{book_id}/reviews")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0 # Should contain the review created above
        for item in data:
            schemas.Review(**item) # Validate schema
            assert item["book_id"] == book_id

    async def test_get_reviews_for_nonexistent_book(self, async_client: AsyncClient):
        """Test retrieving reviews for a book ID that doesn't exist."""
        response = await async_client.get("/books/999999/reviews")
        assert response.status_code == 404


@pytest.mark.asyncio
class TestAISummaryEndpoints:
    """Groups tests related to AI summary and rating endpoints."""
    # Mocking the LLM client would be ideal here to avoid actual LLM calls during tests

    @pytest.fixture(scope="class")
    async def test_book_with_reviews(self, async_client: AsyncClient):
        """Fixture to create a book and add some reviews."""
        book_data = {"title": "Summary Test Book", "author": "Summarizer", "summary": "Original Summary."}
        response = await async_client.post("/books", json=book_data)
        assert response.status_code == 201
        book = response.json()
        book_id = book["id"]
        # Add reviews
        await async_client.post(f"/books/{book_id}/reviews", json={"user_id": 201, "rating": 4.0})
        await async_client.post(f"/books/{book_id}/reviews", json={"user_id": 202, "rating": 5.0})
        return book # Return the created book data

    async def test_get_book_summary_and_rating(self, async_client: AsyncClient, test_book_with_reviews):
        """Test retrieving the book's summary and calculated average rating."""
        book_id = test_book_with_reviews["id"]
        response = await async_client.get(f"/books/{book_id}/summary")
        assert response.status_code == 200
        data = response.json()
        schemas.BookSummary(**data) # Validate schema
        assert data["summary"] == test_book_with_reviews["summary"]
        assert data["average_rating"] == pytest.approx(4.5) # Average of 4.0 and 5.0

    async def test_get_summary_for_book_no_reviews(self, async_client: AsyncClient):
        """Test summary endpoint for a book with no reviews (rating should be None)."""
        book_data = {"title": "No Reviews Book", "author": "Lonely"}
        response = await async_client.post("/books", json=book_data)
        book_id = response.json()["id"]

        response = await async_client.get(f"/books/{book_id}/summary")
        assert response.status_code == 200
        data = response.json()
        schemas.BookSummary(**data)
        assert data["average_rating"] is None

    async def test_get_summary_for_nonexistent_book(self, async_client: AsyncClient):
         """Test summary endpoint for a book ID that doesn't exist."""
         response = await async_client.get("/books/999999/summary")
         assert response.status_code == 404

    # --- Tests for /generate-summary (requires mocking LLM) ---
    # Example using pytest-mock (install it: pip install pytest-mock)
    async def test_generate_summary_endpoint_success(self, async_client: AsyncClient, mocker):
         """Test the /generate-summary endpoint with a mocked LLM call."""
         # Mock the actual LLM function in the llm module
         mocked_llm_call = mocker.patch("llm.generate_summary_async", return_value="This is a mocked summary.")

         payload = {"text_content": "This is some text content that needs summarizing."}
         response = await async_client.post("/generate-summary", json=payload)

         assert response.status_code == 200
         data = response.json()
         schemas.GeneratedSummary(**data)
         assert data["generated_summary"] == "This is a mocked summary."
         # Verify the mock was called correctly
         mocked_llm_call.assert_called_once()
         # Can add more specific assertions about call arguments if needed

    async def test_generate_summary_endpoint_llm_error(self, async_client: AsyncClient, mocker):
        """Test the /generate-summary endpoint when the LLM call raises an error."""
        mocked_llm_call = mocker.patch("llm.generate_summary_async", side_effect=RuntimeError("LLM failed"))

        payload = {"text_content": "Content that will cause an error."}
        response = await async_client.post("/generate-summary", json=payload)

        assert response.status_code == 500 # Expect Internal Server Error
        assert "Failed to generate summary" in response.json()["detail"]
        mocked_llm_call.assert_called_once()

    async def test_generate_summary_endpoint_no_content(self, async_client: AsyncClient):
        """Test the /generate-summary endpoint with invalid input (no content)."""
        response = await async_client.post("/generate-summary", json={"text_content": ""})
        assert response.status_code == 400 # Expect Bad Request


# --- Add tests for /recommendations (likely needs mocking) ---
# --- Add tests for utility endpoints like /health ---

@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    """Test the health check endpoint."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

