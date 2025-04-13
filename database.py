# database.py
# Handles asynchronous database connection setup using SQLAlchemy.

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv # To load environment variables from .env file

# Load environment variables from a .env file if it exists
# Useful for local development without setting system environment variables
load_dotenv()

# --- Database Configuration ---
# Get the database connection URL from environment variables.
# Provides flexibility for different environments (dev, test, prod).
# Format: "postgresql+asyncpg://<user>:<password>@<host>:<port>/<database_name>"
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL")
SYNC_DATABASE_URL = os.getenv("SYNC_DATABASE_URL")

if not ASYNC_DATABASE_URL:
    # Provide a default fallback for local development if not set, but raise error if critical
    print("Warning: ASYNC_DATABASE_URL environment variable not set.")
    # You might want to raise an error in production if the URL is missing:
    # raise ValueError("ASYNC_DATABASE_URL environment variable is required but not set.")
    # Using a common default for local PG instance (adjust if needed)
    ASYNC_DATABASE_URL = "postgresql+asyncpg://postgres:admin@localhost:5432/book_management_db"
    SYNC_DATABASE_URL = "postgresql://postgres:admin@localhost:5432/book_management_db"
    print(f"Using default local database URL: {ASYNC_DATABASE_URL}") # Be careful with exposing defaults

# --- SQLAlchemy Engine Setup ---
# Create the asynchronous engine instance.
# `echo=True` logs all SQL statements issued, useful for debugging. Disable in production.
# `future=True` enables SQLAlchemy 2.0 style usage.
try:
    engine = create_async_engine(
        ASYNC_DATABASE_URL,
        echo=os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true", # Control echo via env var
        future=True,
        # Pool size configuration (optional, adjust based on load)
        pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
        pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "30")), # seconds
    )
except Exception as e:
    print(f"Error creating database engine: {e}")
    # Handle error appropriately, maybe exit or raise
    raise

# --- SQLAlchemy Session Factory ---
# Create a factory for generating new AsyncSession instances.
# `expire_on_commit=False` prevents attributes from being expired after commit,
# which is often necessary in async contexts or when accessing objects after commit.
AsyncSessionFactory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False, # Consider autoflush=False for async, manage flushing manually if needed
)

# --- Declarative Base ---
# Base class for all ORM models. They will inherit from this class.
Base = declarative_base()

# --- Database Session Dependency ---
async def get_db() -> AsyncSession:
    """
    FastAPI dependency that provides an asynchronous database session per request.
    Ensures the session is properly closed and transactions are handled.
    Yields:
        AsyncSession: An asynchronous SQLAlchemy session.
    Raises:
        Exception: Re-raises any exception that occurs during the request handling
                   after rolling back the transaction.
    """
    async with AsyncSessionFactory() as session:
        try:
            # Yield the session to the endpoint function
            yield session
            # If no exceptions were raised by the endpoint, commit the transaction
            await session.commit()
        except Exception as e:
            # If any exception occurred, roll back the transaction
            print(f"Rolling back transaction due to error: {e}") # Logging
            await session.rollback()
            # Re-raise the exception so FastAPI can handle it (e.g., return 500 error)
            raise
        finally:
            # Ensure the session is closed, although `async with` handles this
            await session.close()

# --- Optional: Function to Initialize Database (for development/testing) ---
# async def init_db():
#     """
#     (Optional) Creates all database tables defined in models inheriting from Base.
#     Use with caution, especially `drop_all`. Best managed via migration tools like Alembic.
#     """
#     async with engine.begin() as conn:
#         print("Dropping all tables (if uncommented)...")
#         # await conn.run_sync(Base.metadata.drop_all) # DANGEROUS: Deletes all data!
#         print("Creating all tables...")
#         await conn.run_sync(Base.metadata.create_all)
#     print("Database tables initialized.")

# Example of running init_db directly (e.g., `python database.py init`)
# if __name__ == "__main__":
#     import sys
#     if len(sys.argv) > 1 and sys.argv[1] == "init":
#         import asyncio
#         print("Running database initialization...")
#         asyncio.run(init_db())
#     else:
#         print("Database module loaded. Use 'python database.py init' to create tables (caution!).")

