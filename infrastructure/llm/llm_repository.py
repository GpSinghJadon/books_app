# infrastructure/llm/llm_repository.py
from typing import List
from domain.repositories import LlmRepositoryProtocol
from llm import LocalLlamaClientPlaceholder, generate_summary_async

class LlmRepository(LlmRepositoryProtocol):
    """Implementation of the LLM repository using the local Llama model."""
    
    def __init__(self):
        """Initialize the LLM client."""
        self.client = LocalLlamaClientPlaceholder()
    
    async def generate_summary(self, text: str) -> str:
        """Generate a summary for the given text using the LLM."""
        return await generate_summary_async(self.client, text)
    
    async def generate_book_summary(self, book_title: str, book_content: str) -> str:
        """Generate a summary specifically for a book."""
        prompt = f"""Please provide a concise, one-paragraph summary (around 50-100 words) of the book titled "{book_title}":

        Book Content:
        \"\"\"
        {book_content}
        \"\"\"

        Summary:"""
        
        try:
            summary = await self.client.generate(prompt=prompt, max_tokens=200, temperature=0.5)
            return summary
        except Exception as e:
            print(f"Error during book summary generation: {e}")
            raise RuntimeError(f"AI book summary generation failed.") from e
    
    async def generate_review_summary(self, reviews: List[str]) -> str:
        """Generate a summary of multiple reviews."""
        combined_reviews = "\n".join(f"- {r}" for r in reviews)
        prompt = f"""Summarize the key points and overall sentiment from these book reviews:

        Reviews:
        {combined_reviews}

        Summary:"""
        
        try:
            summary = await self.client.generate(prompt=prompt, max_tokens=150, temperature=0.5)
            return summary
        except Exception as e:
            print(f"Error during review summary generation: {e}")
            raise RuntimeError(f"AI review summary generation failed.") from e
