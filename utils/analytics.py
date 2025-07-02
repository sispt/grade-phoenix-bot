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

    async def get_daily_quote(self) -> Optional[Dict[str, str]]:
        """Get a daily quote from working APIs with philosophy categories"""
        # Try multiple working APIs in order of preference
        apis = [
            self._try_zenquotes_api,
            self._try_adviceslip_api,
            self._try_local_fallback,
        ]

        for api_func in apis:
            try:
                quote = await api_func()
                if quote:
                    return quote
            except Exception as e:
                logger.warning(f"API {api_func.__name__} failed: {e}")
                continue

        return None

    async def _try_zenquotes_api(self) -> Optional[Dict[str, str]]:
        """Try Zen Quotes API"""
        try:
            async with asyncio.timeout(5):
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: requests.get("https://zenquotes.io/api/random", timeout=5),
                )
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        quote_data = data[0]
                        return {
                            "text": quote_data.get("q", ""),
                            "author": quote_data.get("a", "Unknown"),
                            "philosophy": "wisdom",
                        }
        except Exception as e:
            logger.warning(f"Zen Quotes API failed: {e}")
        return None

    async def _try_adviceslip_api(self) -> Optional[Dict[str, str]]:
        """Try Advice Slip API"""
        try:
            async with asyncio.timeout(5):
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: requests.get(
                        "https://api.adviceslip.com/advice", timeout=5
                    ),
                )
                if response.status_code == 200:
                    data = response.json()
                    if data and "slip" in data:
                        return {
                            "text": data["slip"].get("advice", ""),
                            "author": "Life Wisdom",
                            "philosophy": "life",
                        }
        except Exception as e:
            logger.warning(f"Advice Slip API failed: {e}")
        return None

    async def _try_local_fallback(self) -> Optional[Dict[str, str]]:
        """Local fallback quotes with philosophy categories"""
        fallback_quotes = [
            {
                "text": "The only way to do great work is to love what you do.",
                "author": "Steve Jobs",
                "philosophy": "motivation",
            },
            {
                "text": "Success is not final, failure is not fatal: it is the courage to continue that counts.",
                "author": "Winston Churchill",
                "philosophy": "perseverance",
            },
            {
                "text": "The future belongs to those who believe in the beauty of their dreams.",
                "author": "Eleanor Roosevelt",
                "philosophy": "dreams",
            },
            {
                "text": "Education is the most powerful weapon which you can use to change the world.",
                "author": "Nelson Mandela",
                "philosophy": "education",
            },
            {
                "text": "The journey of a thousand miles begins with one step.",
                "author": "Lao Tzu",
                "philosophy": "wisdom",
            },
        ]
        return random.choice(fallback_quotes)

    async def format_old_grades_with_analysis(
        self, telegram_id: int, old_grades: List[Dict[str, Any]]
    ) -> str:
        """Format old grades with analysis and past-focused quotes"""
        try:
            # Get a past-focused quote
            quote = await self.get_daily_quote()

            # Calculate statistics
            total_courses = len(old_grades)
            completed_courses = sum(1 for grade in old_grades if grade.get("total"))
            avg_grade = self._calculate_average_grade(old_grades)

            # Format the message
            message = f"""📚 **درجات الفصل الدراسي الأول 2024/2025**

**إحصائيات عامة:**
• عدد المقررات: {total_courses}
• المقررات المكتملة: {completed_courses}
• متوسط الدرجات: {avg_grade:.2f}%

**الدرجات التفصيلية:**
"""

            for grade in old_grades:
                name = grade.get("name", "غير محدد")
                code = grade.get("code", "-")
                coursework = grade.get("coursework", "لم يتم النشر")
                final_exam = grade.get("final_exam", "لم يتم النشر")
                total = grade.get("total", "لم يتم النشر")

                message += f"📖 **{name}** ({code})\n"
                message += f"   الأعمال: {coursework} | النظري: {final_exam} | النهائي: {total}\n\n"

            # Add quote if available
            if quote:
                message += f"""💭 **حكمة اليوم:**
"{quote['text']}"
— {quote['author']}

"""

            message += (
                "🔍 *استخدم هذا التحليل لفهم أدائك السابق وتحسين مستقبلك الأكاديمي*"
            )

            return message

        except Exception as e:
            logger.error(f"Error formatting old grades: {e}")
            return "❌ حدث خطأ أثناء تحليل الدرجات السابقة."

    def _calculate_average_grade(self, grades: List[Dict[str, Any]]) -> float:
        """Calculate average grade from total grades"""
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
