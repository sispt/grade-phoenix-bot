"""
🏫 University API Integration (Corrected and Final Version)
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
        """Login to university system, now with robust empty response handling."""
        max_retries = CONFIG.get("MAX_RETRY_ATTEMPTS", 3)
        for attempt in range(max_retries):
            try:
                logger.info(f"DEBUG: Login attempt {attempt + 1}/{max_retries} for user {username}")
                if not username or not password:
                    logger.warning(f"DEBUG: Invalid credentials for user {username}")
                    return None
                
                payload = {
                    "operationName": "signinUser",
                    "variables": {"username": username, "password": password},
                    "query": UNIVERSITY_QUERIES["LOGIN"]
                }
                
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(self.login_url, headers=self.api_headers, json=payload) as response:
                        response_text = await response.text()
                        logger.info(f"DEBUG: Login response status: {response.status}")
                        
                        if response.status == 200:
                            if not response_text.strip():
                                logger.error(f"❌ Login failed for user {username}: Server returned status 200 but with an EMPTY response. This could be a server or network issue.")
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(2 ** attempt)
                                    continue
                                return None
                            
                            data = json.loads(response_text)
                            token = data.get("data", {}).get("login")
                            
                            if token:
                                logger.info(f"✅ Login successful for user: {username}")
                                return token
                            else:
                                logger.warning(f"❌ Login failed for user: {username} - no token in response. Errors: {data.get('errors')}")
                                return None
                        
                        else:
                            logger.error(f"❌ Login request failed with status: {response.status}. Response: {response_text[:500]}")
                            if response.status in [429, 500, 502, 503, 504] and attempt < max_retries - 1:
                                await asyncio.sleep(2 ** attempt)
                                continue
                            return None

            except json.JSONDecodeError as json_error:
                logger.error(f"❌ JSON Decode Error during login for {username}: {json_error}. Response text: {response_text[:500]}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
            except Exception as e:
                logger.error(f"❌ Unexpected error during login for user {username} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
            
        return None

    async def test_token(self, token: str) -> bool:
        """Test if token is still valid using GraphQL query"""
        try:
            headers = {**self.api_headers, "Authorization": f"Bearer {token}"}
            payload = {"query": UNIVERSITY_QUERIES["TEST_TOKEN"]}
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "errors" in data: return False
                        return "data" in data and data["data"].get("getGUI", {}).get("user") is not None
                    return False
        except Exception as e:
            logger.error(f"❌ DEBUG: Error testing token: {e}")
            return False

    async def get_user_data(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user data including grades"""
        try:
            user_info = await self._get_user_info(token)
            if not user_info: return None
            grades = await self._get_grades(token)
            return {**user_info, "grades": grades}
        except Exception as e:
            logger.error(f"❌ DEBUG: Error getting user data: {e}")
            return None

    async def _get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user information"""
        try:
            headers = {**self.api_headers, "Authorization": f"Bearer {token}"}
            payload = {"query": UNIVERSITY_QUERIES["GET_USER_INFO"]}
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "data" in data and data["data"].get("getGUI"):
                            user_data = data["data"]["getGUI"]["user"]
                            return {
                                "id": user_data.get("id"),
                                "firstname": user_data.get("firstname"),
                                "lastname": user_data.get("lastname"),
                                "fullname": user_data.get("fullname"),
                                "email": user_data.get("email"),
                                "username": user_data.get("username")
                            }
                    return None
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None

    async def _get_grades(self, token: str) -> List[Dict[str, Any]]:
        """Get user grades from GraphQL endpoint, using multiple strategies."""
        logger.info("🔍 DEBUG: Starting grade fetch with token...")
        homepage_data = await self._get_homepage(token)
        if not homepage_data: return []
        
        terms = self._extract_terms_from_homepage(homepage_data)
        all_grades = []
        for term in terms:
            logger.info(f"📊 DEBUG: Getting grades for term: {term}")
            term_grades = await self._get_term_grades(token, term)
            if term_grades:
                all_grades.extend(term_grades)
        
        logger.info(f"🎉 DEBUG: Total grades retrieved: {len(all_grades)}")
        return all_grades

    async def _get_homepage(self, token: str) -> Optional[Dict[str, Any]]:
        """Get homepage data to extract terms"""
        try:
            headers = {**self.api_headers, "Authorization": f"Bearer {token}"}
            payload = {"query": UNIVERSITY_QUERIES["GET_HOMEPAGE"], "variables": {"name": "homepage", "params": []}}
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "data" in data and data["data"].get("getPage"):
                            return data["data"]["getPage"]
                    return None
        except Exception as e:
            logger.error(f"❌ DEBUG: Error getting homepage: {e}")
            return None

    def _extract_terms_from_homepage(self, homepage_data: Dict[str, Any]) -> List[str]:
        """Extract available terms from homepage data"""
        try:
            terms = set()
            if not homepage_data or "panels" not in homepage_data: return ["1"]
            for panel in homepage_data.get("panels", []):
                for block in panel.get("blocks", []):
                    soup = BeautifulSoup(block.get("body", ""), 'html.parser')
                    for tab in soup.find_all(['button', 'a', 'div'], attrs={'data-id': True}):
                        terms.add(tab['data-id'])
            if not terms:
                logger.warning("⚠️ DEBUG: No terms found, using default '1'")
                return ["1"]
            logger.info(f"📚 DEBUG: Extracted terms: {list(terms)}")
            return list(terms)
        except Exception as e:
            logger.error(f"❌ DEBUG: Error extracting terms: {e}")
            return ["1"]

    async def _get_term_grades(self, token: str, t_grade_id: str) -> List[Dict[str, Any]]:
        """Get grades for a specific term from the 'getPage' GraphQL query"""
        try:
            headers = {**self.api_headers, "Authorization": f"Bearer {token}"}
            payload = {"query": UNIVERSITY_QUERIES["GET_GRADES"], "variables": {"name": "test_student_tracks", "params": [{"name": "t_grade_id", "value": t_grade_id}]}}
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if "data" in data and data["data"].get("getPage"):
                            return self._parse_grades_from_graphql(data["data"]["getPage"])
                    return []
        except Exception as e:
            logger.error(f"❌ DEBUG: Error getting term grades: {e}")
            return []
            
    def _parse_grades_from_graphql(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """More robustly parse grades from GraphQL page data by finding a valid grades table."""
        try:
            logger.info("🔍 DEBUG: Starting robust parsing of grades from GraphQL data")
            all_grades = []
            if not page_data or "panels" not in page_data:
                logger.warning("❌ DEBUG: No 'panels' found in GraphQL data.")
                return []
            for panel in page_data["panels"]:
                for block in panel.get("blocks", []):
                    html_content = block.get('body', '')
                    if html_content and self._contains_course_data(html_content):
                        logger.info("✅ DEBUG: Found a block that appears to contain course data. Parsing now.")
                        parsed_grades = self._parse_grades_table_html(html_content)
                        if parsed_grades:
                            logger.info(f"🎉 DEBUG: Parsed {len(parsed_grades)} grades from the block.")
                            all_grades.extend(parsed_grades)
            if not all_grades:
                logger.warning("⚠️ DEBUG: Could not find or parse any grades from the GraphQL response.")
            return all_grades
        except Exception as e:
            logger.error(f"❌ DEBUG: An unexpected error occurred in _parse_grades_from_graphql: {e}")
            return []

    def _parse_grades_table_html(self, html_content: str) -> List[Dict[str, Any]]:
        """A more robust and flexible parser for HTML tables containing grades."""
        try:
            logger.info("🔍 DEBUG: Starting robust HTML table parsing.")
            grades = []
            soup = BeautifulSoup(html_content, 'html.parser')
            tables = soup.find_all('table')
            if not tables: return []
            HEADER_MAPPING = {
                "المقرر": "name", "اسم المادة": "name", "course": "name", "subject": "name",
                "كود المادة": "code", "الكود": "code", "course code": "code",
                "رصيد ECTS": "ects", "الرصيد": "ects", "credit": "ects",
                "درجة الأعمال": "coursework", "الأعمال": "coursework", "activity": "coursework",
                "درجة النظري": "final_exam", "النظري": "final_exam", "theoretical": "final_exam",
                "الدرجة": "total", "الدرجة النهائية": "total", "grade": "total",
            }
            for table in tables:
                header_row = table.find('thead') or table.find('tr')
                if not header_row: continue
                headers = header_row.find_all(['th', 'td'])
                column_map = {}
                for index, th in enumerate(headers):
                    header_text = th.get_text(strip=True).lower()
                    for map_key, standard_key in HEADER_MAPPING.items():
                        if map_key in header_text:
                            column_map[standard_key] = index
                            break
                if 'name' not in column_map: continue
                data_rows = (table.find('tbody') or table).find_all('tr')
                if table.find('thead') or (data_rows and data_rows[0] == header_row):
                     data_rows = data_rows[1:]
                for row in data_rows:
                    cells = row.find_all('td')
                    if len(cells) < len(column_map): continue
                    grade_entry = {key: cells[index].get_text(strip=True) for key, index in column_map.items() if index < len(cells)}
                    if grade_entry.get("name"):
                        grades.append(grade_entry)
            logger.info(f"🎉 DEBUG: Robustly parsed {len(grades)} grades from HTML.")
            return grades
        except Exception as e:
            logger.error(f"❌ DEBUG: Error during robust HTML table parsing: {e}")
            return []

    def _contains_course_data(self, html_content: str) -> bool:
        """Check if HTML content contains course data by analyzing table headers."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            tables = soup.find_all("table")
            if not tables: return False
            course_indicators = ['مقرر', 'درجة', 'رصيد', 'كود', 'course', 'grade', 'credit', 'code']
            for table in tables:
                thead = table.find("thead")
                if not thead: continue
                headers = [th.get_text(strip=True).lower() for th in thead.find_all("th")]
                if sum(any(indicator in header for indicator in course_indicators) for header in headers) >= 2:
                    logger.info(f"✅ DEBUG: Table appears to contain course data with headers: {headers}")
                    return True
            return False
        except Exception as e:
            logger.error(f"Error checking for course data: {e}")
            return False