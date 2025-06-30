"""
🏫 University API Integration (Final, Complete, and Corrected Version)
"""
import asyncio
import logging
import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup

from config import CONFIG, UNIVERSITY_QUERIES

logger = logging.getLogger(__name__)

class UniversityAPI:
    """University API integration"""
    
    def __init__(self):
        self.login_url = CONFIG["UNIVERSITY_LOGIN_URL"]
        self.api_url = CONFIG["UNIVERSITY_API_URL"]
        self.api_headers = CONFIG["API_HEADERS"]
        self.timeout = aiohttp.ClientTimeout(total=CONFIG.get("REQUEST_TIMEOUT_SECONDS", 30))
    
    async def login(self, username: str, password: str) -> Optional[str]:
        max_retries = CONFIG.get("MAX_RETRY_ATTEMPTS", 3)
        for attempt in range(max_retries):
            try:
                payload = {"operationName": "signinUser", "variables": {"username": username, "password": password}, "query": UNIVERSITY_QUERIES["LOGIN"]}
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(self.login_url, headers=self.api_headers, json=payload) as response:
                        response_text = await response.text()
                        if response.status == 200 and response_text.strip():
                            data = json.loads(response_text)
                            token = data.get("data", {}).get("login")
                            if token: return token
                logger.error(f"Login attempt {attempt + 1} failed with status {response.status if 'response' in locals() else 'N/A'}.")
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Exception during login attempt {attempt + 1}: {e}", exc_info=True)
                await asyncio.sleep(2 ** attempt)
        return None

    async def get_user_data(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            user_info = await self._get_user_info(token)
            if not user_info: return None
            grades = await self._get_grades(token)
            return {**user_info, "grades": grades}
        except Exception as e:
            logger.error(f"❌ DEBUG: Error getting user data: {e}", exc_info=True)
            return None

    async def _get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            headers = {**self.api_headers, "Authorization": f"Bearer {token}"}
            payload = {"query": UNIVERSITY_QUERIES["GET_USER_INFO"]}
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("data", {}).get("getGUI"):
                            return data["data"]["getGUI"]["user"]
                    return None
        except Exception as e:
            logger.error(f"Error getting user info: {e}", exc_info=True)
            return None

    async def _get_grades(self, token: str) -> List[Dict[str, Any]]:
        """
        Corrected method to get grades. It fetches the homepage, extracts the
        real term IDs, and then fetches the grades for each term.
        """
        logger.info("🔍 DEBUG: Starting grade fetch with correct logic...")
        all_grades = []
        
        homepage_data = await self._get_homepage(token)
        if not homepage_data:
            logger.error("❌ DEBUG: Failed to get homepage data to find term IDs.")
            return []
            
        term_ids = self._extract_terms_from_homepage(homepage_data)
        if not term_ids:
            logger.error("❌ DEBUG: Could not extract any term IDs from the homepage.")
            return []
            
        for term_id in term_ids:
            logger.info(f"📊 DEBUG: Fetching grades for extracted term ID: {term_id}")
            term_grades = await self._get_term_grades(token, term_id)
            if term_grades:
                logger.info(f"✅ DEBUG: Found {len(term_grades)} grades for term ID {term_id}.")
                all_grades.extend(term_grades)
                
        logger.info(f"🎉 DEBUG: Total grades retrieved: {len(all_grades)}")
        return all_grades

    async def _get_homepage(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            headers = {**self.api_headers, "Authorization": f"Bearer {token}"}
            payload = {"operationName": "getPage", "variables": {"name": "home", "params": []}, "query": UNIVERSITY_QUERIES["GET_HOMEPAGE"]}
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("data", {}).get("getPage"):
                            return data["data"]["getPage"]
                    return None
        except Exception as e:
            logger.error(f"❌ DEBUG: Error getting homepage: {e}", exc_info=True)
            return None

    def _extract_terms_from_homepage(self, homepage_data: Dict[str, Any]) -> List[str]:
        """
        Corrected version: Extracts term IDs directly from the homepage's JSON config object.
        """
        try:
            logger.info("🔍 DEBUG: Extracting term IDs directly from homepage JSON...")
            term_ids = []
            if not homepage_data or "panels" not in homepage_data: return []
            
            for panel in homepage_data.get("panels", []):
                for block in panel.get("blocks", []):
                    if block.get("name") == "home_tabs":
                        for tab_config in block.get("config", []):
                            if tab_config.get("name") == "tabs":
                                for tab in tab_config.get("array", []):
                                    for prop_array in tab.get("array", []):
                                        if prop_array.get("name") == "page_params":
                                            for param in prop_array.get("array", []):
                                                if param.get("name") == "t_grade_id":
                                                    term_ids.append(param.get("value"))
            
            logger.info(f"📚 DEBUG: Successfully extracted term IDs: {term_ids}")
            return term_ids
            
        except Exception as e:
            logger.error(f"❌ DEBUG: A critical error occurred while extracting term IDs from JSON: {e}", exc_info=True)
            return []

    async def _get_term_grades(self, token: str, t_grade_id: str) -> List[Dict[str, Any]]:
        try:
            headers = {**self.api_headers, "Authorization": f"Bearer {token}"}
            payload = {"operationName": "getPage", "variables": {"name": "test_student_tracks", "params": [{"name": "t_grade_id", "value": t_grade_id}]}, "query": UNIVERSITY_QUERIES["GET_GRADES"]}
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("data", {}).get("getPage"):
                            return self._parse_grades_from_graphql(data["data"]["getPage"])
                    return []
        except Exception as e:
            logger.error(f"❌ DEBUG: Error getting term grades: {e}", exc_info=True)
            return []
            
    def _parse_grades_from_graphql(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        all_grades = []
        if not page_data or "panels" not in page_data: return []
        for panel in page_data.get("panels", []):
            for block in panel.get("blocks", []):
                html_content = block.get('body', '')
                if html_content and self._contains_course_data(html_content):
                    parsed_grades = self._parse_grades_table_html(html_content)
                    if parsed_grades:
                        all_grades.extend(parsed_grades)
        return all_grades

    def _parse_grades_table_html(self, html_content: str) -> List[Dict[str, Any]]:
        try:
            grades = []
            soup = BeautifulSoup(html_content, 'html.parser')
            tables = soup.find_all('table')
            if not tables: return []
            HEADER_MAPPING = {
                "المقرر": "name", "اسم المادة": "name", "course": "name",
                "كود المادة": "code", "الكود": "code", "course code": "code",
                "رصيد ECTS": "ects", "الرصيد": "ects", "credit": "ects",
                "درجة الأعمال": "coursework", "الأعمال": "coursework",
                "درجة النظري": "final_exam", "النظري": "final_exam",
                "الدرجة": "total", "الدرجة النهائية": "total", "grade": "total",
            }
            for table in tables:
                header_row = table.find('thead') or table.find('tr')
                if not header_row: continue
                headers = header_row.find_all(['th', 'td'])
                column_map = {}
                for index, th in enumerate(headers):
                    header_text = th.get_text(strip=True).lower()
                    for map_key in HEADER_MAPPING:
                        if map_key in header_text:
                            column_map[HEADER_MAPPING[map_key]] = index
                            break
                if 'name' not in column_map: continue
                data_rows = (table.find('tbody') or table).find_all('tr')[1:]
                for row in data_rows:
                    cells = row.find_all('td')
                    if len(cells) < len(column_map): continue
                    grade_entry = {key: cells[index].get_text(strip=True) for key, index in column_map.items() if index < len(cells)}
                    if grade_entry.get("name"):
                        grades.append(grade_entry)
            return grades
        except Exception as e:
            logger.error(f"❌ DEBUG: Error during robust HTML table parsing: {e}", exc_info=True)
            return []

    def _contains_course_data(self, html_content: str) -> bool:
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            tables = soup.find_all("table")
            if not tables: return False
            indicators = ['مقرر', 'درجة', 'رصيد', 'كود', 'course', 'grade', 'credit', 'code']
            for table in tables:
                thead = table.find("thead")
                if not thead: continue
                headers = [th.get_text(strip=True).lower() for th in thead.find_all("th")]
                if sum(any(indicator in header for indicator in indicators) for header in headers) >= 2:
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking for course data: {e}", exc_info=True)
            return False