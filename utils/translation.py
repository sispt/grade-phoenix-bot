"""
🌐 Translation Utility
Provides async translation using googletrans only.
"""

import logging
import asyncio
from typing import Optional

# from googletrans import Translator

logger = logging.getLogger(__name__)

async def translate_text(text: str, target_lang: str = "ar", max_retries: int = 10) -> str:
    # """
    # Asynchronously translate text to the target language using googletrans only.
    # Uses official API parameters: service_urls, user_agent, and raise_exception.
    # Adds retry logic with 5 attempts and 200 response checking.
    # """
    # if not text or not isinstance(text, str):
    #     logger.debug("translate_text: input is empty or not a string")
    #     return text
    
    # loop = asyncio.get_running_loop()
    
    # def do_translate():
    #     try:
    #         translator = Translator(
    #             service_urls=["translate.googleapis.com", "translate.google.com"],
    #             user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    #             raise_exception=True
    #         )
    #         logger.debug(f"Translating '{text}' to '{target_lang}'")
    #         result = translator.translate(text, dest=target_lang)
            
    #         # Validate translation result
    #         translated_text = getattr(result, "text", None)
    #         if not translated_text:
    #             logger.warning("Translation returned None or empty text")
    #             return None
                
    #         # Check if translation is actually different from original
    #         if translated_text.strip() == text.strip():
    #             logger.warning("Translation returned same text as original")
    #             return None
                
    #         # Check if translation contains meaningful content
    #         if len(translated_text.strip()) < 2:
    #             logger.warning("Translation too short, likely failed")
    #             return None
                
    #         logger.debug(f"Translation result: {translated_text[:100]}...")
    #         return translated_text
            
    #     except Exception as e:
    #         logger.error(f"googletrans translation failed: {e}", exc_info=True)
    #         return None
    
    # # Retry logic with 10 attempts - all at once without delays
    # for attempt in range(1, max_retries + 1):
    #     try:
    #         logger.info(f"🔄 Translation attempt {attempt}/{max_retries} for text: '{text[:50]}...'")
            
    #         translated = await loop.run_in_executor(None, do_translate)
            
    #         # Check if translation was successful
    #         if translated and translated != text and translated.strip():
    #             logger.info(f"✅ Translation successful on attempt {attempt}: '{translated[:50]}...'")
    #             return translated
    #         else:
    #             logger.warning(f"⚠️ Translation attempt {attempt} failed - returned original text or empty result")
    #             # No delay - continue immediately to next attempt
                    
    #     except Exception as e:
    #         logger.error(f"❌ Translation attempt {attempt} failed with error: {e}")
    #         # No delay - continue immediately to next attempt
    
    # # All attempts failed - fall back to English version
    # logger.error(f"❌ All {max_retries} translation attempts failed for text: '{text[:50]}...' - falling back to English")
    return " "