# main.py
# Main FastAPI application file

import os
from fastapi import FastAPI

# Import the router
from router import router

app = FastAPI(
    title="Intelligent Book Management System",
    description="API for managing books and reviews, with AI-powered summaries and recommendations.",
    version="1.0.0",
    # Add OpenAPI tags for better documentation organization
    openapi_tags=[
        {"name": "Books", "description": "Operations related to books."},
        {"name": "Reviews", "description": "Operations related to book reviews."},
        {"name": "AI Features", "description": "Operations using the AI model."},
        {"name": "Utilities", "description": "Utility endpoints like health checks."},
    ]
)

# Include the router
app.include_router(router)

# --- Running the App (Example using Uvicorn) ---
if __name__ == "__main__":
    import uvicorn
    # Get host and port from environment variables or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true" # Enable reload in dev

    print(f"Starting Uvicorn server on {host}:{port} with reload={'enabled' if reload else 'disabled'}")
    uvicorn.run("main:app", host=host, port=port, reload=reload)
