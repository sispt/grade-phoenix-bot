"""
🎓 University API Client V2 - Clean Implementation
Handles authentication and grade fetching for university students
"""

import aiohttp
import logging
from typing import Dict, List, Any, Optional, Tuple
from bs4 import BeautifulSoup
import re

from config import CONFIG, UNIVERSITY_QUERIES

logger = logging.getLogger(__name__)


class UniversityAPIV2:
    """Clean University API Client for grade fetching"""

    def __init__(self):
        self.api_url = CONFIG["UNIVERSITY_API_URL"]
        self.login_url = CONFIG["UNIVERSITY_LOGIN_URL"]
        self.api_headers = CONFIG["API_HEADERS"]
        self.timeout = aiohttp.ClientTimeout(total=30)

    async def login(self, username: str, password: str) -> Optional[str]:
        """Login to university system and return token"""
        try:
            logger.info(f"🔐 Attempting login for user: {username}")
            
            headers = {**self.api_headers}
            payload = {
                "operationName": "signinUser",
                "variables": {
                    "username": username,
                    "password": password
                },
                "query": UNIVERSITY_QUERIES["LOGIN"]
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    self.login_url, headers=headers, json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("data", {}).get("login"):
                            token = data["data"]["login"]
                            logger.info(f"✅ Login successful for user: {username}")
                            return token
                        else:
                            logger.warning(f"❌ Login failed - no token in response for user: {username}")
                            logger.debug(f"Response data: {data}")
                            return None
                    else:
                        logger.error(f"❌ Login failed with status {response.status} for user: {username}")
                        return None
        except Exception as e:
            logger.error(f"❌ Login error for user {username}: {e}", exc_info=True)
            return None

    async def test_token(self, token: str) -> bool:
        """Test if token is valid"""
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

    async def get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user information from API"""
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
            logger.error(f"❌ Error getting user info: {e}", exc_info=True)
            return None

    async def get_homepage_data(self, token: str) -> Optional[Dict[str, Any]]:
        """Get homepage data to extract available terms"""
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
                        if data.get("data", {}).get("getPage"):
                            return data["data"]["getPage"]
                    return None
        except Exception as e:
            logger.error(f"❌ Error getting homepage data: {e}", exc_info=True)
            return None

    def extract_terms_from_homepage(self, homepage_data: Dict[str, Any]) -> List[Tuple[str, str]]:
        """Extract term names and IDs from homepage data"""
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
                                
                                for tab_item in tabs_array:
                                    child_array = tab_item.get("array", [])
                                    
                                    term_name = None
                                    grade_id = None
                                    
                                    for child_item in child_array:
                                        if child_item.get("name") == "label":
                                            term_name = child_item.get("value")
                                        elif child_item.get("name") == "page_params":
                                            page_params = child_item.get("array")
                                            if page_params and isinstance(page_params, list):
                                                for param in page_params:
                                                    if param.get("name") == "t_grade_id":
                                                        grade_id = param.get("value")
                                                        break
                                    
                                    if term_name and grade_id:
                                        terms.append((term_name, grade_id))
                                        logger.info(f"📊 Found term: '{term_name}' (ID: {grade_id})")
        
        except Exception as e:
            logger.error(f"❌ Error extracting terms: {e}", exc_info=True)
        
        return terms

    async def get_term_grades(self, token: str, term_id: str) -> List[Dict[str, Any]]:
        """Get grades for a specific term"""
        try:
            headers = {**self.api_headers, "Authorization": f"Bearer {token}"}
            payload = {
                "operationName": "getPage",
                "variables": {
                    "name": "test_student_tracks",
                    "params": [{"name": "t_grade_id", "value": term_id}],
                },
                "query": UNIVERSITY_QUERIES["GET_GRADES"],
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    self.api_url, headers=headers, json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("data", {}).get("getPage"):
                            return self.parse_grades_from_response(data["data"]["getPage"])
                    return []
        except Exception as e:
            logger.error(f"❌ Error getting term grades for term {term_id}: {e}", exc_info=True)
            return []

    def parse_grades_from_response(self, page_data: dict) -> List[Dict[str, Any]]:
        """Parse grades from API response"""
        grades = []
        
        try:
            panels = page_data.get("panels", [])
            if not panels:
                return grades
            
            blocks = panels[0].get("blocks", [])
            
            for block_idx, block in enumerate(blocks):
                html_content = block.get("body", "")
                if not html_content:
                    continue
                
                block_grades = self.parse_grades_from_html(html_content, block_idx + 1)
                grades.extend(block_grades)
                
                logger.info(f"📊 Block {block_idx + 1}: Found {len(block_grades)} courses")
            
            logger.info(f"🎉 Total courses found: {len(grades)}")
            return grades
            
        except Exception as e:
            logger.error(f"❌ Error parsing grades: {e}", exc_info=True)
            return []

    def parse_grades_from_html(self, html_content: str, block_num: int) -> List[Dict[str, Any]]:
        """Parse grades from HTML content"""
        grades = []
        
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            tables = soup.find_all("table")
            
            for table_idx, table in enumerate(tables):
                rows = table.find_all("tr")[1:]  # Skip header row
                
                for row_idx, row in enumerate(rows):
                    cells = [td.get_text(strip=True) for td in row.find_all("td")]
                    
                    # Skip rows without course code
                    if len(cells) < 2 or not cells[1].strip():
                        continue
                    
                    # Skip summary rows
                    code = cells[1].strip()
                    name = cells[0].strip()
                    if code.isdigit() and "term" in name.lower():
                        continue
                    
                    # Create grade object
                    grade = {
                        'block': block_num,
                        'table': table_idx + 1,
                        'row': row_idx + 1,
                        'name': cells[0] if len(cells) > 0 else '',
                        'code': cells[1] if len(cells) > 1 else '',
                        'ects': cells[2] if len(cells) > 2 else '',
                        'coursework': cells[3] if len(cells) > 3 else '',
                        'final_exam': cells[4] if len(cells) > 4 else '',
                        'total': cells[5] if len(cells) > 5 else '',
                        'grade_status': self.get_grade_status(cells[5] if len(cells) > 5 else '')
                    }
                    
                    grades.append(grade)
        
        except Exception as e:
            logger.error(f"❌ Error parsing HTML for block {block_num}: {e}", exc_info=True)
        
        return grades

    def get_grade_status(self, grade_text: str) -> str:
        """Determine grade status"""
        if not grade_text or grade_text.strip() == '':
            return "Not Published"
        if 'لم يتم النشر' in grade_text:
            return "Not Published"
        if '%' in grade_text:
            return "Published"
        return "Unknown"

    async def get_current_grades(self, token: str) -> List[Dict[str, Any]]:
        """Get current term grades"""
        try:
            logger.info("🔍 Fetching current grades...")
            
            # Get homepage data to find terms
            homepage_data = await self.get_homepage_data(token)
            if not homepage_data:
                logger.warning("❌ No homepage data available")
                return []
            
            # Extract terms
            terms = self.extract_terms_from_homepage(homepage_data)
            if not terms:
                logger.warning("❌ No terms found in homepage")
                return []
            
            logger.info(f"📊 Found {len(terms)} terms: {[term[0] for term in terms]}")
            
            # Try first term (usually current)
            if terms:
                current_term_name, current_term_id = terms[0]
                logger.info(f"📊 Trying current term: '{current_term_name}' (ID: {current_term_id})")
                
                grades = await self.get_term_grades(token, current_term_id)
                if grades:
                    logger.info(f"✅ Found {len(grades)} current grades")
                    # Add term info to grades
                    for grade in grades:
                        grade['term_name'] = current_term_name
                        grade['term_id'] = current_term_id
                    return grades
            
            # Fallback: try known current term IDs
            logger.info("🔄 Trying fallback term IDs...")
            fallback_ids = ["10459", "10460", "10461"]
            for term_id in fallback_ids:
                logger.info(f"🔍 Trying term ID: {term_id}")
                grades = await self.get_term_grades(token, term_id)
                if grades:
                    logger.info(f"✅ Found {len(grades)} grades for term {term_id}")
                    for grade in grades:
                        grade['term_name'] = f"Current Term ({term_id})"
                        grade['term_id'] = term_id
                    return grades
            
            logger.warning("❌ No current grades found")
            return []
            
        except Exception as e:
            logger.error(f"❌ Error getting current grades: {e}", exc_info=True)
            return []

    async def get_old_grades(self, token: str) -> List[Dict[str, Any]]:
        """Get previous term grades"""
        try:
            logger.info("🔍 Fetching old grades...")
            
            # Get homepage data to find terms
            homepage_data = await self.get_homepage_data(token)
            if not homepage_data:
                logger.warning("❌ No homepage data available")
                return []
            
            # Extract terms
            terms = self.extract_terms_from_homepage(homepage_data)
            if len(terms) < 2:
                logger.warning("❌ Not enough terms found for old grades")
                return []
            
            # Use second term (usually previous)
            previous_term_name, previous_term_id = terms[1]
            logger.info(f"📊 Using previous term: '{previous_term_name}' (ID: {previous_term_id})")
            
            grades = await self.get_term_grades(token, previous_term_id)
            if grades:
                logger.info(f"✅ Found {len(grades)} old grades")
                # Add term info to grades
                for grade in grades:
                    grade['term_name'] = previous_term_name
                    grade['term_id'] = previous_term_id
                return grades
            
            # Fallback: try known previous term IDs
            logger.info("🔄 Trying fallback previous term IDs...")
            fallback_ids = ["10458", "10457", "10456"]
            for term_id in fallback_ids:
                logger.info(f"🔍 Trying previous term ID: {term_id}")
                grades = await self.get_term_grades(token, term_id)
                if grades:
                    logger.info(f"✅ Found {len(grades)} old grades for term {term_id}")
                    for grade in grades:
                        grade['term_name'] = f"Previous Term ({term_id})"
                        grade['term_id'] = term_id
                    return grades
            
            logger.warning("❌ No old grades found")
            return []
            
        except Exception as e:
            logger.error(f"❌ Error getting old grades: {e}", exc_info=True)
            return []

    async def get_user_data(self, token: str) -> Optional[Dict[str, Any]]:
        """Get complete user data including grades"""
        try:
            # Get user info
            user_info = await self.get_user_info(token)
            if not user_info:
                logger.warning("❌ No user info returned")
                return None
            
            # Get current grades
            grades = await self.get_current_grades(token)
            logger.info(f"📊 Current grades count: {len(grades)}")
            
            # Return combined data
            return {**user_info, "grades": grades}
            
        except Exception as e:
            logger.error(f"❌ Error getting user data: {e}", exc_info=True)
            return None 