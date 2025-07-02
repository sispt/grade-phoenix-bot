"""
🌐 Translation Utility
Provides async translation using googletrans only.
"""

import logging
import asyncio
from typing import Optional

from googletrans import Translator

logger = logging.getLogger(__name__)

async def translate_text(text: str, target_lang: str = "ar") -> str:
    """
    Asynchronously translate text to the target language using googletrans only.
    Uses official API parameters: service_urls, user_agent, and raise_exception.
    Adds strict debugging logs and error handling.
    """
    if not text or not isinstance(text, str):
        logger.debug("translate_text: input is empty or not a string")
        return text
    loop = asyncio.get_running_loop()
    def do_translate():
        try:
            translator = Translator(
                service_urls=["translate.googleapis.com", "translate.google.com"],
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                raise_exception=True
            )
            logger.debug(f"Translating '{text}' to '{target_lang}'")
            result = translator.translate(text, dest=target_lang)
            logger.debug(f"Translation result: {getattr(result, 'text', None)} (raw: {result})")
            return getattr(result, "text", text)
        except Exception as e:
            logger.error(f"googletrans translation failed: {e}", exc_info=True)
            return text
    try:
        translated = await loop.run_in_executor(None, do_translate)
        if translated == text:
            logger.error(f"Translation failed or returned original text: '{text}'")
        return translated
    except Exception as e:
        logger.error(f"Translation async error: {e}", exc_info=True)
        return text 