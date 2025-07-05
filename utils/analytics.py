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

    def get_quote_category_for_grades(self, grades: List[Dict[str, Any]]) -> str:
        """Determine the most relevant quote category based on grades (numeric, single-letter, or double-letter)."""
        if not grades:
            return "beginning"
        numeric_totals = []
        letter_grades = []
        for grade in grades:
            total = grade.get("total")
            if total is None or total == "" or total == "لم يتم النشر":
                continue
            # Try numeric
            try:
                numeric_totals.append(float(total))
                continue
            except Exception:
                pass
            # Check for single- and double-letter grades
            t = str(total).strip().upper()
            # Single-letter
            if t in ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F"]:
                letter_grades.append(t)
                continue
            # Double-letter (Turkish/European system)
            if t in ["AA", "BA", "BB", "CB", "CC", "DC", "DD", "FF"]:
                letter_grades.append(t)
                continue
        # Numeric logic
        if numeric_totals:
            avg = sum(numeric_totals) / len(numeric_totals)
            if avg >= 90:
                return "excellence"
            elif avg >= 75:
                return "achievement"
            elif avg >= 60:
                return "growth"
            else:
                return "perseverance"
        # Letter grade logic
        if letter_grades:
            # Map letter grades to performance
            grade_order = [
                "A+", "A", "A-", "BA", "BB", "CB", "CC", "DC", "DD", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "AA", "FF", "F"
            ]
            best = min(letter_grades, key=lambda g: grade_order.index(g) if g in grade_order else 100)
            if best in ["A+", "A", "A-", "AA", "BA"]:
                return "excellence"
            elif best in ["B+", "B", "B-", "BB", "CB"]:
                return "achievement"
            elif best in ["C+", "C", "C-", "CC", "DC"]:
                return "growth"
            elif best in ["D+", "D", "D-", "DD", "FF", "F"]:
                return "perseverance"
            else:
                return "learning"
        return "learning"

    async def get_daily_quote(self, categories: list = None) -> dict:
        """Fetch a daily quote, trying all preferred and general keywords in order."""
        general_keywords = [
            "philosophy", "wisdom", "motivation", "learning", "education", "progress", "growth", "Psychology", "Anthropology"
        ]
        # If categories is a string, convert to list
        if categories is None:
            categories = []
        elif isinstance(categories, str):
            categories = [categories]
        # Remove duplicates, preserve order
        seen = set()
        all_keywords = [k for k in categories if not (k in seen or seen.add(k))] + [k for k in general_keywords if k not in categories]
        # Try each keyword in order
        for keyword in all_keywords:
            try:
                async with aiohttp.ClientSession() as session:
                    # ZenQuotes API (English)
                    url = f"https://zenquotes.io/api/random"
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data and isinstance(data, list):
                                q = data[0].get("q", "")
                                a = data[0].get("a", "")
                                if q:
                                    return {"text": q, "author": a, "philosophy": keyword}
                    # API Ninjas fallback
                    url2 = f"https://api.api-ninjas.com/v1/quotes?category={keyword}"
                    headers = {"X-Api-Key": "YOUR_API_KEY"}  # Set your API key
                    async with session.get(url2, headers=headers) as resp2:
                        if resp2.status == 200:
                            data2 = await resp2.json()
                            if data2 and isinstance(data2, list):
                                q = data2[0].get("quote", "")
                                a = data2[0].get("author", "")
                                if q:
                                    return {"text": q, "author": a, "philosophy": keyword}
            except Exception as e:
                logger.warning(f"Quote API failed for keyword '{keyword}': {e}")
        # Use local fallback quote
        fallback_quotes = [
            {"text": "The only way to do great work is to love what you do.", "author": "Steve Jobs", "philosophy": "motivation"},
            {"text": "Knowledge is power.", "author": "Francis Bacon", "philosophy": "knowledge"},
            {"text": "To be yourself in a world that is constantly trying to make you something else is the greatest accomplishment.", "author": "Ralph Waldo Emerson", "philosophy": "self-improvement"},
            {"text": "The unexamined life is not worth living.", "author": "Socrates", "philosophy": "philosophy"},
            {"text": "Success is not final, failure is not fatal: It is the courage to continue that counts.", "author": "Winston Churchill", "philosophy": "resilience"},
        ]
        return random.choice(fallback_quotes)

    async def get_quote_for_grade(self, grade_value: str) -> dict:
        """Get a quote related to a specific grade value (for update notifications), always including general keywords."""
        t = str(grade_value).strip().upper()
        if t in ["A+", "A", "A-", "AA", "BA"]:
            categories = ["excellence", "achievement"]
        elif t in ["B+", "B", "B-", "BB", "CB"]:
            categories = ["achievement", "growth"]
        elif t in ["C+", "C", "C-", "CC", "DC"]:
            categories = ["growth", "perseverance"]
        elif t in ["D+", "D", "D-", "DD", "FF", "F"]:
            categories = ["perseverance"]
        else:
            categories = ["learning"]
        return await self.get_daily_quote(categories)

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
            # Only translate if text is English
            if any('a' <= c.lower() <= 'z' for c in text):
                translated = await translate_text(text, target_lang='ar')
                if translated.strip() and translated.strip() != text.strip():
                    quote_block = f'"{text}"\n"{translated}"' + (f'\n{author}' if author else '')
                else:
                    quote_block = f'"{text}"' + (f'\n{author}' if author else '')
            else:
                # If not English, just show as is
                quote_block = f'"{text}"' + (f'\n{author}' if author else '')
            disclaimer = "\n_اقتباس آلي من الإنترنت (مخصص لك)_"
            return f"{quote_block}{disclaimer}"
        except Exception as e:
            logger.warning(f"Quote translation failed: {e}")
            if isinstance(quote, dict):
                text = quote.get('text', '')
                author = quote.get('author', '')
                quote_block = f'"{text}"' + (f'\n{author}' if author else '')
                disclaimer = "\n_اقتباس آلي من الإنترنت (مخصص لك)_"
                return f"{quote_block}{disclaimer}"
            else:
                quote_block = f'"{quote}"'
                disclaimer = "\n_اقتباس آلي من الإنترنت (مخصص لك)_"
                return f"{quote_block}{disclaimer}"

    async def format_old_grades_with_analysis(
        self, telegram_id: int, old_grades: List[Dict[str, Any]]
    ) -> str:
        """Format old grades with analysis and dual-language quote, using a relevant category."""
        try:
            category = self.get_quote_category_for_grades(old_grades)
            quote = await self.get_daily_quote(category)
            # Calculate stats
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
            
            # Get the actual term name from the first grade (all grades should have the same term)
            term_name = "الفصل الدراسي السابق"  # fallback
            if old_grades and old_grades[0].get('term_name'):
                term_name = old_grades[0]['term_name']
            
            # Build message
            message = (
                f"📚 **درجات {term_name}**\n\n"
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
            # Add quote if available, only once
            if quote:
                quote_text = await self.format_quote_dual_language(quote)
                if quote_text.strip() not in message:
                    message += quote_text
            return message
        except Exception as e:
            logger.error(f"Error formatting old grades: {e}")
            return "❌ حدث خطأ أثناء تحليل الدرجات السابقة."

    def _calculate_average_grade(self, grades: List[Dict[str, Any]]) -> float:
        """
        Calculate the average grade from the 'total' field of each grade.
        - Extracts the first numeric value from each 'total' (e.g., '87 %', '94', etc.)
        - Skips grades with 'لم يتم النشر', empty, or non-numeric values
        - Ignores letter grades and other non-numeric formats
        Returns the average as a float, or 0.0 if no numeric grades found.
        """
        import re
        try:
            total_grades = []
            for grade in grades:
                total = grade.get("total")
                if not total or not isinstance(total, str):
                    continue
                if total.strip() == '' or total.strip() == 'لم يتم النشر':
                    continue
                # Extract first number (integer or float) from the string
                match = re.search(r"\d+(?:\.\d+)?", total)
                if match:
                    try:
                        total_grades.append(float(match.group(0)))
                    except Exception:
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
        """Format current term grades and append a dual-language quote, using a relevant category."""
        try:
            category = self.get_quote_category_for_grades(grades)
            quote = await self.get_daily_quote(category)
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
            
            # Get the actual term name from the first grade (all grades should have the same term)
            term_name = "الفصل الدراسي الحالي"  # fallback
            if grades and grades[0].get('term_name'):
                term_name = grades[0]['term_name']
            
            message = (
                f"📚 **درجات {term_name}**\n\n"
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
