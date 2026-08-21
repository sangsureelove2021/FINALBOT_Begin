"""
Gemini API Transport Driver for Part 3
=======================================
Pure transport layer: sends prompt → returns raw text response.
Primary model  : gemini-3.5-flash-lite
Fallback model : gemini-3.1-flash-lite
Supports both synchronous (send_prompt) and asynchronous (send_prompt_async) dispatch.
"""

import os
import asyncio
import logging
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

PRIMARY_MODEL = "gemini-3.5-flash-lite"
FALLBACK_MODEL = "gemini-3.1-flash-lite"

_FALLBACK_TRIGGERS = [
    "404", "not_found", "not found",
    "503", "high demand", "unavailable",
    "resource_exhausted", "429", "rate"
]


class GeminiApiAgent:
    """
    Pure Transport Driver for Google Gemini API.
    Responsible ONLY for sending prompt text and returning raw text response.
    Primary: gemini-3.5-flash-lite | Fallback: gemini-3.1-flash-lite
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = PRIMARY_MODEL):
        if api_key is not None and not isinstance(api_key, str):
            raise TypeError(f"FAIL-FAST: api_key must be a string, got {type(api_key)}")
        if not isinstance(model_name, str):
            raise TypeError(f"FAIL-FAST: model_name must be a string, got {type(model_name)}")

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("FAIL-FAST: GEMINI_API_KEY is not set in environment or .env file.")

        self.model_name = model_name
        self._models_to_try = self._build_model_list(model_name)

        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            logger.info(
                f"[GeminiApiAgent] Initialized | Primary: {self._models_to_try[0]} "
                f"| Fallback: {self._models_to_try[1] if len(self._models_to_try) > 1 else 'None'}"
            )
        except Exception as e:
            logger.exception("[GeminiApiAgent] Could not initialize Google GenAI client.")
            raise RuntimeError(f"FAIL-FAST: Google GenAI client initialization failed: {e}") from e

    @staticmethod
    def _build_model_list(primary: str) -> list:
        """Returns ordered [primary, fallback] list with no duplicates."""
        ordered = [primary]
        if FALLBACK_MODEL != primary:
            ordered.append(FALLBACK_MODEL)
        return ordered

    def send_prompt(self, user_prompt: str, system_instruction: str = "") -> str:
        """
        Synchronous dispatch to Gemini API.
        Tries primary model first, then fallback on rate-limit / not-found errors.
        """
        if not isinstance(user_prompt, str) or not user_prompt.strip():
            raise ValueError("FAIL-FAST: user_prompt must be a non-empty string.")

        from google.genai import types
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.2
        )
        if system_instruction:
            config.system_instruction = system_instruction

        last_err = None
        for model in self._models_to_try:
            try:
                logger.info(f"[GeminiApiAgent] Dispatching to model: {model}")
                response = self.client.models.generate_content(
                    model=model,
                    contents=user_prompt,
                    config=config
                )
                txt = (response.text or "").strip()
                if txt:
                    logger.info(f"[GeminiApiAgent] Response received from: {model}")
                    return txt
                logger.warning(f"[GeminiApiAgent] Empty response from {model}, trying next...")
            except Exception as e:
                last_err = e
                err_str = str(e).lower()
                if any(t in err_str for t in _FALLBACK_TRIGGERS):
                    logger.warning(
                        f"[GeminiApiAgent] {model} hit rate-limit/fallback trigger ({e}), switching..."
                    )
                    continue
                logger.exception(f"[GeminiApiAgent] Non-recoverable error on {model}: {e}")
                raise RuntimeError(f"FAIL-FAST: Gemini API call failed: {e}") from e

        if last_err is not None:
            logger.error(
                f"[GeminiApiAgent] All models exhausted. Last error: {last_err}",
                exc_info=(type(last_err), last_err, last_err.__traceback__)
            )
        else:
            logger.error("[GeminiApiAgent] All models exhausted with no captured error.")
        raise RuntimeError(
            f"FAIL-FAST: Gemini API failed on all models [{', '.join(self._models_to_try)}]: {last_err}"
        ) from last_err

    async def send_prompt_async(self, user_prompt: str, system_instruction: str = "") -> str:
        """
        Asynchronous dispatch — used by asyncio.gather() for N-symbol concurrent calls.
        Runs blocking send_prompt() in a thread pool executor to avoid blocking the event loop.
        """
        if not isinstance(user_prompt, str) or not user_prompt.strip():
            raise ValueError("FAIL-FAST: user_prompt must be a non-empty string.")

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.send_prompt, user_prompt, system_instruction)
