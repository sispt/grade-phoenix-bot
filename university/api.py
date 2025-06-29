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
                "homepage"  # Only homepage contains grades
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
                logger.info(f"📡 DEBUG: Request payload: {payload}")
                logger.info(f"📡 DEBUG: Request headers: {headers}")
                
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
                            
                            # Log the full response structure for debugging
                            logger.info(f"🔍 DEBUG: Full response for {page_name}: {data}")
                            
                            if "data" in data and data["data"] and data["data"]["getPage"]:
                                logger.info(f"✅ DEBUG: Page {page_name} has valid data structure")
                                page_content = data["data"]["getPage"]
                                logger.info(f"📋 DEBUG: Page {page_name} content structure: {page_content}")
                                
                                # Log each panel and block in detail
                                if "panels" in page_content:
                                    logger.info(f"📋 DEBUG: Found {len(page_content['panels'])} panels")
                                    for panel_idx, panel in enumerate(page_content["panels"]):
                                        logger.info(f"📋 DEBUG: Panel {panel_idx + 1}: {panel}")
                                        if "blocks" in panel:
                                            logger.info(f"📋 DEBUG: Panel {panel_idx + 1} has {len(panel['blocks'])} blocks")
                                            for block_idx, block in enumerate(panel["blocks"]):
                                                logger.info(f"📋 DEBUG: Block {block_idx + 1} in panel {panel_idx + 1}:")
                                                logger.info(f"   Title: {block.get('title', 'No title')}")
                                                logger.info(f"   Body length: {len(block.get('body', ''))}")
                                                logger.info(f"   Body preview: {block.get('body', '')[:500]}...")
                                
                                grades = self._parse_grades_from_html(page_content)
                                if grades:  # If we found grades, return them
                                    logger.info(f"🎉 DEBUG: Found {len(grades)} grades in page: {page_name}")
                                    return grades
                                else:
                                    logger.info(f"❌ DEBUG: No grades found in page: {page_name}")
                            else:
                                logger.info(f"❌ DEBUG: No valid data structure in page: {page_name}")
                                if "data" in data:
                                    logger.info(f"📄 DEBUG: Data content: {data['data']}")
                                if "errors" in data:
                                    logger.info(f"❌ DEBUG: GraphQL errors: {data['errors']}")
                        else:
                            logger.warning(f"❌ DEBUG: Page {page_name} failed with status: {response.status}")
                            try:
                                error_text = await response.text()
                                logger.info(f"❌ DEBUG: Error response: {error_text}")
                            except:
                                logger.info(f"❌ DEBUG: Could not read error response")
            
            logger.warning(f"❌ DEBUG: No grades found in homepage")
            
            # Try direct HTTP request to homepage as fallback
            logger.info("🔄 DEBUG: Trying direct HTTP request to homepage...")
            try:
                homepage_url = "https://staging.sis.shamuniversity.com/page/home"
                logger.info(f"🌐 DEBUG: Making direct request to: {homepage_url}")
                
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.get(
                        homepage_url,
                        headers={**self.api_headers, "Authorization": f"Bearer {token}"}
                    ) as response:
                        logger.info(f"📡 DEBUG: Direct homepage response status: {response.status}")
                        if response.status == 200:
                            html_content = await response.text()
                            logger.info(f"📄 DEBUG: Direct homepage HTML length: {len(html_content)}")
                            logger.info(f"📄 DEBUG: Direct homepage HTML preview: {html_content[:1000]}...")
                            
                            # Try to parse grades from the direct HTML
                            soup = BeautifulSoup(html_content, 'html.parser')
                            tables = soup.find_all("table")
                            logger.info(f"📋 DEBUG: Found {len(tables)} tables in direct homepage HTML")
                            
                            for table_idx, table in enumerate(tables):
                                logger.info(f"📋 DEBUG: Table {table_idx + 1} HTML: {table}")
                        else:
                            logger.info(f"❌ DEBUG: Direct homepage request failed with status: {response.status}")
            except Exception as e:
                logger.error(f"❌ DEBUG: Direct homepage request failed: {e}")
            
            # Try alternative GraphQL queries as fallback
            logger.info("🔄 DEBUG: Trying alternative GraphQL queries...")
            
            # Try a more generic query
            alternative_query = """
            query {
              grades {
                courseName
                courseCode
                grade
                credits
              }
            }
            """
            
            try:
                logger.info("🔍 DEBUG: Trying alternative grades query...")
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(
                        self.api_url,
                        headers=headers,
                        json={"query": alternative_query}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"📄 DEBUG: Alternative query response: {data}")
                            if "data" in data and data["data"] and data["data"]["grades"]:
                                logger.info("🎉 DEBUG: Found grades with alternative query!")
                                return data["data"]["grades"]
            except Exception as e:
                logger.error(f"❌ DEBUG: Alternative query failed: {e}")
            
            # Try another alternative query
            courses_query = """
            query {
              courses {
                name
                code
                grade
                ects
              }
            }
            """
            
            try:
                logger.info("🔍 DEBUG: Trying courses query...")
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(
                        self.api_url,
                        headers=headers,
                        json={"query": courses_query}
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            logger.info(f"📄 DEBUG: Courses query response: {data}")
                            if "data" in data and data["data"] and data["data"]["courses"]:
                                logger.info("🎉 DEBUG: Found courses with courses query!")
                                return data["data"]["courses"]
            except Exception as e:
                logger.error(f"❌ DEBUG: Courses query failed: {e}")
            
            return []
                    
        except Exception as e:
            logger.error(f"❌ DEBUG: Error getting grades: {e}")
            return []
    
    def _parse_grades_from_html(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse grades from HTML response"""
        try:
            logger.info("DEBUG: Starting HTML parsing for homepage")
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
                                logger.info(f"DEBUG: Block {block_index + 1} HTML body preview: {html_body[:500]}...")
                                
                                # For homepage, be more aggressive - parse any block with HTML content
                                # that might contain course data
                                logger.info(f"DEBUG: Processing block {block_index + 1} for potential course data")
                                parsed_grades = self._extract_grades_from_html(html_body)
                                if parsed_grades:  # Only add if we found grades
                                    grades.extend(parsed_grades)
                                    logger.info(f"DEBUG: Found {len(parsed_grades)} grades in block: {block_title}")
                                else:
                                    logger.info(f"DEBUG: No grades found in block: {block_title}")
                            else:
                                logger.info(f"DEBUG: Block {block_index + 1} has no HTML body (body is None or empty)")
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
            logger.info("DEBUG: Starting HTML table parsing for homepage")
            grades = []
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for any table structure
            tables = soup.find_all("table")
            if not tables:
                logger.info("DEBUG: No tables found in HTML")
                # Also look for div elements that might contain course data
                divs = soup.find_all("div")
                logger.info(f"DEBUG: Found {len(divs)} div elements")
                for div in divs:
                    div_text = div.get_text(strip=True)
                    if div_text and len(div_text) > 50:  # Meaningful content
                        logger.info(f"DEBUG: Div content preview: {div_text[:200]}...")
                return []
            
            logger.info(f"DEBUG: Found {len(tables)} tables")
            
            for table_index, table in enumerate(tables):
                logger.info(f"DEBUG: Processing table {table_index + 1}")
                
                # Find thead to get headers
                thead = table.find("thead")
                if not thead:
                    logger.info(f"DEBUG: No thead found in table {table_index + 1}, looking for tr elements directly")
                    # Try to find headers in the first tr
                    first_tr = table.find("tr")
                    if first_tr:
                        # Check if first row contains headers (th elements)
                        th_elements = first_tr.find_all("th")
                        if th_elements:
                            headers = [th.get_text(strip=True) for th in th_elements if th.get_text(strip=True)]
                            logger.info(f"DEBUG: Found headers in first row: {headers}")
                        else:
                            # Use td elements from first row as headers
                            td_elements = first_tr.find_all("td")
                            headers = [f"Column_{i+1}" for i in range(len(td_elements))]
                            logger.info(f"DEBUG: Using generic headers: {headers}")
                    else:
                        logger.info(f"DEBUG: No tr elements found in table {table_index + 1}")
                        continue
                else:
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
                
                # For homepage, be more aggressive - process any table with multiple columns
                # that might contain course data, regardless of header names
                logger.info(f"DEBUG: Processing table {table_index + 1} for potential course data")
                
                # Find tbody to get rows, or use all tr elements if no tbody
                tbody = table.find("tbody")
                if tbody:
                    rows = tbody.find_all("tr")
                    logger.info(f"DEBUG: Found {len(rows)} rows in tbody")
                else:
                    # No tbody, get all tr elements
                    rows = table.find_all("tr")
                    logger.info(f"DEBUG: Found {len(rows)} rows in table (no tbody)")
                    # Skip the first row if it was used for headers
                    if thead:
                        rows = rows[1:]  # Skip header row
                        logger.info(f"DEBUG: Skipping header row, processing {len(rows)} data rows")
                
                # Parse each row
                for row_index, row in enumerate(rows):
                    cells = row.find_all("td")
                    if len(cells) != len(headers):
                        logger.info(f"DEBUG: Row {row_index + 1} has {len(cells)} cells but {len(headers)} headers, adjusting")
                        # Adjust headers to match cells
                        if len(cells) > len(headers):
                            # Add generic headers for extra columns
                            for i in range(len(headers), len(cells)):
                                headers.append(f"Column_{i+1}")
                        else:
                            # Truncate headers to match cells
                            headers = headers[:len(cells)]
                    
                    # Extract data from each cell as raw text
                    row_data = {}
                    has_meaningful_data = False
                    
                    for i, cell in enumerate(cells):
                        if i < len(headers):
                            cell_text = cell.get_text(strip=True)
                            row_data[headers[i]] = cell_text
                            logger.info(f"DEBUG: Cell {i} ({headers[i]}): {cell_text}")
                            
                            # Check if this row has any meaningful data (not empty or just whitespace)
                            if cell_text and cell_text.strip() and cell_text.strip() != "":
                                has_meaningful_data = True
                    
                    # For homepage, be more aggressive - include any row with meaningful data
                    # that has at least 2 non-empty cells
                    if has_meaningful_data:
                        non_empty_cells = sum(1 for v in row_data.values() if v and v.strip())
                        logger.info(f"DEBUG: Row {row_index + 1} has {non_empty_cells} non-empty cells")
                        
                        # Include any row with at least 2 non-empty cells that might be course data
                        if non_empty_cells >= 2:
                            # Additional check: skip rows that are clearly not course data
                            is_likely_course_row = False
                            
                            # Check for course-like patterns
                            for value in row_data.values():
                                if value:
                                    # Course codes (alphanumeric with letters and numbers)
                                    if any(char.isalpha() for char in value) and any(char.isdigit() for char in value):
                                        is_likely_course_row = True
                                        logger.info(f"DEBUG: Found potential course code: {value}")
                                        break
                                    # Grades (numbers with possible %)
                                    if any(char.isdigit() for char in value) and ('%' in value or value.replace('.', '').replace('%', '').isdigit()):
                                        is_likely_course_row = True
                                        logger.info(f"DEBUG: Found potential grade: {value}")
                                        break
                                    # Course names (Arabic or English text)
                                    if len(value) > 3 and not value.isdigit():
                                        is_likely_course_row = True
                                        logger.info(f"DEBUG: Found potential course name: {value}")
                                        break
                            
                            # If no clear patterns but has multiple cells, still include it
                            if not is_likely_course_row and non_empty_cells >= 3:
                                is_likely_course_row = True
                                logger.info(f"DEBUG: Including row with {non_empty_cells} cells despite no clear patterns")
                            
                            if is_likely_course_row:
                                grades.append(row_data)
                                logger.info(f"DEBUG: Added grade entry: {row_data}")
                            else:
                                logger.info(f"DEBUG: Skipped row that doesn't look like course data: {row_data}")
                        else:
                            logger.info(f"DEBUG: Skipped row with insufficient data: {row_data}")
                    else:
                        logger.info(f"DEBUG: Skipped empty row: {row_data}")
            
            logger.info(f"DEBUG: Total grades parsed: {len(grades)}")
            return grades
            
        except Exception as e:
            logger.error(f"Error extracting grades from HTML: {e}")
            return [] 