import pytest
from unittest.mock import AsyncMock, patch
from domain.services.llm_service import LlmService
from domain.repositories.llm_repository_protocol import LlmRepositoryProtocol

class TestLlmService:
    @pytest.fixture
    def mock_llm_repository(self):
        """Create a mock LLM repository."""
        mock_repo = AsyncMock(spec=LlmRepositoryProtocol)
        mock_repo.generate_summary.return_value = "This is a generated summary."
        mock_repo.generate_book_summary.return_value = "This is a generated book summary."
        mock_repo.generate_review_summary.return_value = "This is a generated review summary."
        return mock_repo
    
    @pytest.fixture
    def llm_service(self, mock_llm_repository):
        """Create an LLM service with a mock repository."""
        return LlmService(mock_llm_repository)
    
    async def test_generate_text_summary(self, llm_service, mock_llm_repository):
        """Test generating a text summary."""
        text = "This is some text to summarize."
        summary = await llm_service.generate_text_summary(text)
        
        mock_llm_repository.generate_summary.assert_called_once_with(text)
        assert summary == "This is a generated summary."
    
    async def test_generate_book_summary(self, llm_service, mock_llm_repository):
        """Test generating a book summary."""
        title = "Test Book"
        content = "This is the content of the test book."
        summary = await llm_service.generate_book_summary(title, content)
        
        mock_llm_repository.generate_book_summary.assert_called_once_with(title, content)
        assert summary == "This is a generated book summary."
    
    async def test_generate_review_summary(self, llm_service, mock_llm_repository):
        """Test generating a review summary."""
        reviews = ["Review 1", "Review 2", "Review 3"]
        summary = await llm_service.generate_review_summary(reviews)
        
        mock_llm_repository.generate_review_summary.assert_called_once_with(reviews)
        assert summary == "This is a generated review summary."
    
    async def test_repository_error_handling(self, llm_service, mock_llm_repository):
        """Test error handling when the repository raises an exception."""
        mock_llm_repository.generate_summary.side_effect = RuntimeError("Repository error")
        
        with pytest.raises(RuntimeError) as excinfo:
            await llm_service.generate_text_summary("Some text")
        
        assert "Repository error" in str(excinfo.value)
