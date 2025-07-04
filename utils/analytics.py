"""
Grade Analytics & Quote Support
Enhanced grade display with motivational quotes and daily wisdom.
"""

from typing import Dict, List, Any, Optional
import json
import os
import random
import requests
import asyncio
import logging
import httpx
import re
from googletrans import Translator
import aiohttp
from utils.translation import translate_text

# Configure logging
logger = logging.getLogger(__name__)


class GradeAnalytics:
    """Handles grade analytics with motivational quotes and wisdom"""

    def __init__(self, user_storage):
        self.user_storage = user_storage
        self.analytics_file = "data/grade_analytics.json"
        self.achievements_file = "data/achievements.json"
        self.daily_quotes_file = "data/daily_quotes.json"
        self._ensure_files()

    def _ensure_files(self):
        """Ensure analytics and achievements files exist"""
        for file_path in [
            self.analytics_file,
            self.achievements_file,
            self.daily_quotes_file,
        ]:
            if not os.path.exists(file_path):
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)

    async def get_daily_quote(self) -> dict:
        """Fetch a daily quote in English from APIs, using a broad set of intellectual keywords."""
        keywords = [
            "wisdom", "motivation", "perseverance", "philosophy", "science", "creativity", "knowledge", "learning", "curiosity", "logic", "reason", "ethics", "innovation", "inspiration", "education", "critical thinking", "progress", "leadership", "vision", "purpose", "meaning", "happiness", "success", "failure", "resilience", "growth", "change", "future", "potential", "discovery", "truth", "justice", "freedom", "responsibility", "empathy", "compassion", "humanity", "society", "culture", "art", "beauty", "excellence", "virtue", "integrity", "honesty", "courage", "patience", "humility", "gratitude", "mindfulness", "self-discipline", "self-awareness", "self-improvement"
        ]
        keyword = random.choice(keywords)
        # Always fetch English quotes
        try:
            async with aiohttp.ClientSession() as session:
                # Example: ZenQuotes API (always returns English)
                url = f"https://zenquotes.io/api/random"
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data and isinstance(data, list):
                            q = data[0].get("q", "")
                            a = data[0].get("a", "")
                            return {"text": q, "author": a, "philosophy": keyword}
                # Fallback: API Ninjas (with keyword)
                url2 = f"https://api.api-ninjas.com/v1/quotes?category={keyword}"
                headers = {"X-Api-Key": "YOUR_API_KEY"}  # Replace with your API key
                async with session.get(url2, headers=headers) as resp2:
                    if resp2.status == 200:
                        data2 = await resp2.json()
                        if data2 and isinstance(data2, list):
                            q = data2[0].get("quote", "")
                            a = data2[0].get("author", "")
                            return {"text": q, "author": a, "philosophy": keyword}
        except Exception as e:
            logger.warning(f"Quote API failed: {e}")
        # Fallback: local English quote
        fallback_quotes = [
            {"text": "The only way to do great work is to love what you do.", "author": "Steve Jobs", "philosophy": "motivation"},
            {"text": "Knowledge is power.", "author": "Francis Bacon", "philosophy": "knowledge"},
            {"text": "To be yourself in a world that is constantly trying to make you something else is the greatest accomplishment.", "author": "Ralph Waldo Emerson", "philosophy": "self-improvement"},
            {"text": "The unexamined life is not worth living.", "author": "Socrates", "philosophy": "philosophy"},
            {"text": "Success is not final, failure is not fatal: It is the courage to continue that counts.", "author": "Winston Churchill", "philosophy": "resilience"},
        ]
        return random.choice(fallback_quotes)

    async def format_quote_dual_language(self, quote) -> str:
        """Format quote: "[EN]"\n"[AR]"\n[AUTHOR]. Only translate from English to Arabic. Always wrap quotes in double quotation marks. Adds a short disclaimer below the quote."""
        try:
            if isinstance(quote, dict):
                text = quote.get('text', '')
                author = quote.get('author', '')
            else:
                text = str(quote)
                author = ''
            if not text:
                return ''
            # Only translate if the text is English (basic check: contains a-z or A-Z)
            if any('a' <= c.lower() <= 'z' for c in text):
                translated = await translate_text(text, target_lang='ar')
                if translated.strip() and translated.strip() != text.strip():
                    quote_block = f'"{text}"\n"{translated}"' + (f'\n{author}' if author else '')
                else:
                    quote_block = f'"{text}"' + (f'\n{author}' if author else '')
            else:
                # Not English, just show the text and author, quoted
                quote_block = f'"{text}"' + (f'\n{author}' if author else '')
            disclaimer = "\n_اقتباس آلي من الإنترنت_"
            return f"{quote_block}{disclaimer}"
        except Exception as e:
            logger.warning(f"Quote translation failed: {e}")
            if isinstance(quote, dict):
                text = quote.get('text', '')
                author = quote.get('author', '')
                quote_block = f'"{text}"' + (f'\n{author}' if author else '')
                disclaimer = "\n_اقتباس آلي من الإنترنت_"
                return f"{quote_block}{disclaimer}"
            else:
                quote_block = f'"{quote}"'
                disclaimer = "\n_اقتباس آلي من الإنترنت_"
                return f"{quote_block}{disclaimer}"

    async def format_old_grades_with_analysis(
        self, telegram_id: int, old_grades: List[Dict[str, Any]]
    ) -> str:
        """Format old grades with analysis and dual-language quote"""
        try:
            quote = await self.get_daily_quote()
            # Calculate statistics
            total_courses = len(old_grades)
            completed_courses = sum(1 for grade in old_grades if grade.get("total"))
            avg_grade = self._calculate_average_grade(old_grades)
            has_numeric = any(
                isinstance(grade.get("total"), (int, float)) or (isinstance(grade.get("total"), str) and grade.get("total", "").replace(".", "", 1).isdigit())
                for grade in old_grades
            )
            avg_grade_str = (
                f"{avg_grade:.2f}%" if has_numeric and avg_grade > 0 else "لا يوجد درجات رقمية لحساب المتوسط"
            )
            # Format the message
            message = (
                f"📚 **درجات الفصل الدراسي الأول 2024/2025**\n\n"
                f"**إحصائيات عامة:**\n"
                f"• عدد المقررات: {total_courses}\n"
                f"• المقررات المكتملة: {completed_courses}\n"
                f"• متوسط الدرجات: {avg_grade_str}\n\n"
                f"**الدرجات التفصيلية:**\n"
            )
            for grade in old_grades:
                name = grade.get("name", "غير محدد")
                code = grade.get("code", "-")
                coursework = grade.get("coursework", "لم يتم النشر")
                final_exam = grade.get("final_exam", "لم يتم النشر")
                total = grade.get("total", "لم يتم النشر")
                message += f"📖 **{name}** ({code})\n   الأعمال: {coursework} | النظري: {final_exam} | النهائي: {total}\n\n"
            # Add dual-language quote if available, only once
            if quote:
                quote_text = await self.format_quote_dual_language(quote)
                if quote_text.strip() not in message:
                    message += quote_text
            return message
        except Exception as e:
            logger.error(f"Error formatting old grades: {e}")
            return "❌ حدث خطأ أثناء تحليل الدرجات السابقة."

    def _calculate_average_grade(self, grades: List[Dict[str, Any]]) -> float:
        """Calculate average grade from total grades."""
        try:
            total_grades = []
            for grade in grades:
                total = grade.get("total")
                if total and isinstance(total, (int, float)):
                    total_grades.append(float(total))
                elif total and isinstance(total, str):
                    try:
                        total_grades.append(float(total))
                    except ValueError:
                        continue

            if total_grades:
                return sum(total_grades) / len(total_grades)
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating average grade: {e}")
            return 0.0

    async def format_current_grades_with_quote(
        self, telegram_id: int, grades: List[Dict[str, Any]]
    ) -> str:
        """Format current term grades and append a dual-language quote."""
        try:
            quote = await self.get_daily_quote()
            total_courses = len(grades)
            completed_courses = sum(1 for grade in grades if grade.get("total"))
            avg_grade = self._calculate_average_grade(grades)
            has_numeric = any(
                isinstance(grade.get("total"), (int, float)) or (isinstance(grade.get("total"), str) and grade.get("total", "").replace(".", "", 1).isdigit())
                for grade in grades
            )
            avg_grade_str = (
                f"{avg_grade:.2f}%" if has_numeric and avg_grade > 0 else "لا يوجد درجات رقمية لحساب المتوسط"
            )
            message = (
                f"📚 **درجات الفصل الدراسي الثاني 2024/2025**\n\n"
                f"**إحصائيات عامة:**\n"
                f"• عدد المقررات: {total_courses}\n"
                f"• المقررات المكتملة: {completed_courses}\n"
                f"• متوسط الدرجات: {avg_grade_str}\n\n"
                f"**الدرجات التفصيلية:**\n"
            )
            for grade in grades:
                name = grade.get("name", "غير محدد")
                code = grade.get("code", "-")
                coursework = grade.get("coursework", "لم يتم النشر")
                final_exam = grade.get("final_exam", "لم يتم النشر")
                total = grade.get("total", "لم يتم النشر")
                message += f"📖 **{name}** ({code})\n   الأعمال: {coursework} | النظري: {final_exam} | النهائي: {total}\n\n"
            if quote:
                quote_text = await self.format_quote_dual_language(quote)
                if quote_text.strip() not in message:
                    message += f"\n{quote_text}"
            return message
        except Exception as e:
            logger.error(f"Error formatting current grades: {e}")
            return "❌ حدث خطأ أثناء تحليل الدرجات الحالية."
