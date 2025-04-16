# infrastructure/llm/llm_repository.py
import os
from typing import List
import ollama
from domain.repositories import LlmRepositoryProtocol

class LlmRepository(LlmRepositoryProtocol):
    """Implementation of the LLM repository using the local Llama model."""
    
    def __init__(self):
        """Initialize the LLM client."""
        # Configure Ollama client
        ollama_host = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        # Set the Ollama host for the client
        ollama.host = ollama_host
        
        # Store configuration parameters
        self.model = os.getenv("OLLAMA_MODEL", "llama2")
        self.max_tokens = int(os.getenv("OLLAMA_MAX_TOKENS", "2048"))
        self.temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
        self.top_p = float(os.getenv("OLLAMA_TOP_P", "0.9"))
    
    async def generate_summary(self, text: str) -> str:
        """Generate a summary for the given text using the LLM."""
        prompt = f"Please summarize the following text concisely:\n\n{text}"
        
        try:
            response = await ollama.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "num_predict": self.max_tokens,
                    "temperature": self.temperature,
                    "top_p": self.top_p
                }
            )
            return response['response'].strip()
        except Exception as e:
            print(f"Error during summary generation: {e}")
            raise RuntimeError(f"AI summary generation failed.") from e
    
    async def generate_book_summary(self, book_title: str, book_content: str) -> str:
        """Generate a summary specifically for a book."""
        prompt = f"""Please provide a concise, one-paragraph summary (around 50-100 words) of the book titled "{book_title}":

        Book Content:
        \"\"\"
        {book_content}
        \"\"\"

        Summary:"""
        
        try:
            # Generate the summary
            response = await ollama.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "num_predict": self.max_tokens,
                    "temperature": self.temperature,
                    "top_p": self.top_p
                }
            )
            return response['response'].strip()
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
            response = await ollama.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "num_predict": self.max_tokens,
                    "temperature": self.temperature,
                    "top_p": self.top_p
                }
            )
            return response['response'].strip()
        except Exception as e:
            print(f"Error during review summary generation: {e}")
            raise RuntimeError(f"AI review summary generation failed.") from e
