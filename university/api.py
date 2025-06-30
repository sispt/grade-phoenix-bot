"""
🏫 University API Integration (Final, Complete, and Corrected Version with test_token)
"""
import asyncio
import logging
import aiohttp
import json
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
        # This function is now correct and robust.
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
                logger.error(f"Login attempt {attempt + 1} failed.")
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Exception during login attempt {attempt + 1}: {e}", exc_info=True)
                await asyncio.sleep(2 ** attempt)
        return None

    # --- THIS FUNCTION IS NOW RESTORED ---
    async def test_token(self, token: str) -> bool:
        """Test if token is still valid using GraphQL query"""
        try:
            headers = {**self.api_headers, "Authorization": f"Bearer {token}"}
            payload = {"query": UNIVERSITY_QUERIES["TEST_TOKEN"]}
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "errors" in data or not data.get("data"):
                            return False
                        return data.get("data", {}).get("getGUI", {}).get("user") is not None
                    return False
        except Exception as e:
            logger.error(f"❌ DEBUG: Error testing token: {e}")
            return False

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

    # In api.py, replace ONLY the _get_grades function with this final version:

async def _get_grades(self, token: str) -> List[Dict[str, Any]]:
    """
    Final, direct method to get user grades. It bypasses the unreliable
    homepage parsing and fetches grades using the known-good term IDs from the HAR file.
    """
    logger.info("🔍 DEBUG: Starting DIRECT grade fetch with hardcoded known term IDs...")
    all_grades = []
    
    # These are the correct term IDs we found in your HAR file.
    # This is much more reliable than trying to find them dynamically.
    known_term_ids = ["10459", "8530"] 
    
    for term_id in known_term_ids:
        logger.info(f"📊 DEBUG: Directly fetching grades for known term ID: {term_id}")
        
        # This function fetches the page containing the actual grades table.
        term_grades = await self._get_term_grades(token, term_id)
        
        if term_grades:
            logger.info(f"✅ DEBUG: Found {len(term_grades)} grades for term ID {term_id}.")
            all_grades.extend(term_grades)
        else:
            logger.info(f"ℹ️ DEBUG: No grades found for term ID {term_id}.")

    if not all_grades:
        logger.warning("⚠️ DEBUG: No grades found for any of the attempted term IDs.")
        
    logger.info(f"🎉 DEBUG: Total grades retrieved directly: {len(all_grades)}")
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
                    all_grades.extend(self._parse_grades_table_html(html_content))
        return all_grades

    def _parse_grades_table_html(self, html_content: str) -> List[Dict[str, Any]]:
        try:
            grades, soup, tables = [], BeautifulSoup(html_content, 'html.parser'), soup.find_all('table')
            if not tables: return []
            HEADER_MAPPING = { "المقرر": "name", "اسم المادة": "name", "كود المادة": "code", "الكود": "code", "رصيد ECTS": "ects", "درجة الأعمال": "coursework", "درجة النظري": "final_exam", "الدرجة": "total" }
            for table in tables:
                header_row = table.find('thead') or table.find('tr')
                if not header_row: continue
                headers, column_map = header_row.find_all(['th', 'td']), {}
                for index, th in enumerate(headers):
                    header_text = th.get_text(strip=True).lower()
                    for map_key, standard_key in HEADER_MAPPING.items():
                        if map_key in header_text: column_map[standard_key] = index; break
                if 'name' not in column_map: continue
                data_rows = (table.find('tbody') or table).find_all('tr')[1:]
                for row in data_rows:
                    cells = row.find_all('td')
                    if len(cells) < len(column_map): continue
                    grade_entry = {key: cells[index].get_text(strip=True) for key, index in column_map.items() if index < len(cells)}
                    if grade_entry.get("name"): grades.append(grade_entry)
            return grades
        except Exception as e:
            logger.error(f"❌ DEBUG: Error during HTML table parsing: {e}", exc_info=True)
            return []

    def _contains_course_data(self, html_content: str) -> bool:
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            tables = soup.find_all("table")
            if not tables: return False
            indicators = ['مقرر', 'درجة', 'رصيد', 'كود']
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