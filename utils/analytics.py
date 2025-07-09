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
import csv
from decimal import Decimal, ROUND_HALF_UP

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

    def get_quote_category_for_grades(self, grades: List[Dict[str, Any]]) -> list:
        """Determine the most relevant quote category based on grades (numeric, single-letter, or double-letter). Returns a list of categories. For low grades, use comforting/supportive categories."""
        if not grades:
            return ["beginning"]
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
                return ["excellence"]
            elif avg >= 75:
                return ["achievement"]
            elif avg >= 60:
                return ["growth"]
            elif avg < 60:
                # Comforting/supportive for low numeric grades
                return [
                    "resilience", "perseverance", "hope", "encouragement", "compassion", "self-improvement", "growth", "reflection", "meaningful life"
                ]
        # Letter grade logic
        if letter_grades:
            # Map letter grades to performance
            grade_order = [
                "A+", "A", "A-", "BA", "BB", "CB", "CC", "DC", "DD", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "AA", "FF", "F"
            ]
            best = min(letter_grades, key=lambda g: grade_order.index(g) if g in grade_order else 100)
            if best in ["A+", "A", "A-", "AA", "BA"]:
                return ["excellence"]
            elif best in ["B+", "B", "B-", "BB", "CB"]:
                return ["achievement"]
            elif best in ["C+", "C", "C-", "CC", "DC"]:
                return ["growth"]
            elif best in ["D+", "D", "D-", "DD", "FF", "F"]:
                # Comforting/supportive for low letter grades
                return [
                    "resilience", "perseverance", "hope", "encouragement", "compassion", "self-improvement", "growth", "reflection", "meaningful life"
                ]
            else:
                return ["learning"]
        return ["learning"]

    def get_quote_category_for_gpa(self, gpa: float) -> list:
        """Return a quote category based on GPA value. For low GPA, use comforting/supportive categories."""
        if gpa is None:
            return ["learning"]
        if gpa >= 3.5:
            return ["excellence"]
        elif gpa >= 3.0:
            return ["achievement"]
        elif gpa >= 2.0:
            return ["growth"]
        else:
            # For low GPA, use comforting/supportive categories
            return [
                "resilience", "perseverance", "hope", "encouragement", "compassion", "self-improvement", "growth", "reflection", "meaningful life"
            ]

    async def get_daily_quote(self, categories: list = None) -> dict:
        """Fetch a daily quote, trying all preferred and general keywords in order."""
        # Improved, high-quality keywords for better quotes
        general_keywords = [
            # Philosophy & Wisdom
            "philosophy", "wisdom", "stoicism", "existentialism", "ethics", "virtue", "meaning", "truth", "logic", "reason", "consciousness", "mindfulness",
            # Literature & Classics
            "literature", "poetry", "classics", "Shakespeare", "Socrates", "Plato", "Aristotle", "Seneca", "Marcus Aurelius", "Epictetus", "Nietzsche", "Kant", "Confucius", "Lao Tzu",
            # Science & Knowledge
            "science", "knowledge", "curiosity", "discovery", "innovation", "creativity", "learning", "education",
            # Human Potential & Character
            "character", "integrity", "resilience", "courage", "perseverance", "growth", "reflection", "purpose", "self-discipline", "self-improvement", "gratitude", "humility",
            # Psychology & Meaningful Life
            "psychology", "meaningful life", "happiness", "fulfillment", "compassion", "empathy", "altruism", "generosity"
        ]
        # Filter specified categories to only allow high-quality keywords
        allowed_keywords = set(general_keywords)
        if categories is None:
            categories = []
        elif isinstance(categories, str):
            categories = [categories]
        # Remove duplicates, preserve order, and filter for quality
        seen = set()
        filtered_categories = [k for k in categories if k in allowed_keywords and not (k in seen or seen.add(k))]
        all_keywords = filtered_categories + [k for k in general_keywords if k not in filtered_categories]
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

    async def format_quote_dual_language(self, quote, do_translate=True) -> str:
        """Format quote: "[EN]"\n"[AR]"\n[AUTHOR]. Only translate from English to Arabic if do_translate is True. Otherwise, return an empty string."""
        if not do_translate:
            return ""
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
            disclaimer = "\n_اقتباس آلي من الإنترنت_\n_قد ﻻ تكون الترجمة دقيقة_"
            return f"{quote_block}{disclaimer}"
        except Exception as e:
            logger.warning(f"Quote translation failed: {e}")
            if isinstance(quote, dict):
                text = quote.get('text', '')
                author = quote.get('author', '')
                quote_block = f'"{text}"' + (f'\n{author}' if author else '')
                disclaimer = "\n_اقتباس آلي من الإنترنت_\n_قد ﻻ تكون الترجمة دقيقة_"
                return f"{quote_block}{disclaimer}"
            else:
                quote_block = f'"{quote}"'
                disclaimer = "\n_اقتباس آلي من الإنترنت_\n_قد ﻻ تكون الترجمة دقيقة_"
                return f"{quote_block}{disclaimer}"

    async def format_old_grades_with_analysis(
        self, telegram_id: int, old_grades: List[Dict[str, Any]]
    ) -> str:
        """Format old grades with analysis and dual-language quote, using a relevant category."""
        import re
        try:
            # Get user's translation preference
            user = self.user_storage.get_user_by_telegram_id(telegram_id)
            do_translate = user.get("do_trans", False) if user else False
            
            category = self.get_quote_category_for_grades(old_grades)
            quote = await self.get_daily_quote(category)
            total_courses = len(old_grades)
            completed_courses = sum(1 for grade in old_grades if grade.get("total"))
            avg_grade = self._calculate_average_grade(old_grades)
            has_numeric = any(
                (isinstance(grade.get("total"), (int, float)) and grade.get("total") is not None) or
                (isinstance(grade.get("total"), str) and grade.get("total") is not None and isinstance(grade.get("total"), str) and re.search(r"\d+(?:\.\d+)?", grade.get("total")))
                for grade in old_grades
            )
            avg_grade_str = (
                f"{avg_grade:.2f}%" if has_numeric and avg_grade > 0 else "لا يوجد درجات رقمية لحساب المتوسط"
            )
            
            # Calculate GPA
            gpa = self._calculate_gpa(old_grades)
            gpa_str = f"{gpa:.2f}".rstrip('0').rstrip('.') if gpa is not None else "-"
            
            # Get the actual term name from the first grade (all grades should have the same term)
            term_name = "الفصل الدراسي السابق"  # fallback
            if old_grades and old_grades[0].get('term_name'):
                term_name = old_grades[0]['term_name']
            
            # Calculate completion status
            completion_status = f"{completed_courses}/{total_courses}"
            if completed_courses == 0:
                completion_text = "لا توجد مقررات مكتملة"
            elif completed_courses == total_courses:
                completion_text = f"جميع المقررات مكتملة ({completion_status})"
            else:
                completion_text = f"مقررات مكتملة: {completion_status}"
            
            # Build message
            message = (
                f"📚 **درجات {term_name}**\n\n"
                f"**إحصائيات عامة:**\n"
                f"• عدد المقررات: {total_courses}\n"
                f"• {completion_text}\n"
                f"• متوسط الدرجات: {avg_grade_str}\n"
                f"• المعدل التراكمي (GPA): {gpa_str}\n\n"
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
                quote_text = await self.format_quote_dual_language(quote, do_translate=do_translate)
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
        self, telegram_id: int, grades: List[Dict[str, Any]], manual: bool = False
    ) -> str:
        """Format current term grades and append a dual-language quote, using a relevant category. If manual=True, use GPA for category if available."""
        import re
        try:
            # Get user's translation preference
            user = self.user_storage.get_user_by_telegram_id(telegram_id)
            do_translate = user.get("do_trans", False) if user else False
            
            gpa = self._calculate_gpa(grades)
            if manual and gpa is not None:
                category = self.get_quote_category_for_gpa(gpa)
            else:
                category = self.get_quote_category_for_grades(grades)
            quote = await self.get_daily_quote(category)
            total_courses = len(grades)
            completed_courses = sum(1 for grade in grades if grade.get("total"))
            avg_grade = self._calculate_average_grade(grades)
            has_numeric = any(
                (isinstance(grade.get("total"), (int, float)) and grade.get("total") is not None) or
                (isinstance(grade.get("total"), str) and grade.get("total") is not None and isinstance(grade.get("total"), str) and re.search(r"\d+(?:\.\d+)?", grade.get("total")))
                for grade in grades
            )
            avg_grade_str = (
                f"{avg_grade:.2f}%" if has_numeric and avg_grade > 0 else "لا يوجد درجات رقمية لحساب المتوسط"
            )
            gpa_str = f"{gpa:.2f}".rstrip('0').rstrip('.') if gpa is not None else "-"
            term_name = "الفصل الدراسي الحالي"  # fallback
            if grades and grades[0].get('term_name'):
                term_name = grades[0]['term_name']
            completion_status = f"{completed_courses}/{total_courses}"
            if completed_courses == 0:
                completion_text = "لا توجد مقررات مكتملة"
            elif completed_courses == total_courses:
                completion_text = f"جميع المقررات مكتملة ({completion_status})"
            else:
                completion_text = f"مقررات مكتملة: {completion_status}"
            message = (
                f"📚 **درجات {term_name}**\n\n"
                f"**إحصائيات عامة:**\n"
                f"• عدد المقررات: {total_courses}\n"
                f"• {completion_text}\n"
                f"• متوسط الدرجات: {avg_grade_str}\n"
                f"• المعدل التراكمي (GPA): {gpa_str}\n\n"
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
                quote_text = await self.format_quote_dual_language(quote, do_translate=do_translate)
                if quote_text.strip() not in message:
                    message += f"\n{quote_text}"
            return message
        except Exception as e:
            logger.error(f"Error formatting current grades: {e}")
            return "❌ حدث خطأ أثناء تحليل الدرجات الحالية."

    def _load_percentage_to_ects(self) -> dict:
        """Load percentage to earned points mapping from credit.csv."""
        mapping = {}
        try:
            with open("storage/credit.csv", newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        percent = int(row['percentage'])
                        earned_points = float(row['earned_points'])
                        mapping[percent] = earned_points
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Invalid row in credit.csv: {row}, error: {e}")
                        continue
            logger.info(f"Loaded {len(mapping)} percentage-to-points mappings from credit.csv")
        except FileNotFoundError:
            logger.error("credit.csv not found, using default mapping")
            # Default mapping for percentages 30-100 (same as credit.csv)
            for percent in range(30, 101):
                if percent >= 90:
                    mapping[percent] = 3.57
                elif percent >= 85:
                    mapping[percent] = 3.35
                elif percent >= 80:
                    mapping[percent] = 3.14
                elif percent >= 75:
                    mapping[percent] = 2.92
                elif percent >= 70:
                    mapping[percent] = 2.71
                elif percent >= 65:
                    mapping[percent] = 2.5
                elif percent >= 60:
                    mapping[percent] = 2.28
                elif percent >= 55:
                    mapping[percent] = 2.07
                elif percent >= 50:
                    mapping[percent] = 1.85
                elif percent >= 45:
                    mapping[percent] = 1.64
                elif percent >= 40:
                    mapping[percent] = 1.38
                elif percent >= 35:
                    mapping[percent] = 1.17
                elif percent >= 30:
                    mapping[percent] = 0.0
                else:
                    mapping[percent] = 0.0
        except Exception as e:
            logger.error(f"Error loading credit mapping: {e}")
        return mapping

    def _calculate_gpa(self, grades: List[Dict[str, Any]]) -> Optional[float]:
        """Calculate GPA using the formula: sum(earned_ects × assigned_ects) / sum(assigned_ects)"""
        try:
            if not grades:
                return None
            
            # Load percentage to ECTS mapping
            percentage_to_ects = self._load_percentage_to_ects()
            
            total_weighted_points = 0.0
            total_assigned_ects = 0.0
            valid_courses = 0
            
            for grade in grades:
                if not grade:
                    continue
                
                # Get percentage and assigned ECTS
                total = grade.get('total')
                assigned_ects = grade.get('ects')
                
                if not total or not assigned_ects:
                    continue
                
                # Convert percentage to integer
                try:
                    if isinstance(total, str):
                        # Extract first number (integer or float) from the string
                        import re
                        match = re.search(r"\d+(?:\.\d+)?", total)
                        if not match:
                            continue
                        percentage = int(float(match.group(0)))
                    else:
                        percentage = int(total)
                except (ValueError, TypeError):
                    continue
                
                # Validate percentage range
                if not (0 <= percentage <= 100):
                    continue
                
                # Get earned ECTS from mapping (0 for percentages below 30)
                if percentage < 30:
                    earned_ects = 0.0
                else:
                    earned_ects = percentage_to_ects.get(percentage, 0.0)
                
                # Validate assigned ECTS
                try:
                    assigned_ects = float(assigned_ects)
                    if not (0.5 <= assigned_ects <= 20):
                        continue
                except (ValueError, TypeError):
                    continue
                
                # Calculate weighted points
                total_weighted_points += earned_ects * assigned_ects
                total_assigned_ects += assigned_ects
                valid_courses += 1
            
            # Calculate GPA
            if valid_courses > 0 and total_assigned_ects > 0:
                gpa = total_weighted_points / total_assigned_ects
                # Round to 3 decimal places
                return round(gpa, 3)
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating GPA: {e}")
            return None
