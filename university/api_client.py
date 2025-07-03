"""
University API Client Integration
"""

import asyncio
import logging
import aiohttp
import json
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
import os

from config import CONFIG, UNIVERSITY_QUERIES, PRINT_HTML_DEBUG

logger = logging.getLogger(__name__)

class UniversityAPI:
    """University API integration"""

    def __init__(self):
        self.login_url = CONFIG["UNIVERSITY_LOGIN_URL"]
        self.api_url = CONFIG["UNIVERSITY_API_URL"]
        self.api_headers = CONFIG["API_HEADERS"]
        self.timeout = aiohttp.ClientTimeout(
            total=CONFIG.get("REQUEST_TIMEOUT_SECONDS", 30)
        )

    async def login(self, username: str, password: str) -> Optional[str]:
        max_retries = CONFIG.get("MAX_RETRY_ATTEMPTS", 3)
        for attempt in range(max_retries):
            try:
                payload = {
                    "operationName": "signinUser",
                    "variables": {"username": username, "password": password},
                    "query": UNIVERSITY_QUERIES["LOGIN"],
                }
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(
                        self.login_url, headers=self.api_headers, json=payload
                    ) as response:
                        response_text = await response.text()
                        if response.status == 200 and response_text.strip():
                            data = json.loads(response_text)
                            token = data.get("data", {}).get("login")
                            if token:
                                return token
                logger.error(f"Login attempt {attempt + 1} failed.")
                await asyncio.sleep(2**attempt)
            except Exception as e:
                logger.error(
                    f"Exception during login attempt {attempt + 1}: {e}", exc_info=True
                )
                await asyncio.sleep(2**attempt)
        return None

    async def test_token(self, token: str) -> bool:
        try:
            headers = {**self.api_headers, "Authorization": f"Bearer {token}"}
            payload = {"query": UNIVERSITY_QUERIES["TEST_TOKEN"]}
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    self.api_url, headers=headers, json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return (
                            "data" in data
                            and data["data"].get("getGUI", {}).get("user") is not None
                        )
                    return False
        except Exception:
            return False

    async def get_user_data(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            user_info = await self._get_user_info(token)
            if not user_info:
                return None
            grades = await self._get_grades(token)
            return {**user_info, "grades": grades}
        except Exception as e:
            logger.error(f"Error getting user data: {e}", exc_info=True)
            return None

    async def _get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            headers = {**self.api_headers, "Authorization": f"Bearer {token}"}
            payload = {"query": UNIVERSITY_QUERIES["GET_USER_INFO"]}
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    self.api_url, headers=headers, json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("data", {}).get("getGUI"):
                            return data["data"]["getGUI"]["user"]
                    return None
        except Exception as e:
            logger.error(f"Error getting user info: {e}", exc_info=True)
            return None

    async def get_old_grades(self, token: str) -> Optional[List[Dict[str, Any]]]:
        """Get old grades using the old term ID, auto-detect if needed"""
        try:
            logger.info("🔍 Fetching old grades with term ID 8530...")
            old_grades = await self._get_term_grades(token, "8530", user_id=0)
            if old_grades:
                logger.info(f"✅ Found {len(old_grades)} old grades for term 8530")
                return old_grades
            # If empty, try to auto-detect previous term
            logger.warning("No old grades found for term 8530, trying to auto-detect previous term...")
            # Try known fallback term IDs (add more as needed)
            fallback_terms = ["10458", "10457", "10456"]
            for term_id in fallback_terms:
                logger.info(f"🔍 Trying fallback term ID: {term_id}")
                old_grades = await self._get_term_grades(token, term_id, user_id=0)
                if old_grades:
                    logger.info(f"✅ Found {len(old_grades)} old grades for term {term_id}")
                    return old_grades
            logger.error("No old grades found for any known term IDs.")
            return []
        except Exception as e:
            logger.error(f"Error getting old grades: {e}", exc_info=True)
            return None

    async def _get_grades(self, token: str) -> List[Dict[str, Any]]:
        logger.info("🔍 Starting direct grade fetch with known term IDs...")
        all_grades = []
        known_term_ids = ["10459"]  # 2nd term 2024-2025 (current)
        for term_id in known_term_ids:
            logger.info(f"📊 Fetching grades for term ID: {term_id}")
            term_grades = await self._get_term_grades(token, term_id, user_id=0)
            if term_grades:
                logger.info(f"✅ Found {len(term_grades)} grades for term ID {term_id}")
                all_grades.extend(term_grades)
        logger.info(f"🎉 Total grades retrieved: {len(all_grades)}")
        return all_grades

    async def fetch_and_parse_grades(self, token: str, user_id: int) -> list:
        """
        Fetch grades for a user, log all steps, and handle errors robustly.
        Returns a list of parsed grades or an empty list on error.
        """
        try:
            logger.info(f"[Grade Fetch] Starting grade fetch for user {user_id}")
            all_grades = []
            known_term_ids = ["10459"]  # Example: current term
            for term_id in known_term_ids:
                logger.info(f"[Grade Fetch] User {user_id} - Fetching grades for term ID: {term_id}")
                term_grades = await self._get_term_grades(token, term_id, user_id)
                if term_grades:
                    logger.info(f"[Grade Fetch] User {user_id} - Found {len(term_grades)} grades for term ID {term_id}")
                    all_grades.extend(term_grades)
            logger.info(f"[Grade Fetch] User {user_id} - Total grades retrieved: {len(all_grades)}")
            return all_grades
        except Exception as e:
            logger.error(f"[Grade Fetch] Error fetching grades for user {user_id}: {e}", exc_info=True)
            return []

    async def _get_term_grades(self, token: str, t_grade_id: str, user_id: int) -> list:
        try:
            headers = {**self.api_headers, "Authorization": f"Bearer {token}"}
            payload = {
                "operationName": "getPage",
                "variables": {
                    "name": "test_student_tracks",
                    "params": [{"name": "t_grade_id", "value": t_grade_id}],
                },
                "query": UNIVERSITY_QUERIES["GET_GRADES"],
            }
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    self.api_url, headers=headers, json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"[Grade Fetch] User {user_id} - Raw API response: {data}")
                        if data.get("data", {}).get("getPage"):
                            grades = self._parse_grades_from_graphql(
                                data["data"]["getPage"], user_id
                            )
                            logger.debug(f"[Grade Parse] User {user_id} - Parsed grades: {grades}")
                            return grades
                        else:
                            logger.warning(f"[Grade Fetch] User {user_id} - No 'getPage' in API response for term {t_grade_id}: {data}")
                            return []
                    else:
                        logger.error(f"[Grade Fetch] User {user_id} - API returned status {response.status} for term {t_grade_id}")
                        return []
        except Exception as e:
            logger.error(f"[Grade Fetch] Error getting term grades for user {user_id}, term {t_grade_id}: {e}", exc_info=True)
            return []

    def _parse_grades_from_graphql(self, page_data: dict, user_id: int) -> list:
        all_grades = []
        if not page_data or "panels" not in page_data:
            logger.warning(f"[Grade Parse] User {user_id} - No panels in page data.")
            return []
        for panel in page_data.get("panels", []):
            for block in panel.get("blocks", []):
                html_content = block.get("body", "")
                if html_content and self._contains_course_data(html_content):
                    if PRINT_HTML_DEBUG:
                        logger.debug(f"[Grade Parse] User {user_id} - Raw HTML content:\n{html_content}")
                    grades = self._parse_grades_table_html(html_content)
                    if PRINT_HTML_DEBUG:
                        logger.debug(f"[Grade Parse] User {user_id} - Parsed grades from HTML: {grades}")
                    all_grades.extend(grades)
        return all_grades

    def _parse_grades_table_html(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Improved parser: Extracts all real courses (code, name, coursework, final_exam, total) from the HTML using BeautifulSoup.
        Excludes summary/term rows (e.g., '2nd Term 2024-2025') and rows with no course code.
        """
        try:
            grades = []
            soup = BeautifulSoup(html_content, "html.parser")
            tables = soup.find_all("table")
            for table in tables:
                headers = [th.get_text(strip=True) for th in table.find_all("th")]
                # Look for course table by header
                if any("المقرر" in h or "Course" in h for h in headers):
                    rows = table.find_all("tr")[1:]  # skip header
                    for row in rows:
                        cells = row.find_all("td")
                        if len(cells) < 2:
                            continue
                        name = cells[0].get_text(strip=True)
                        code = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                        # Exclude summary/term rows and rows with no code
                        if not code or any(term in name for term in ["term", "الفصل", "الدورة", "semester", "quarter", "2nd Term", "1st Term", "الفصل الدراسي"]):
                            continue
                        course = {
                            "name": name,
                            "code": code,
                            "ects": cells[2].get_text(strip=True) if len(cells) > 2 else "",
                            "coursework": cells[3].get_text(strip=True) if len(cells) > 3 else "",
                            "final_exam": cells[4].get_text(strip=True) if len(cells) > 4 else "",
                            "total": cells[5].get_text(strip=True) if len(cells) > 5 else "",
                        }
                        grades.append(course)
            if not grades:
                logger.warning("No real courses found in HTML table.")
            return grades
        except Exception as e:
            logger.error(f"Error during HTML table parsing: {e}", exc_info=True)
            return []

    def _normalize_grade(self, grade: dict) -> dict:
        """
        Normalize grade dict for comparison: strip, lowercase, only relevant fields.
        """
        return {
            k: (v.strip().lower() if isinstance(v, str) else v)
            for k, v in grade.items()
            if k in ("code", "name", "coursework", "final_exam", "total")
        }

    def _normalize_grades_list(self, grades: list) -> list:
        """
        Normalize and sort grades list for reliable comparison.
        """
        return sorted([self._normalize_grade(g) for g in grades], key=lambda g: (g.get("code", ""), g.get("name", "")))

    def _contains_course_data(self, html_content: str) -> bool:
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            tables = soup.find_all("table")
            if not tables:
                return False
            indicators = ["مقرر", "درجة", "رصيد", "كود"]
            for table in tables:
                thead = table.find("thead")
                if not thead:
                    continue
                headers = [
                    th.get_text(strip=True).lower() for th in thead.find_all("th")
                ]
                if (
                    sum(
                        any(indicator in header for indicator in indicators)
                        for header in headers
                    )
                    >= 2
                ):
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking for course data: {e}", exc_info=True)
            return False
