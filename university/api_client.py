"""
University API Client Integration
"""

import asyncio
import logging
import aiohttp
import json
from typing import Dict, List, Optional, Any, Tuple
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
                logger.warning("❌ No user info returned")
                return None
            grades = await self.get_current_grades(token)
            logger.info(f"📊 get_current_grades result: {grades}")
            # Handle case where get_current_grades returns None (error) or empty list
            if grades is None:
                logger.warning("❌ get_current_grades returned None (error)")
                grades = []
            return {**user_info, "grades": grades}
        except Exception as e:
            logger.error(f"❌ Error getting user data: {e}", exc_info=True)
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

    async def get_homepage_data(self, token: str) -> Optional[Dict[str, Any]]:
        """Get homepage data to extract available terms and their IDs"""
        try:
            headers = {**self.api_headers, "Authorization": f"Bearer {token}"}
            payload = {
                "operationName": "getPage",
                "variables": {
                    "name": "homepage",
                    "params": []
                },
                "query": UNIVERSITY_QUERIES["GET_HOMEPAGE"]
            }
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    self.api_url, headers=headers, json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.debug(f"Homepage API response: {data}")
                        if data.get("data", {}).get("getPage"):
                            return data["data"]["getPage"]
                        else:
                            logger.error(f"No 'getPage' in response: {data}")
                    logger.error(f"Failed to get homepage data: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error getting homepage data: {e}", exc_info=True)
            return None

    def extract_terms_from_homepage(self, homepage_data: Dict[str, Any]) -> List[Tuple[str, str | None]]:
        """Extract term names and grade IDs from homepage data. If grade_id is missing, return None and print a warning."""
        terms = []
        
        try:
            panels = homepage_data.get("panels", [])
            
            for panel in panels:
                blocks = panel.get("blocks", [])
                
                for block in blocks:
                    if block.get("type") == "tabs":
                        config = block.get("config", [])
                        
                        for config_item in config:
                            if config_item.get("name") == "tabs":
                                tabs_array = config_item.get("array", [])
                                
                                # Loop through all tab items at the same level
                                for tab_item in tabs_array:
                                    child_array = tab_item.get("array", [])
                                    
                                    term_name = None
                                    grade_id = None
                                    
                                    # Extract from child array
                                    for child_item in child_array:
                                        if child_item.get("name") == "label":
                                            term_name = child_item.get("value")
                                        elif child_item.get("name") == "page_params":
                                            # Defensive: page_params may be null or missing array
                                            page_params = child_item.get("array")
                                            if page_params and isinstance(page_params, list):
                                                for param in page_params:
                                                    if param.get("name") == "t_grade_id":
                                                        grade_id = param.get("value")
                                                        break
                                            else:
                                                # page_params is null or not a list
                                                grade_id = None
                                    
                                    if term_name:
                                        if grade_id is None:
                                            print(f"⚠️  Warning: No t_grade_id found for term '{term_name}'")
                                        terms.append((term_name, grade_id))
                                
                                # Also check for nested childs in the same block
                                childs = block.get("childs", [])
                                for child in childs:
                                    if child.get("type") == "tabs":
                                        child_config = child.get("config", [])
                                        for child_config_item in child_config:
                                            if child_config_item.get("name") == "tabs":
                                                child_tabs_array = child_config_item.get("array", [])
                                                
                                                # Loop through all child tab items
                                                for child_tab_item in child_tabs_array:
                                                    child_tab_array = child_tab_item.get("array", [])
                                                    
                                                    term_name = None
                                                    grade_id = None
                                                    
                                                    # Extract from child tab array
                                                    for child_tab_child_item in child_tab_array:
                                                        if child_tab_child_item.get("name") == "label":
                                                            term_name = child_tab_child_item.get("value")
                                                        elif child_tab_child_item.get("name") == "page_params":
                                                            page_params = child_tab_child_item.get("array")
                                                            if page_params and isinstance(page_params, list):
                                                                for param in page_params:
                                                                    if param.get("name") == "t_grade_id":
                                                                        grade_id = param.get("value")
                                                                        break
                                                            else:
                                                                grade_id = None
                                                    
                                                    if term_name:
                                                        if grade_id is None:
                                                            print(f"⚠️  Warning: No t_grade_id found for nested term '{term_name}'")
                                                        terms.append((term_name, grade_id))
                                break
                        break
        
        except Exception as e:
            print(f"Error extracting terms from homepage: {e}")
        
        return terms

    async def get_old_grades(self, token: str) -> Optional[List[Dict[str, Any]]]:
        """Get old grades using the second term from homepage (previous term)"""
        try:
            logger.info("🔍 Fetching old grades (previous term)...")
            
            # Get homepage data to extract available terms
            homepage_data = await self.get_homepage_data(token)
            if homepage_data:
                terms = self.extract_terms_from_homepage(homepage_data)
                if len(terms) > 1:
                    # Use the second term as the previous term
                    previous_term_name, previous_term_id = terms[1]
                    logger.info(f"📊 Using second term as previous: '{previous_term_name}' (ID: {previous_term_id})")
                    
                    if previous_term_id:
                        old_grades = await self._get_term_grades(token, previous_term_id, user_id=0)
                        if old_grades:
                            logger.info(f"✅ Found {len(old_grades)} old grades for term '{previous_term_name}'")
                            # Add term information to each grade
                            for grade in old_grades:
                                grade['term_name'] = previous_term_name
                                grade['term_id'] = previous_term_id
                            return old_grades
            
            # Fallback: Try known previous term IDs
            logger.info("🔄 Trying known previous term IDs...")
            previous_term_ids = ["10458", "10457", "10456"]  # Known previous terms
            for term_id in previous_term_ids:
                logger.info(f"🔍 Trying previous term ID: {term_id}")
                old_grades = await self._get_term_grades(token, term_id, user_id=0)
                if old_grades:
                    logger.info(f"✅ Found {len(old_grades)} old grades for term ID {term_id}")
                    # Add term information to each grade
                    for grade in old_grades:
                        grade['term_name'] = f"Previous Term ({term_id})"
                        grade['term_id'] = term_id
                    return old_grades
            
            logger.warning("No old grades found with any approach")
            return []
            
        except Exception as e:
            logger.error(f"Error getting old grades: {e}", exc_info=True)
            return None

    async def _get_grades(self, token: str) -> List[Dict[str, Any]]:
        """Get grades using dynamic term IDs from homepage extraction"""
        logger.info("🔍 Starting dynamic grade fetch with term extraction...")
        
        try:
            # First, get homepage data to extract available terms
            homepage_data = await self.get_homepage_data(token)
            if not homepage_data:
                logger.error("Failed to get homepage data for term extraction")
                return []
            
            # Extract terms and their grade IDs
            terms = self.extract_terms_from_homepage(homepage_data)
            if not terms:
                logger.error("No terms found in homepage data")
                return []
            
            logger.info(f"Found {len(terms)} terms: {[term[0] for term in terms]}")
            
            all_grades = []
            for term_name, grade_id in terms:
                if grade_id is None:
                    logger.warning(f"Skipping term '{term_name}' (no grade ID)")
                    continue
                
                logger.info(f"📊 Fetching grades for term '{term_name}' (ID: {grade_id})")
                term_grades = await self._get_term_grades(token, grade_id, user_id=0)
                if term_grades:
                    logger.info(f"✅ Found {len(term_grades)} grades for term '{term_name}'")
                    # Add term information to each grade
                    for grade in term_grades:
                        grade['term_name'] = term_name
                        grade['term_id'] = grade_id
                    all_grades.extend(term_grades)
                else:
                    logger.warning(f"No grades found for term '{term_name}'")
            
            logger.info(f"🎉 Total grades retrieved: {len(all_grades)}")
            return all_grades
            
        except Exception as e:
            logger.error(f"Error getting grades: {e}", exc_info=True)
            return []

    async def fetch_and_parse_grades(self, token: str, user_id: int) -> list:
        """
        Fetch current grades for a user using the current grades method.
        Returns a list of parsed grades or an empty list on error.
        """
        try:
            logger.info(f"[Grade Fetch] Starting current grade fetch for user {user_id}")
            
            current_grades = await self.get_current_grades(token)
            if current_grades is None:
                logger.error(f"[Grade Fetch] User {user_id} - Error getting current grades")
                return []
            
            logger.info(f"[Grade Fetch] User {user_id} - Found {len(current_grades)} current grades")
            return current_grades
            
        except Exception as e:
            logger.error(f"[Grade Fetch] Error fetching current grades for user {user_id}: {e}", exc_info=True)
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
        """Parse grades using the order-based method - processes blocks in order"""
        all_grades = []
        if not page_data or "panels" not in page_data:
            logger.warning(f"[Grade Parse] User {user_id} - No panels in page data.")
            return []
        
        try:
            # Get the blocks in order from the first panel
            panels = page_data.get("panels", [])
            if not panels:
                logger.warning(f"[Grade Parse] User {user_id} - No panels found.")
                return []
            
            blocks = panels[0].get("blocks", [])
            logger.info(f"[Grade Parse] User {user_id} - Processing {len(blocks)} blocks in order")
            
            for block_idx, block in enumerate(blocks):
                html_content = block.get("body", "")
                if not html_content:
                    continue
                
                logger.debug(f"[Grade Parse] User {user_id} - Processing block {block_idx + 1}: {block.get('title', 'No Title')}")
                
                # Parse grades from this block using the order-based method
                block_grades = self._parse_grades_from_block_html(html_content, block_idx + 1, user_id)
                all_grades.extend(block_grades)
                
                logger.info(f"[Grade Parse] User {user_id} - Block {block_idx + 1}: Found {len(block_grades)} courses")
            
            logger.info(f"[Grade Parse] User {user_id} - Total courses found: {len(all_grades)}")
            return all_grades
            
        except Exception as e:
            logger.error(f"[Grade Parse] User {user_id} - Error parsing grades: {e}", exc_info=True)
            return []

    def _parse_grades_from_block_html(self, html_content: str, block_num: int, user_id: int) -> List[Dict[str, Any]]:
        """Parse grades from a single block's HTML using the order-based method"""
        try:
            grades = []
            soup = BeautifulSoup(html_content, "html.parser")
            tables = soup.find_all("table")
            
            if not tables:
                return []
            
            for table_idx, table in enumerate(tables):
                logger.debug(f"[Grade Parse] User {user_id} - Block {block_num}, Table {table_idx + 1}")
                
                # Extract headers
                headers = [th.get_text(strip=True) for th in table.find_all("th")]
                
                # Extract ALL rows (no limit)
                rows = table.find_all("tr")[1:]  # Skip header row
                
                if not rows:
                    continue
                
                # Process each row as a course - NO LIMIT on number of courses
                for row_idx, row in enumerate(rows):
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    
                    # Filter: Only process rows with a non-empty course code (usually column 2)
                    if len(cells) < 2 or not cells[1].strip():
                        continue
                    
                    # Skip summary/statistics rows (numeric code + term name)
                    code = cells[1].strip()
                    name = cells[0].strip()
                    if code.isdigit() and "term" in name.lower():
                        continue
                    
                    # Process ANY number of cells - don't assume 6 columns
                    if len(cells) > 0:
                        course_data = {
                            'block': block_num,
                            'table': table_idx + 1,
                            'row': row_idx + 1,
                            'raw_cells': cells,  # Keep all raw data
                            'num_columns': len(cells)
                        }
                        
                        # Map cells to known fields if available
                        if len(cells) >= 1:
                            course_data['name'] = cells[0]
                        if len(cells) >= 2:
                            course_data['code'] = cells[1]
                        if len(cells) >= 3:
                            course_data['ects'] = cells[2]
                        if len(cells) >= 4:
                            course_data['coursework'] = cells[3]
                        if len(cells) >= 5:
                            course_data['final_exam'] = cells[4]
                        if len(cells) >= 6:
                            course_data['total'] = cells[5]
                        else:
                            course_data['total'] = ""
                        
                        # Add grade status
                        course_data['grade_status'] = self._get_grade_status(course_data.get('total', ''))
                        
                        grades.append(course_data)
                        
                        logger.debug(f"[Grade Parse] User {user_id} - Course: {course_data.get('code', 'N/A')} - {course_data.get('name', 'N/A')}")
            
            return grades
            
        except Exception as e:
            logger.error(f"[Grade Parse] User {user_id} - Error parsing block {block_num}: {e}", exc_info=True)
            return []

    def _get_grade_status(self, grade_text: str) -> str:
        """Determine grade status"""
        if not grade_text or grade_text.strip() == '':
            return "Not Published"
        if 'لم يتم النشر' in grade_text:
            return "Not Published"
        if '%' in grade_text:
            return "Published"
        return "Unknown"

    def _extract_numeric_grade(self, grade_text: str) -> int | None:
        """Extract numeric grade from text like '87 %' or 'لم يتم النشر'"""
        import re
        if not grade_text or grade_text.strip() == '' or 'لم يتم النشر' in grade_text:
            return None
        # Extract numbers from text like "87 %"
        numbers = re.findall(r'\d+', grade_text)
        return int(numbers[0]) if numbers else None

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

    async def get_current_grades(self, token: str) -> Optional[List[Dict[str, Any]]]:
        """Get current grades with multiple fallback approaches"""
        try:
            logger.info("🔍 Fetching current grades with multiple approaches...")
            
            # Approach 1: Try to get homepage data and extract current term
            logger.info("📊 Approach 1: Getting homepage data...")
            homepage_data = await self.get_homepage_data(token)
            logger.info(f"📊 Homepage data result: {homepage_data is not None}")
            
            if homepage_data:
                terms = self.extract_terms_from_homepage(homepage_data)
                logger.info(f"📊 Extracted terms: {len(terms)} terms found")
                for i, (term_name, term_id) in enumerate(terms):
                    logger.info(f"  Term {i+1}: '{term_name}' (ID: {term_id})")
                
                if terms:
                    # Try the first term (usually the current one)
                    current_term_name, current_term_id = terms[0]
                    logger.info(f"📊 Trying first term as current: '{current_term_name}' (ID: {current_term_id})")
                    
                    if current_term_id:
                        current_grades = await self._get_term_grades(token, current_term_id, user_id=0)
                        logger.info(f"📊 First term grades result: {len(current_grades) if current_grades else 0}")
                        if current_grades:
                            logger.info(f"✅ Found {len(current_grades)} current grades for term '{current_term_name}'")
                            # Add term information to each grade
                            for grade in current_grades:
                                grade['term_name'] = current_term_name
                                grade['term_id'] = current_term_id
                            return current_grades
            
            # Approach 2: Try known current term IDs
            logger.info("🔄 Approach 2: Trying known current term IDs...")
            current_term_ids = ["10459", "10460", "10461"]  # Add more as needed
            for term_id in current_term_ids:
                logger.info(f"🔍 Trying current term ID: {term_id}")
                current_grades = await self._get_term_grades(token, term_id, user_id=0)
                logger.info(f"📊 Term {term_id} grades result: {len(current_grades) if current_grades else 0}")
                if current_grades:
                    logger.info(f"✅ Found {len(current_grades)} current grades for term ID {term_id}")
                    # Add term information to each grade
                    for grade in current_grades:
                        grade['term_name'] = f"Current Term ({term_id})"
                        grade['term_id'] = term_id
                    return current_grades
            
            # Approach 3: Try the most recent term from all available terms
            if homepage_data:
                terms = self.extract_terms_from_homepage(homepage_data)
                if len(terms) > 1:
                    # Try the second term (might be more current)
                    current_term_name, current_term_id = terms[1]
                    logger.info(f"📊 Approach 3: Trying second term as current: '{current_term_name}' (ID: {current_term_id})")
                    
                    if current_term_id:
                        current_grades = await self._get_term_grades(token, current_term_id, user_id=0)
                        logger.info(f"📊 Second term grades result: {len(current_grades) if current_grades else 0}")
                        if current_grades:
                            logger.info(f"✅ Found {len(current_grades)} current grades for term '{current_term_name}'")
                            # Add term information to each grade
                            for grade in current_grades:
                                grade['term_name'] = current_term_name
                                grade['term_id'] = current_term_id
                            return current_grades
            
            logger.warning("❌ No current grades found with any approach")
            return []
            
        except Exception as e:
            logger.error(f"❌ Error getting current grades: {e}", exc_info=True)
            return None
