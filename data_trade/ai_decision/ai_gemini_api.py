import os
import logging
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


class GeminiApiAgent:
    """
    Pure Transport Driver for Google Gemini API.
    Responsible ONLY for sending prompt text and returning raw text response.
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-3.5-flash-lite"):
        if api_key is not None and not isinstance(api_key, str):
            raise TypeError(f"FAIL-FAST: api_key must be a string, got {type(api_key)}")
        if not isinstance(model_name, str):
            raise TypeError(f"FAIL-FAST: model_name must be a string, got {type(model_name)}")
            
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("FAIL-FAST: GEMINI_API_KEY is not set in environment or .env file.")
            
        self.model_name = model_name
        
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            logger.info(f"Initialized Gemini Transport Driver via google.genai ({self.model_name})")
        except Exception as e:
            logger.exception("Could not initialize Google GenAI client.")
            raise RuntimeError(f"FAIL-FAST: Google GenAI client initialization failed: {e}") from e

    def send_prompt(self, user_prompt: str, system_instruction: str = "") -> str:
        """
        Sends user prompt and system instruction to Gemini API and returns raw text response.
        """
        if not isinstance(user_prompt, str) or not user_prompt.strip():
            raise ValueError("FAIL-FAST: user_prompt must be a non-empty string.")

        try:
            logger.info(f"[Gemini Transport] Dispatching prompt to model {self.model_name}...")
            from google.genai import types
            
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
            if system_instruction:
                config.system_instruction = system_instruction

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=config
            )
            return (response.text or "").strip()

        except Exception as e:
            logger.exception(f"[Gemini Transport] API call failed on model {self.model_name}: {e}")
            raise RuntimeError(f"FAIL-FAST: Gemini API call failed: {e}") from e
