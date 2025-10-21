"""
LLM Client wrapper for Ollama integration.
Provides methods for text generation with retry logic, timeout handling, and output parsing.
"""

import json
import time
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass
import requests
from requests.exceptions import RequestException, Timeout


@dataclass
class LLMResponse:
    """Response from LLM generation."""
    text: str
    model: str
    tokens_used: Optional[int] = None
    generation_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class OllamaClient:
    """Client for interacting with Ollama LLM API."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Base URL for Ollama API
            model: Default model to use
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None
    ) -> LLMResponse:
        """
        Generate text from prompt.
        
        Args:
            prompt: User prompt
            model: Model to use (overrides default)
            system_prompt: System prompt for context
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stop_sequences: Sequences that stop generation
            
        Returns:
            LLMResponse with generated text
            
        Raises:
            RequestException: If API request fails
            TimeoutError: If request times out
        """
        model_name = model or self.model
        start_time = time.time()
        
        # Build request payload
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        if stop_sequences:
            payload["options"]["stop"] = stop_sequences
        
        # Make API request
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            generation_time = time.time() - start_time
            
            return LLMResponse(
                text=result.get("response", ""),
                model=model_name,
                tokens_used=result.get("eval_count"),
                generation_time=generation_time,
                metadata={
                    "total_duration": result.get("total_duration"),
                    "load_duration": result.get("load_duration"),
                    "prompt_eval_count": result.get("prompt_eval_count")
                }
            )
        
        except Timeout:
            raise TimeoutError(f"Request timed out after {self.timeout} seconds")
        except RequestException as e:
            raise RequestException(f"API request failed: {str(e)}")
    
    def generate_with_retry(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stop_sequences: Optional[List[str]] = None,
        retry_delay: float = 2.0
    ) -> LLMResponse:
        """
        Generate text with automatic retry on failure.
        
        Args:
            prompt: User prompt
            model: Model to use
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stop_sequences: Stop sequences
            retry_delay: Delay between retries in seconds
            
        Returns:
            LLMResponse with generated text
            
        Raises:
            Exception: If all retry attempts fail
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return self.generate(
                    prompt=prompt,
                    model=model,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stop_sequences=stop_sequences
                )
            except (RequestException, TimeoutError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    break
        
        raise Exception(f"Failed after {self.max_retries} attempts. Last error: {str(last_error)}")
    
    def stream_generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        callback: Optional[Callable[[str], None]] = None
    ) -> LLMResponse:
        """
        Generate text with streaming output.
        
        Args:
            prompt: User prompt
            model: Model to use
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            callback: Function to call with each chunk of text
            
        Returns:
            LLMResponse with complete generated text
            
        Raises:
            RequestException: If API request fails
        """
        model_name = model or self.model
        start_time = time.time()
        
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": True,
            "options": {
                "temperature": temperature
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            full_text = ""
            total_tokens = 0
            
            for line in response.iter_lines():
                if line:
                    chunk = json.loads(line)
                    text_chunk = chunk.get("response", "")
                    full_text += text_chunk
                    
                    if callback:
                        callback(text_chunk)
                    
                    if chunk.get("done", False):
                        total_tokens = chunk.get("eval_count", 0)
                        break
            
            generation_time = time.time() - start_time
            
            return LLMResponse(
                text=full_text,
                model=model_name,
                tokens_used=total_tokens,
                generation_time=generation_time
            )
        
        except RequestException as e:
            raise RequestException(f"Streaming request failed: {str(e)}")
    
    def parse_json_response(self, response: LLMResponse) -> Dict[str, Any]:
        """
        Parse JSON from LLM response.
        
        Args:
            response: LLMResponse object
            
        Returns:
            Parsed JSON as dictionary
            
        Raises:
            ValueError: If response is not valid JSON
        """
        try:
            # Try to find JSON in the response
            text = response.text.strip()
            
            # Handle markdown code blocks
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            text = text.strip()
            return json.loads(text)
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON from response: {str(e)}")
    
    def parse_list_response(self, response: LLMResponse, delimiter: str = "\n") -> List[str]:
        """
        Parse list from LLM response.
        
        Args:
            response: LLMResponse object
            delimiter: Delimiter to split on
            
        Returns:
            List of strings
        """
        text = response.text.strip()
        items = [item.strip() for item in text.split(delimiter) if item.strip()]
        
        # Remove common list markers
        cleaned_items = []
        for item in items:
            # Remove numbered list markers (1. 2. etc.)
            if item and item[0].isdigit() and ". " in item[:4]:
                item = item.split(". ", 1)[1]
            # Remove bullet points
            item = item.lstrip("•-*").strip()
            if item:
                cleaned_items.append(item)
        
        return cleaned_items
    
    def extract_code_block(self, response: LLMResponse, language: Optional[str] = None) -> str:
        """
        Extract code block from markdown-formatted response.
        
        Args:
            response: LLMResponse object
            language: Expected language (e.g., 'python', 'json')
            
        Returns:
            Extracted code as string
        """
        text = response.text
        
        # Look for code blocks
        if language:
            marker = f"```{language}"
            if marker in text:
                start = text.index(marker) + len(marker)
                end = text.index("```", start)
                return text[start:end].strip()
        
        # Generic code block
        if "```" in text:
            start = text.index("```") + 3
            # Skip language identifier if present
            if text[start] != '\n':
                start = text.index('\n', start) + 1
            end = text.index("```", start)
            return text[start:end].strip()
        
        return text.strip()
    
    def health_check(self) -> bool:
        """
        Check if Ollama service is available.
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except RequestException:
            return False
    
    def list_models(self) -> List[str]:
        """
        List available models.
        
        Returns:
            List of model names
            
        Raises:
            RequestException: If API request fails
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            
            data = response.json()
            return [model["name"] for model in data.get("models", [])]
        
        except RequestException as e:
            raise RequestException(f"Failed to list models: {str(e)}")
