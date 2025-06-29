"""
🏫 University API Integration
"""
import asyncio
import logging
import aiohttp
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup

from config import CONFIG

logger = logging.getLogger(__name__)

class UniversityAPI:
    """University API integration"""
    
    def __init__(self):
        self.login_url = CONFIG["UNIVERSITY_LOGIN_URL"]
        self.api_url = CONFIG["UNIVERSITY_API_URL"]
        self.api_headers = CONFIG["API_HEADERS"]
        self.timeout = aiohttp.ClientTimeout(total=CONFIG.get("REQUEST_TIMEOUT_SECONDS", 30))
    
    async def login(self, username: str, password: str) -> Optional[str]:
        """Login to university system"""
        max_retries = CONFIG.get("MAX_RETRY_ATTEMPTS", 3)
        
        for attempt in range(max_retries):
            try:
                logger.info(f"DEBUG: Login attempt {attempt + 1}/{max_retries} for user {username}")
                
                # Use the correct GraphQL mutation format
                payload = {
                    "operationName": "signinUser",
                    "variables": {"username": username, "password": password},
                    "query": """
                        mutation signinUser($username: String!, $password: String!) {
                            login(username: $username, password: $password)
                        }
                    """
                }
                
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(
                        self.login_url,
                        headers=self.api_headers,
                        json=payload
                    ) as response:
                        logger.info(f"DEBUG: Login response status: {response.status}")
                        
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"DEBUG: Login response data: {data}")
                            
                            token = data.get("data", {}).get("login")
                            if token:
                                logger.info(f"Login successful for user: {username}")
                                return token
                            else:
                                logger.warning(f"Login failed for user: {username} - no token in response")
                                return None
                        elif response.status == 401:
                            logger.error(f"Login failed for user: {username} - invalid credentials")
                            return None
                        else:
                            logger.error(f"Login request failed with status: {response.status}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                                continue
                            return None
                            
            except asyncio.TimeoutError:
                logger.error(f"Login timeout for user {username} (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
            except Exception as e:
                logger.error(f"Error during login for user {username} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
        
        return None
    
    async def test_token(self, token: str) -> bool:
        """Test if token is still valid"""
        try:
            logger.info(f"🔍 DEBUG: Testing token validity...")
            test_query = """
            query TestToken {
                getGUI {
                    user {
                        id
                        username
                    }
                }
            }
            """
            
            headers = {**self.api_headers, "Authorization": f"Bearer {token}"}
            
            payload = {
                "query": test_query
            }
            
            logger.info(f"🌐 DEBUG: Making token test request to {self.api_url}")
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                ) as response:
                    logger.info(f"📡 DEBUG: Token test response status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"📄 DEBUG: Token test response data: {data}")
                        is_valid = "data" in data and data["data"] and data["data"]["getGUI"]
                        logger.info(f"✅ DEBUG: Token is {'valid' if is_valid else 'invalid'}")
                        return is_valid
                    else:
                        logger.warning(f"❌ DEBUG: Token test failed with status: {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ DEBUG: Error testing token: {e}")
            return False
    
    async def get_user_data(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user data including grades"""
        try:
            logger.info(f"🔍 DEBUG: Getting user data with token...")
            
            # Get user info
            logger.info(f"👤 DEBUG: Fetching user info...")
            user_info = await self._get_user_info(token)
            if not user_info:
                logger.warning(f"❌ DEBUG: Failed to get user info")
                return None
            
            logger.info(f"✅ DEBUG: User info retrieved: {user_info}")
            
            # Get grades
            logger.info(f"📊 DEBUG: Fetching grades...")
            grades = await self._get_grades(token)
            logger.info(f"📚 DEBUG: Grades retrieved: {len(grades)} courses")
            
            # Combine data
            user_data = {
                **user_info,
                "grades": grades
            }
            
            logger.info(f"✅ DEBUG: User data retrieved successfully - {len(grades)} grades")
            return user_data
            
        except Exception as e:
            logger.error(f"❌ DEBUG: Error getting user data: {e}")
            return None
    
    async def _get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user information"""
        try:
            user_query = """
            {
              getGUI {
                user {
                  id
                  firstname
                  lastname
                  fullname
                  email
                  username
                }
              }
            }
            """
            
            headers = {**self.api_headers, "Authorization": f"Bearer {token}"}
            
            payload = {
                "query": user_query
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "data" in data and data["data"] and data["data"]["getGUI"]:
                            user = data["data"]["getGUI"]["user"]
                            return {
                                "id": user.get("id"),
                                "firstname": user.get("firstname"),
                                "lastname": user.get("lastname"),
                                "fullname": user.get("fullname"),
                                "email": user.get("email"),
                                "username": user.get("username")
                            }
                    
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    async def _get_grades(self, token: str) -> List[Dict[str, Any]]:
        """Get user grades"""
        try:
            logger.info(f"🔍 DEBUG: Starting grade fetch with token...")
            grades_query = """
            query getPage($name: String!, $params: [PageParam!]) {
              getPage(name: $name, params: $params) {
                panels {
                  blocks {
                    title
                    body
                  }
                }
              }
            }
            """
            
            headers = {**self.api_headers, "Authorization": f"Bearer {token}"}
            
            # Try different page names that might contain grades
            possible_pages = [
                "homepage",
                "grades",
                "academic_record", 
                "student_grades",
                "courses",
                "transcript",
                "final_courses_grades_page",
                "student_academic_record"
            ]
            
            logger.info(f"🔍 DEBUG: Will try {len(possible_pages)} possible pages for grades")
            
            for page_name in possible_pages:
                logger.info(f"🌐 DEBUG: Trying page: {page_name}")
                
                variables = {
                    "name": page_name,
                    "params": []
                }
                
                payload = {
                    "query": grades_query,
                    "variables": variables
                }
                
                logger.info(f"📡 DEBUG: Making request to {self.api_url} for page: {page_name}")
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(
                        self.api_url,
                        headers=headers,
                        json=payload
                    ) as response:
                        logger.info(f"📡 DEBUG: Page {page_name} response status: {response.status}")
                        
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"📄 DEBUG: Page {page_name} response data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                            
                            if "data" in data and data["data"] and data["data"]["getPage"]:
                                logger.info(f"✅ DEBUG: Page {page_name} has valid data structure")
                                grades = self._parse_grades_from_html(data["data"]["getPage"])
                                if grades:  # If we found grades, return them
                                    logger.info(f"🎉 DEBUG: Found {len(grades)} grades in page: {page_name}")
                                    return grades
                                else:
                                    logger.info(f"❌ DEBUG: No grades found in page: {page_name}")
                            else:
                                logger.info(f"❌ DEBUG: No valid data structure in page: {page_name}")
                        else:
                            logger.warning(f"❌ DEBUG: Page {page_name} failed with status: {response.status}")
            
            logger.warning(f"❌ DEBUG: No grades found in any of the {len(possible_pages)} pages tried")
            return []
                    
        except Exception as e:
            logger.error(f"❌ DEBUG: Error getting grades: {e}")
            return []
    
    def _parse_grades_from_html(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse grades from HTML response"""
        try:
            logger.info("DEBUG: Starting HTML parsing")
            grades = []
            
            if "panels" in page_data:
                logger.info(f"DEBUG: Found {len(page_data['panels'])} panels")
                for panel_index, panel in enumerate(page_data["panels"]):
                    logger.info(f"DEBUG: Processing panel {panel_index + 1}")
                    if "blocks" in panel:
                        logger.info(f"DEBUG: Found {len(panel['blocks'])} blocks in panel {panel_index + 1}")
                        for block_index, block in enumerate(panel["blocks"]):
                            block_title = block.get('title', 'No title')
                            logger.info(f"DEBUG: Block {block_index + 1} - Title: '{block_title}'")
                            
                            # Log the full block structure for debugging
                            logger.info(f"DEBUG: Block {block_index + 1} full data: {block}")
                            
                            # Skip student card block (بطاقة الطالب) - it contains student info, not grades
                            if block_title == "بطاقة الطالب":
                                logger.info("DEBUG: Skipping student card block - contains student info, not grades")
                                continue
                            
                            # Parse any other block that has HTML body content
                            html_body = block.get("body", "")
                            if html_body:
                                logger.info(f"DEBUG: Block {block_index + 1} HTML body length: {len(html_body)}")
                                logger.info(f"DEBUG: Block {block_index + 1} HTML body preview: {html_body[:200]}...")
                                
                                # Check if this block contains course data by analyzing the HTML content
                                if self._contains_course_data(html_body):
                                    logger.info(f"DEBUG: Block {block_index + 1} appears to contain course data")
                                    parsed_grades = self._extract_grades_from_html(html_body)
                                    if parsed_grades:  # Only add if we found grades
                                        grades.extend(parsed_grades)
                                        logger.info(f"DEBUG: Found {len(parsed_grades)} grades in block: {block_title}")
                                else:
                                    logger.info(f"DEBUG: Block {block_index + 1} does not contain course data")
                            else:
                                logger.info(f"DEBUG: Block {block_index + 1} has no HTML body")
                    else:
                        logger.info(f"DEBUG: Panel {panel_index + 1} has no blocks")
            else:
                logger.warning("DEBUG: No panels found in page data")
                logger.info(f"DEBUG: Full page_data structure: {page_data}")
            
            logger.info(f"Parsed {len(grades)} total grades from all blocks")
            return grades
            
        except Exception as e:
            logger.error(f"Error parsing grades from HTML: {e}")
            return []
    
    def _contains_course_data(self, html_content: str) -> bool:
        """Check if HTML content contains course data by analyzing the structure and content"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for tables
            tables = soup.find_all("table")
            if not tables:
                logger.info("DEBUG: No tables found in HTML content")
                return False
            
            logger.info(f"DEBUG: Found {len(tables)} tables in HTML content")
            
            for table_index, table in enumerate(tables):
                # Check if this table looks like it contains course data
                if self._is_course_table(table):
                    logger.info(f"DEBUG: Table {table_index + 1} appears to contain course data")
                    return True
            
            logger.info("DEBUG: No course tables found in HTML content")
            return False
            
        except Exception as e:
            logger.error(f"Error checking for course data: {e}")
            return False
    
    def _is_course_table(self, table) -> bool:
        """Check if a table contains course data by analyzing its structure"""
        try:
            # Find thead to get headers
            thead = table.find("thead")
            if not thead:
                return False
            
            # Extract headers
            headers = []
            for th in thead.find_all("th"):
                header_text = th.get_text(strip=True)
                if header_text:
                    headers.append(header_text)
            
            if not headers:
                return False
            
            logger.info(f"DEBUG: Table headers: {headers}")
            
            # Skip tables that are clearly student info
            student_info_indicators = ['sis.code', 'sis.name', 'sis.academy', 'sis.branch', 'sis.program_abs_grade_num', 'student', 'student_id', 'gpa']
            if any(indicator in ' '.join(headers).lower() for indicator in student_info_indicators):
                logger.info("DEBUG: Table contains student info, not course data")
                return False
            
            # Look for course-related indicators in headers
            course_indicators = ['course', 'subject', 'grade', 'mark', 'score', 'credit', 'ects', 'مقرر', 'درجة', 'رصيد', 'كود', 'مادة']
            has_course_indicators = any(indicator in ' '.join(headers).lower() for indicator in course_indicators)
            
            if has_course_indicators:
                logger.info("DEBUG: Table has course-related headers")
                return True
            
            # If no clear course indicators, check the table content
            tbody = table.find("tbody")
            if tbody:
                rows = tbody.find_all("tr")
                if len(rows) > 1:  # More than just header row
                    # Check if any row contains what looks like course data
                    for row in rows[:3]:  # Check first 3 rows
                        cells = row.find_all("td")
                        if len(cells) >= 3:  # At least 3 columns
                            # Check if any cell contains course-like data
                            for cell in cells:
                                cell_text = cell.get_text(strip=True)
                                if cell_text:
                                    # Check for course codes (alphanumeric with letters and numbers)
                                    if any(char.isalpha() for char in cell_text) and any(char.isdigit() for char in cell_text):
                                        logger.info(f"DEBUG: Found potential course code: {cell_text}")
                                        return True
                                    # Check for grades (numbers with possible %)
                                    if any(char.isdigit() for char in cell_text) and ('%' in cell_text or cell_text.replace('.', '').replace('%', '').isdigit()):
                                        logger.info(f"DEBUG: Found potential grade: {cell_text}")
                                        return True
            
            logger.info("DEBUG: Table does not appear to contain course data")
            return False
            
        except Exception as e:
            logger.error(f"Error checking if table contains course data: {e}")
            return False
    
    def _extract_grades_from_html(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract grades from HTML content"""
        try:
            logger.info("DEBUG: Starting HTML table parsing")
            grades = []
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for any table structure
            tables = soup.find_all("table")
            if not tables:
                logger.info("DEBUG: No tables found in HTML")
                return []
            
            logger.info(f"DEBUG: Found {len(tables)} tables")
            
            for table_index, table in enumerate(tables):
                logger.info(f"DEBUG: Processing table {table_index + 1}")
                
                # Find thead to get headers
                thead = table.find("thead")
                if not thead:
                    logger.info(f"DEBUG: No thead found in table {table_index + 1}")
                    continue
                
                # Extract headers from th elements
                headers = []
                for th in thead.find_all("th"):
                    header_text = th.get_text(strip=True)
                    if header_text:  # Only add non-empty headers
                        headers.append(header_text)
                        logger.info(f"DEBUG: Found header: {header_text}")
                
                if not headers:
                    logger.info(f"DEBUG: No valid headers found in table {table_index + 1}")
                    continue
                
                logger.info(f"DEBUG: Table {table_index + 1} headers: {headers}")
                
                # Skip tables that are clearly student info (not course grades)
                # These are common student info headers that we want to skip
                student_info_indicators = ['sis.code', 'sis.name', 'sis.academy', 'sis.branch', 'sis.program_abs_grade_num', 'student', 'student_id', 'gpa']
                if any(indicator in ' '.join(headers).lower() for indicator in student_info_indicators):
                    logger.info(f"DEBUG: Skipping table {table_index + 1} - appears to contain student info")
                    continue
                
                # Check if this table looks like it contains course data
                # Look for any indication of courses, grades, or academic data
                course_indicators = ['course', 'subject', 'grade', 'mark', 'score', 'credit', 'ects', 'مقرر', 'درجة', 'رصيد', 'كود']
                has_course_indicators = any(indicator in ' '.join(headers).lower() for indicator in course_indicators)
                
                # If no clear course indicators, but table has multiple columns and rows, still process it
                # (it might be course data with different naming)
                if not has_course_indicators:
                    logger.info(f"DEBUG: Table {table_index + 1} has no clear course indicators, but will process anyway")
                
                logger.info(f"DEBUG: Processing table {table_index + 1} for potential course data")
                
                # Find tbody to get rows
                tbody = table.find("tbody")
                if not tbody:
                    logger.info(f"DEBUG: No tbody found in table {table_index + 1}")
                    continue
                
                # Parse each row
                for row_index, row in enumerate(tbody.find_all("tr")):
                    cells = row.find_all("td")
                    if len(cells) != len(headers):
                        logger.info(f"DEBUG: Row {row_index + 1} has {len(cells)} cells but {len(headers)} headers, skipping")
                        continue
                    
                    # Extract data from each cell as raw text
                    row_data = {}
                    has_meaningful_data = False
                    
                    for i, cell in enumerate(cells):
                        cell_text = cell.get_text(strip=True)
                        row_data[headers[i]] = cell_text
                        logger.info(f"DEBUG: Cell {i} ({headers[i]}): {cell_text}")
                        
                        # Check if this row has any meaningful data (not empty or just whitespace)
                        if cell_text and cell_text.strip() and cell_text.strip() != "":
                            has_meaningful_data = True
                    
                    # Only add rows that have some meaningful data
                    if has_meaningful_data:
                        # Additional validation: skip rows that look like headers or empty data
                        # Check if this looks like a real course row (not just headers repeated)
                        is_likely_course_row = False
                        
                        # If any cell contains what looks like a course code (alphanumeric with letters)
                        for value in row_data.values():
                            if value and any(char.isalpha() for char in value) and any(char.isdigit() for char in value):
                                is_likely_course_row = True
                                break
                        
                        # Or if any cell contains what looks like a grade (numbers with possible %)
                        for value in row_data.values():
                            if value and any(char.isdigit() for char in value) and ('%' in value or value.replace('.', '').replace('%', '').isdigit()):
                                is_likely_course_row = True
                                break
                        
                        # Or if we have at least 3 non-empty cells (likely course data)
                        non_empty_cells = sum(1 for v in row_data.values() if v and v.strip())
                        if non_empty_cells >= 3:
                            is_likely_course_row = True
                        
                        if is_likely_course_row:
                            grades.append(row_data)
                            logger.info(f"DEBUG: Added grade entry: {row_data}")
                        else:
                            logger.info(f"DEBUG: Skipped row that doesn't look like course data: {row_data}")
                    else:
                        logger.info(f"DEBUG: Skipped empty row: {row_data}")
            
            logger.info(f"DEBUG: Total grades parsed: {len(grades)}")
            return grades
            
        except Exception as e:
            logger.error(f"Error extracting grades from HTML: {e}")
            return [] 