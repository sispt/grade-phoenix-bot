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
                
                # Validate inputs
                if not username or not password:
                    logger.warning(f"DEBUG: Invalid credentials for user {username}")
                    return None
                
                payload = {
                    "operationName": "signinUser",
                    "variables": {"username": username, "password": password},
                    "query": """
                        mutation signinUser($username: String!, $password: String!) {
                            login(username: $username, password: $password)
                        }
                    """
                }
                
                logger.info(f"DEBUG: Making login request to {self.login_url}")
                logger.info(f"DEBUG: Payload: {payload}")
                
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(
                        self.login_url,
                        headers=self.api_headers,
                        json=payload
                    ) as response:
                        logger.info(f"DEBUG: Login response status: {response.status}")
                        logger.info(f"DEBUG: Response headers: {dict(response.headers)}")
                        
                        # Get response content type
                        content_type = response.headers.get('Content-Type', '')
                        logger.info(f"DEBUG: Content-Type: {content_type}")
                        
                        if response.status == 200:
                            try:
                                # Check if response is JSON
                                if 'application/json' not in content_type.lower():
                                    response_text = await response.text()
                                    logger.error(f"DEBUG: Expected JSON but got {content_type}. Response: {response_text[:500]}")
                                    
                                    # If it's HTML, it might be an error page
                                    if 'text/html' in content_type.lower():
                                        logger.error(f"DEBUG: Server returned HTML instead of JSON. This might indicate:")
                                        logger.error(f"DEBUG: 1. Wrong URL endpoint")
                                        logger.error(f"DEBUG: 2. Server error")
                                        logger.error(f"DEBUG: 3. Authentication required")
                                    
                                    if attempt < max_retries - 1:
                                        await asyncio.sleep(2 ** attempt)
                                        continue
                                    return None
                                
                                data = await response.json()
                                logger.info(f"DEBUG: Login response data: {data}")
                                
                                token = data.get("data", {}).get("login")
                                if token:
                                    logger.info(f"✅ Login successful for user: {username}")
                                    return token
                                else:
                                    logger.warning(f"❌ Login failed for user: {username} - no token in response")
                                    return None
                            except json.JSONDecodeError as json_error:
                                response_text = await response.text()
                                logger.error(f"DEBUG: JSON decode error: {json_error}")
                                logger.error(f"DEBUG: Response text: {response_text[:500]}")
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(2 ** attempt)
                                    continue
                                return None
                        elif response.status == 401:
                            logger.error(f"❌ Login failed for user: {username} - invalid credentials")
                            return None
                        elif response.status == 429:
                            logger.warning(f"⚠️ Rate limited for user {username}, retrying...")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(2 ** attempt)
                                continue
                            return None
                        elif response.status == 404:
                            logger.error(f"❌ Login endpoint not found: {self.login_url}")
                            return None
                        else:
                            response_text = await response.text()
                            logger.error(f"❌ Login request failed with status: {response.status}")
                            logger.error(f"DEBUG: Response text: {response_text[:500]}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(2 ** attempt)
                                continue
                            return None
                            
            except asyncio.TimeoutError:
                logger.error(f"⏰ Login timeout for user {username} (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return None
            except aiohttp.ClientError as client_error:
                logger.error(f"🌐 Network error during login for user {username} (attempt {attempt + 1}): {client_error}")
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
        """Get user grades from GraphQL endpoint"""
        try:
            logger.info(f"🔍 DEBUG: Starting grade fetch with token...")
            
            # Use the correct GraphQL endpoint and query
            graphql_url = "https://staging.sis.shamuniversity.com/portal/graphql"
            
            # GraphQL query for test_student_tracks
            grades_query = """
            query {
              getPage(name: "test_student_tracks") {
                name
                title
                panels {
                  blocks {
                    name
                    body
                  }
                }
              }
            }
            """
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Accept-Language": "ar-SA,ar;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br, zstd",
                "Referer": "https://staging.sis.shamuniversity.com/",
                "Origin": "https://staging.sis.shamuniversity.com",
                "Connection": "keep-alive",
                "x-lang": "ar"
            }
            
            payload = {
                "query": grades_query
            }
            
            logger.info(f"🌐 DEBUG: Making GraphQL request to {graphql_url}")
            logger.info(f"📡 DEBUG: Request payload: {payload}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    graphql_url,
                    headers=headers,
                    json=payload
                ) as response:
                    logger.info(f"📡 DEBUG: GraphQL response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"📄 DEBUG: GraphQL response data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                        
                        if "data" in data and data["data"] and data["data"]["getPage"]:
                            page_content = data["data"]["getPage"]
                            logger.info(f"✅ DEBUG: Got page content: {page_content.get('name', 'Unknown')}")
                            
                            # Parse grades from the page content
                            grades = self._parse_grades_from_graphql(page_content)
                            logger.info(f"🎉 DEBUG: Parsed {len(grades)} grades from GraphQL")
                            return grades
                        else:
                            logger.error(f"❌ DEBUG: Invalid GraphQL response structure")
                            if "errors" in data:
                                logger.error(f"❌ DEBUG: GraphQL errors: {data['errors']}")
                            return []
                    else:
                        logger.error(f"❌ DEBUG: GraphQL request failed with status: {response.status}")
                        try:
                            error_text = await response.text()
                            logger.error(f"❌ DEBUG: Error response: {error_text}")
                        except:
                            logger.error(f"❌ DEBUG: Could not read error response")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ DEBUG: Error getting grades from GraphQL: {e}")
            return []
    
    def _parse_grades_from_graphql(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse grades from GraphQL page data"""
        try:
            logger.info("🔍 DEBUG: Starting to parse grades from GraphQL data")
            grades = []
            
            if not page_data or "panels" not in page_data:
                logger.warning("❌ DEBUG: No panels found in GraphQL data")
                return []
            
            panels = page_data["panels"]
            logger.info(f"📋 DEBUG: Found {len(panels)} panels in GraphQL data")
            
            for panel_idx, panel in enumerate(panels):
                logger.info(f"📋 DEBUG: Processing panel {panel_idx + 1}")
                
                if "blocks" not in panel:
                    logger.info(f"❌ DEBUG: No blocks found in panel {panel_idx + 1}")
                    continue
                
                blocks = panel["blocks"]
                logger.info(f"📋 DEBUG: Panel {panel_idx + 1} has {len(blocks)} blocks")
                
                for block_idx, block in enumerate(blocks):
                    logger.info(f"📋 DEBUG: Processing block {block_idx + 1} in panel {panel_idx + 1}")
                    
                    body = block.get('body', '')
                    if not body:
                        logger.info(f"❌ DEBUG: No body content in block {block_idx + 1}")
                        continue
                    
                    logger.info(f"📄 DEBUG: Block {block_idx + 1} body length: {len(body)}")
                    
                    # Check if this block contains the grades table (look for "كود المادة")
                    if "كود المادة" in body:
                        logger.info(f"✅ DEBUG: Found grades table in block {block_idx + 1}")
                        
                        # Parse the HTML table
                        block_grades = self._parse_grades_table_html(body)
                        if block_grades:
                            logger.info(f"🎉 DEBUG: Found {len(block_grades)} grades in block {block_idx + 1}")
                            grades.extend(block_grades)
                        else:
                            logger.info(f"❌ DEBUG: No grades parsed from block {block_idx + 1}")
                    else:
                        logger.info(f"⏭️ DEBUG: Block {block_idx + 1} does not contain grades table")
            
            logger.info(f"🎉 DEBUG: Total grades parsed from GraphQL: {len(grades)}")
            return grades
            
        except Exception as e:
            logger.error(f"❌ DEBUG: Error parsing grades from GraphQL data: {e}")
            return []
    
    def _parse_grades_table_html(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse grades from HTML table with Arabic headers"""
        try:
            logger.info("🔍 DEBUG: Starting to parse grades table HTML")
            grades = []
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find the table
            table = soup.find('table')
            if not table:
                logger.error("❌ DEBUG: No table found in HTML")
                return []
            
            # Find thead to get headers
            thead = table.find('thead')
            if not thead:
                logger.error("❌ DEBUG: No thead found in table")
                return []
            
            # Extract headers
            headers = []
            for th in thead.find_all('th'):
                header_text = th.get_text(strip=True)
                if header_text:
                    headers.append(header_text)
                    logger.info(f"📋 DEBUG: Found header: {header_text}")
            
            if not headers:
                logger.error("❌ DEBUG: No headers found in table")
                return []
            
            logger.info(f"📋 DEBUG: Table headers: {headers}")
            
            # Find tbody to get rows
            tbody = table.find('tbody')
            if not tbody:
                logger.error("❌ DEBUG: No tbody found in table")
                return []
            
            rows = tbody.find_all('tr')
            logger.info(f"📋 DEBUG: Found {len(rows)} rows in table")
            
            # Parse each row
            for row_idx, row in enumerate(rows):
                cells = row.find_all('td')
                if len(cells) != len(headers):
                    logger.warning(f"⚠️ DEBUG: Row {row_idx + 1} has {len(cells)} cells but {len(headers)} headers")
                    continue
                
                # Extract data from each cell
                row_data = {}
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        cell_text = cell.get_text(strip=True)
                        row_data[headers[i]] = cell_text
                
                # Convert to standard format
                grade_entry = {
                    "name": row_data.get("المقرر", ""),
                    "code": row_data.get("كود المادة", ""),
                    "ects": row_data.get("رصيد ECTS", ""),
                    "coursework": row_data.get("درجة الأعمال", ""),
                    "final_exam": row_data.get("درجة النظري", ""),
                    "total": row_data.get("الدرجة", "")
                }
                
                # Only add if we have meaningful data
                if grade_entry["name"] and grade_entry["code"]:
                    grades.append(grade_entry)
                    logger.info(f"✅ DEBUG: Added grade: {grade_entry}")
                else:
                    logger.info(f"⏭️ DEBUG: Skipped row with insufficient data: {row_data}")
            
            logger.info(f"🎉 DEBUG: Parsed {len(grades)} grades from table")
            return grades
            
        except Exception as e:
            logger.error(f"❌ DEBUG: Error parsing grades table HTML: {e}")
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
        """Check if table contains course data"""
        try:
            # Get headers from thead
            thead = table.find("thead")
            if not thead:
                return False
            
            headers = []
            for th in thead.find_all("th"):
                header_text = th.get_text(strip=True).lower()
                if header_text:
                    headers.append(header_text)
            
            if not headers:
                return False
            
            logger.info(f"🔍 DEBUG: Checking table headers: {headers}")
            
            # Course-related headers in Arabic and English
            course_indicators = [
                'course', 'subject', 'grade', 'mark', 'score', 'credit', 'ects',
                'مقرر', 'درجة', 'رصيد', 'كود', 'مادة', 'أعمال', 'نظري', 'عملي'
            ]
            
            # Check if any header contains course indicators
            has_course_indicators = any(
                any(indicator in header for indicator in course_indicators)
                for header in headers
            )
            
            if has_course_indicators:
                logger.info("✅ DEBUG: Table has course-related headers")
                return True
            
            # If no clear course indicators, check the table content
            tbody = table.find("tbody")
            if tbody:
                rows = tbody.find_all("tr")
                if len(rows) > 0:  # Has data rows
                    # Check if any row contains what looks like course data
                    for row in rows[:3]:  # Check first 3 rows
                        cells = row.find_all("td")
                        if len(cells) >= 3:  # At least 3 columns
                            # Check if any cell contains course-like data
                            for cell in cells:
                                cell_text = cell.get_text(strip=True)
                                if cell_text:
                                    # Course codes (alphanumeric with letters and numbers)
                                    if any(char.isalpha() for char in cell_text) and any(char.isdigit() for char in cell_text):
                                        logger.info(f"✅ DEBUG: Found potential course code: {cell_text}")
                                        return True
                                    # Grades (numbers with possible %)
                                    if any(char.isdigit() for char in cell_text) and ('%' in cell_text or cell_text.replace('.', '').replace('%', '').isdigit()):
                                        logger.info(f"✅ DEBUG: Found potential grade: {cell_text}")
                                        return True
                                    # Course names (Arabic or English text longer than 3 chars)
                                    if len(cell_text) > 3 and not cell_text.isdigit():
                                        logger.info(f"✅ DEBUG: Found potential course name: {cell_text}")
                                        return True
            
            logger.info("❌ DEBUG: Table does not appear to contain course data")
            return False
            
        except Exception as e:
            logger.error(f"❌ DEBUG: Error checking if table contains course data: {e}")
            return False
    
    def _extract_grades_from_html(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract grades from HTML content"""
        try:
            logger.info("🔍 DEBUG: Starting HTML table parsing")
            grades = []
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for any table structure
            tables = soup.find_all("table")
            if not tables:
                logger.info("❌ DEBUG: No tables found in HTML")
                return []
            
            logger.info(f"📋 DEBUG: Found {len(tables)} tables")
            
            for table_index, table in enumerate(tables):
                logger.info(f"📋 DEBUG: Processing table {table_index + 1}")
                
                # Find thead to get headers
                thead = table.find("thead")
                if not thead:
                    logger.info(f"❌ DEBUG: No thead found in table {table_index + 1}")
                    continue
                
                # Extract headers from th elements
                headers = []
                for th in thead.find_all("th"):
                    header_text = th.get_text(strip=True)
                    if header_text:  # Only add non-empty headers
                        headers.append(header_text)
                        logger.info(f"📋 DEBUG: Found header: {header_text}")
                
                if not headers:
                    logger.info(f"❌ DEBUG: No valid headers found in table {table_index + 1}")
                    continue
                
                logger.info(f"📋 DEBUG: Table {table_index + 1} headers: {headers}")
                
                # Check if this table contains course data
                if not self._is_course_table(table):
                    logger.info(f"⏭️ DEBUG: Skipping table {table_index + 1} - not a course table")
                    continue
                
                # Find tbody to get rows
                tbody = table.find("tbody")
                if not tbody:
                    logger.info(f"❌ DEBUG: No tbody found in table {table_index + 1}")
                    continue
                
                rows = tbody.find_all("tr")
                logger.info(f"📋 DEBUG: Found {len(rows)} rows in table {table_index + 1}")
                
                # Parse each row
                for row_index, row in enumerate(rows):
                    cells = row.find_all("td")
                    if len(cells) != len(headers):
                        logger.info(f"⚠️ DEBUG: Row {row_index + 1} has {len(cells)} cells but {len(headers)} headers")
                        # Adjust to match
                        if len(cells) > len(headers):
                            headers = headers + [f"Column_{i+1}" for i in range(len(headers), len(cells))]
                        else:
                            headers = headers[:len(cells)]
                    
                    # Extract data from each cell as raw text
                    row_data = {}
                    has_meaningful_data = False
                    
                    for i, cell in enumerate(cells):
                        if i < len(headers):
                            cell_text = cell.get_text(strip=True)
                            row_data[headers[i]] = cell_text
                            
                            # Check if this row has any meaningful data
                            if cell_text and cell_text.strip():
                                has_meaningful_data = True
                    
                    # Only include rows with meaningful data
                    if has_meaningful_data:
                        # Additional validation: check if this looks like course data
                        is_course_row = False
                        for value in row_data.values():
                            if value:
                                # Course codes (alphanumeric with letters and numbers)
                                if any(char.isalpha() for char in value) and any(char.isdigit() for char in value):
                                    is_course_row = True
                                    break
                                # Grades (numbers with possible %)
                                if any(char.isdigit() for char in value) and ('%' in value or value.replace('.', '').replace('%', '').isdigit()):
                                    is_course_row = True
                                    break
                                # Course names (Arabic or English text longer than 3 chars)
                                if len(value) > 3 and not value.isdigit():
                                    is_course_row = True
                                    break
                        
                        if is_course_row:
                            grades.append(row_data)
                            logger.info(f"✅ DEBUG: Added grade entry: {row_data}")
                        else:
                            logger.info(f"⏭️ DEBUG: Skipped row that doesn't look like course data: {row_data}")
                    else:
                        logger.info(f"⏭️ DEBUG: Skipped empty row")
            
            logger.info(f"🎉 DEBUG: Total grades parsed: {len(grades)}")
            return grades
            
        except Exception as e:
            logger.error(f"❌ DEBUG: Error extracting grades from HTML: {e}")
            return [] 