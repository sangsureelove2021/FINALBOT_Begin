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

        models_to_try = [self.model_name]
        if "gemini-3.5-flash-lite" not in models_to_try:
            models_to_try.append("gemini-3.5-flash-lite")
        if "gemini-3.6-flash" not in models_to_try:
            models_to_try.append("gemini-3.6-flash")

        from google.genai import types
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2
        )
        if system_instruction:
            config.system_instruction = system_instruction

        last_err = None
        for m in models_to_try:
            try:
                logger.info(f"[Gemini Transport] Dispatching prompt to model {m}...")
                response = self.client.models.generate_content(
                    model=m,
                    contents=user_prompt,
                    config=config
                )
                txt = (response.text or "").strip()
                if txt:
                    return txt
            except Exception as e:
                last_err = e
                err_str = str(e).lower()
                fallback_triggers = ["404", "not_found", "not found", "503", "high demand", "unavailable", "resource_exhausted", "429"]
                if any(trigger in err_str for trigger in fallback_triggers):
                    logger.warning(f"[Gemini Transport] Model {m} failed with fallback error ({e}), falling back to next available model...", exc_info=True)
                    continue
                else:
                    logger.exception(f"[Gemini Transport] API call failed on model {m}: {e}")
                    raise RuntimeError(f"FAIL-FAST: Gemini API call failed: {e}") from e

        logger.exception(f"[Gemini Transport] All model candidates failed: {last_err}")
        raise RuntimeError(f"FAIL-FAST: Gemini API call failed on all candidate models: {last_err}") from last_err
