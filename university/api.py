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
        """Login to university system using GraphQL mutation"""
        max_retries = CONFIG.get("MAX_RETRY_ATTEMPTS", 3)
        
        for attempt in range(max_retries):
            try:
                logger.info(f"DEBUG: Login attempt {attempt + 1}/{max_retries} for user {username}")
                
                # Validate inputs
                if not username or not password:
                    logger.warning(f"DEBUG: Invalid credentials for user {username}")
                    return None
                
                # GraphQL mutation payload - using proper GraphQL structure
                payload = {
                    "operationName": "signinUser",
                    "variables": {
                        "username": username,
                        "password": password
                    },
                    "query": CONFIG["UNIVERSITY_QUERIES"]["LOGIN"]
                }
                
                logger.info(f"DEBUG: Making GraphQL login request to {self.login_url}")
                logger.info(f"DEBUG: Request method: POST")
                logger.info(f"DEBUG: Request URL: {self.login_url}")
                logger.info(f"DEBUG: Payload: {payload}")
                logger.info(f"DEBUG: Headers: {self.api_headers}")
                
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(
                        self.login_url,
                        headers=self.api_headers,
                        json=payload
                    ) as response:
                        logger.info(f"DEBUG: Login response status: {response.status}")
                        logger.info(f"DEBUG: Response headers: {dict(response.headers)}")
                        logger.info(f"DEBUG: Response URL: {response.url}")
                        
                        # Get response content type
                        content_type = response.headers.get('Content-Type', '')
                        logger.info(f"DEBUG: Content-Type: {content_type}")
                        
                        # ALWAYS capture the complete response body for debugging
                        try:
                            response_text = await response.text()
                            logger.info(f"🔍 DEBUG: COMPLETE RESPONSE BODY:")
                            logger.info(f"🔍 DEBUG: Response length: {len(response_text)} characters")
                            logger.info(f"🔍 DEBUG: Raw response text (first 2000 chars): {response_text[:2000]}")
                            if len(response_text) > 2000:
                                logger.info(f"🔍 DEBUG: Response text (chars 2000-4000): {response_text[2000:4000]}")
                            if len(response_text) > 4000:
                                logger.info(f"🔍 DEBUG: Response text (chars 4000-6000): {response_text[4000:6000]}")
                            logger.info(f"🔍 DEBUG: Full response text: {response_text}")
                        except Exception as read_error:
                            logger.error(f"❌ DEBUG: Failed to read response body: {read_error}")
                            response_text = ""
                        
                        if response.status == 200:
                            try:
                                # Check if response is JSON
                                if 'application/json' not in content_type.lower():
                                    logger.error(f"DEBUG: Expected JSON but got {content_type}. Response: {response_text[:500]}")
                                    logger.error(f"DEBUG: Full response text: {response_text}")
                                    
                                    # If it's HTML, it might be an error page
                                    if 'text/html' in content_type.lower():
                                        logger.error(f"DEBUG: Server returned HTML instead of JSON. This might indicate:")
                                        logger.error(f"DEBUG: 1. Wrong URL endpoint")
                                        logger.error(f"DEBUG: 2. Server error")
                                        logger.error(f"DEBUG: 3. Authentication required")
                                        logger.error(f"DEBUG: 4. CORS issue")
                                        logger.error(f"DEBUG: 5. Wrong HTTP method")
                                    
                                    if attempt < max_retries - 1:
                                        await asyncio.sleep(2 ** attempt)
                                        continue
                                    return None
                                
                                # Parse JSON from the text we already read
                                data = json.loads(response_text)
                                logger.info(f"DEBUG: Login response data: {data}")
                                logger.info(f"DEBUG: Full response: {data}")
                                
                                # Extract token from GraphQL response - matching BeeHouse v2.1 structure
                                token = data.get("data", {}).get("login")
                                if token:
                                    logger.info(f"✅ Login successful for user: {username}")
                                    logger.info(f"✅ Token obtained: {token[:20]}...")
                                    return token
                                else:
                                    logger.warning(f"❌ Login failed for user: {username} - no token in response")
                                    logger.warning(f"❌ DEBUG: Response data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                                    if "errors" in data:
                                        logger.warning(f"❌ DEBUG: GraphQL errors: {data['errors']}")
                                    return None
                            except json.JSONDecodeError as json_error:
                                logger.error(f"DEBUG: JSON decode error: {json_error}")
                                logger.error(f"DEBUG: Response text: {response_text[:500]}")
                                if attempt < max_retries - 1:
                                    await asyncio.sleep(2 ** attempt)
                                    continue
                                return None
                        elif response.status == 401:
                            logger.error(f"❌ Login failed for user: {username} - invalid credentials")
                            logger.error(f"❌ DEBUG: 401 Response body: {response_text}")
                            return None
                        elif response.status == 429:
                            logger.warning(f"⚠️ Rate limited for user {username}, retrying...")
                            logger.warning(f"⚠️ DEBUG: 429 Response body: {response_text}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(2 ** attempt)
                                continue
                            return None
                        elif response.status == 404:
                            logger.error(f"❌ Login endpoint not found: {self.login_url}")
                            logger.error(f"❌ DEBUG: 404 Response body: {response_text}")
                            return None
                        elif response.status == 403:
                            logger.error(f"❌ Login forbidden for user: {username}")
                            logger.error(f"❌ DEBUG: 403 Response body: {response_text}")
                            return None
                        elif response.status == 500:
                            logger.error(f"❌ Server error during login for user: {username}")
                            logger.error(f"❌ DEBUG: 500 Response body: {response_text}")
                            if attempt < max_retries - 1:
                                await asyncio.sleep(2 ** attempt)
                                continue
                            return None
                        else:
                            logger.error(f"❌ Login request failed with status: {response.status}")
                            logger.error(f"❌ DEBUG: {response.status} Response body: {response_text}")
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
        """Test if token is still valid using GraphQL query"""
        try:
            logger.info(f"🔍 DEBUG: Testing token validity...")
            test_query = """
            {
              getGUI {
                user {
                  id
                  username
                  email
                  fullname
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
                        logger.info(f"📄 DEBUG: Full token test response: {data}")
                        
                        # Check for GraphQL errors
                        if "errors" in data:
                            logger.warning(f"❌ DEBUG: GraphQL errors in token test: {data['errors']}")
                            return False
                        
                        is_valid = "data" in data and data["data"] and data["data"]["getGUI"] and data["data"]["getGUI"]["user"]
                        logger.info(f"✅ DEBUG: Token is {'valid' if is_valid else 'invalid'}")
                        return is_valid
                    else:
                        logger.warning(f"❌ DEBUG: Token test failed with status: {response.status}")
                        try:
                            error_text = await response.text()
                            logger.warning(f"❌ DEBUG: Token test error response: {error_text}")
                        except:
                            pass
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
                        logger.info(f"📄 DEBUG: User info response data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                        logger.info(f"📄 DEBUG: Full user info response: {data}")
                        
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
                        else:
                            logger.error(f"❌ DEBUG: Invalid user info response structure")
                            return None
                    else:
                        logger.error(f"❌ DEBUG: User info request failed with status: {response.status}")
                        return None
                    
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    async def _get_grades(self, token: str) -> List[Dict[str, Any]]:
        """Get user grades from GraphQL endpoint"""
        try:
            logger.info(f"🔍 DEBUG: Starting grade fetch with token...")
            
            # First get homepage to get available terms
            homepage_data = await self._get_homepage(token)
            if not homepage_data:
                logger.error(f"❌ DEBUG: Failed to get homepage data")
                return []
            
            # Extract terms from homepage
            terms = self._extract_terms_from_homepage(homepage_data)
            logger.info(f"📚 DEBUG: Found {len(terms)} terms: {terms}")
            
            all_grades = []
            
            # Get grades for each term
            for term in terms:
                logger.info(f"📊 DEBUG: Getting grades for term: {term}")
                term_grades = await self._get_term_grades(token, term)
                if term_grades:
                    all_grades.extend(term_grades)
                    logger.info(f"✅ DEBUG: Got {len(term_grades)} grades for term {term}")
                else:
                    logger.warning(f"⚠️ DEBUG: No grades found for term {term}")
            
            logger.info(f"🎉 DEBUG: Total grades retrieved: {len(all_grades)}")
            return all_grades
            
        except Exception as e:
            logger.error(f"❌ DEBUG: Error getting grades: {e}")
            return []
    
    async def _get_homepage(self, token: str) -> Optional[Dict[str, Any]]:
        """Get homepage data to extract terms"""
        try:
            logger.info(f"🏠 DEBUG: Getting homepage data...")
            
            homepage_query = """
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
            
            payload = {
                "query": homepage_query,
                "variables": {
                    "name": "homepage",
                    "params": []
                }
            }
            
            logger.info(f"🌐 DEBUG: Making homepage request to {self.api_url}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                ) as response:
                    logger.info(f"📡 DEBUG: Homepage response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"📄 DEBUG: Homepage response data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                        logger.info(f"📄 DEBUG: Full homepage response: {data}")
                        
                        # Check for GraphQL errors
                        if "errors" in data:
                            logger.error(f"❌ DEBUG: GraphQL errors in homepage request: {data['errors']}")
                            return None
                        
                        if "data" in data and data["data"] and data["data"]["getPage"]:
                            return data["data"]["getPage"]
                        else:
                            logger.error(f"❌ DEBUG: Invalid homepage response structure")
                            logger.error(f"❌ DEBUG: Expected 'data.getPage' but got: {data}")
                            return None
                    else:
                        logger.error(f"❌ DEBUG: Homepage request failed with status: {response.status}")
                        try:
                            error_text = await response.text()
                            logger.error(f"❌ DEBUG: Homepage error response: {error_text}")
                        except:
                            pass
                        return None
                        
        except Exception as e:
            logger.error(f"❌ DEBUG: Error getting homepage: {e}")
            return None
    
    def _extract_terms_from_homepage(self, homepage_data: Dict[str, Any]) -> List[str]:
        """Extract available terms from homepage data"""
        try:
            logger.info(f"🔍 DEBUG: Extracting terms from homepage...")
            terms = []
            
            if not homepage_data or "panels" not in homepage_data:
                logger.warning(f"❌ DEBUG: No panels found in homepage data")
                return []
            
            for panel in homepage_data["panels"]:
                if "blocks" not in panel:
                    continue
                
                for block in panel["blocks"]:
                    body = block.get("body", "")
                    if not body:
                        continue
                    
                    # Look for term tabs in the HTML
                    soup = BeautifulSoup(body, 'html.parser')
                    
                    # Look for tabs or buttons that might contain term information
                    tabs = soup.find_all(['button', 'a', 'div'], class_=lambda x: x and ('tab' in x.lower() or 'term' in x.lower()))
                    
                    for tab in tabs:
                        tab_text = tab.get_text(strip=True)
                        if tab_text and any(keyword in tab_text.lower() for keyword in ['فصل', 'semester', 'term']):
                            # Extract t_grade_id from data attributes or href
                            t_grade_id = tab.get('data-id') or tab.get('href', '').split('=')[-1]
                            if t_grade_id:
                                terms.append(t_grade_id)
                                logger.info(f"📚 DEBUG: Found term: {tab_text} (ID: {t_grade_id})")
            
            # If no terms found, try a default term
            if not terms:
                logger.warning(f"⚠️ DEBUG: No terms found, using default")
                terms = ["1"]  # Default to first term
            
            logger.info(f"📚 DEBUG: Extracted terms: {terms}")
            return terms
            
        except Exception as e:
            logger.error(f"❌ DEBUG: Error extracting terms: {e}")
            return ["1"]  # Default fallback
    
    async def _get_term_grades(self, token: str, t_grade_id: str) -> List[Dict[str, Any]]:
        """Get grades for a specific term"""
        try:
            logger.info(f"📊 DEBUG: Getting grades for term {t_grade_id}...")
            
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
            
            payload = {
                "query": grades_query,
                "variables": {
                    "name": "test_student_tracks",
                    "params": [
                        {
                            "name": "t_grade_id",
                            "value": t_grade_id
                        }
                    ]
                }
            }
            
            logger.info(f"🌐 DEBUG: Making grades request to {self.api_url}")
            logger.info(f"📡 DEBUG: Request payload: {payload}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                ) as response:
                    logger.info(f"📡 DEBUG: Grades response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"📄 DEBUG: Grades response data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                        logger.info(f"📄 DEBUG: Full grades response: {data}")
                        
                        # Check for GraphQL errors
                        if "errors" in data:
                            logger.error(f"❌ DEBUG: GraphQL errors in grades request: {data['errors']}")
                            return []
                        
                        if "data" in data and data["data"] and data["data"]["getPage"]:
                            page_content = data["data"]["getPage"]
                            logger.info(f"✅ DEBUG: Got grades page content")
                            
                            # Parse grades from the page content
                            grades = self._parse_grades_from_graphql(page_content)
                            logger.info(f"🎉 DEBUG: Parsed {len(grades)} grades for term {t_grade_id}")
                            return grades
                        else:
                            logger.error(f"❌ DEBUG: Invalid grades response structure")
                            logger.error(f"❌ DEBUG: Expected 'data.getPage' but got: {data}")
                            return []
                    else:
                        logger.error(f"❌ DEBUG: Grades request failed with status: {response.status}")
                        try:
                            error_text = await response.text()
                            logger.error(f"❌ DEBUG: Error response: {error_text}")
                        except:
                            logger.error(f"❌ DEBUG: Could not read error response")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ DEBUG: Error getting term grades: {e}")
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
            
            # Find all tables
            tables = soup.find_all('table')
            if not tables:
                logger.error("❌ DEBUG: No tables found in HTML")
                return []
            
            logger.info(f"📋 DEBUG: Found {len(tables)} tables in HTML")
            
            for table_idx, table in enumerate(tables):
                logger.info(f"📋 DEBUG: Processing table {table_idx + 1}")
                
                # Find thead to get headers
                thead = table.find('thead')
                if not thead:
                    logger.info(f"❌ DEBUG: No thead found in table {table_idx + 1}")
                    continue
                
                # Extract headers
                headers = []
                for th in thead.find_all('th'):
                    header_text = th.get_text(strip=True)
                    if header_text:
                        headers.append(header_text)
                        logger.info(f"📋 DEBUG: Found header: {header_text}")
                
                if not headers:
                    logger.info(f"❌ DEBUG: No headers found in table {table_idx + 1}")
                    continue
                
                logger.info(f"📋 DEBUG: Table {table_idx + 1} headers: {headers}")
                
                # Check if this table contains course data
                course_indicators = ['مقرر', 'كود', 'درجة', 'رصيد', 'course', 'code', 'grade', 'credit']
                has_course_data = any(any(indicator in header for indicator in course_indicators) for header in headers)
                
                if not has_course_data:
                    logger.info(f"⏭️ DEBUG: Table {table_idx + 1} does not contain course data")
                    continue
                
                # Find tbody to get rows
                tbody = table.find('tbody')
                if not tbody:
                    logger.info(f"❌ DEBUG: No tbody found in table {table_idx + 1}")
                    continue
                
                rows = tbody.find_all('tr')
                logger.info(f"📋 DEBUG: Found {len(rows)} rows in table {table_idx + 1}")
                
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
                    
                    # Convert to standard format based on actual headers
                    grade_entry = {}
                    
                    # Map headers to standard fields
                    for header, value in row_data.items():
                        if 'مقرر' in header or 'course' in header.lower():
                            grade_entry["name"] = value
                        elif 'كود' in header or 'code' in header.lower():
                            grade_entry["code"] = value
                        elif 'رصيد' in header or 'ects' in header.lower() or 'credit' in header.lower():
                            grade_entry["ects"] = value
                        elif 'أعمال' in header or 'activity' in header.lower() or 'coursework' in header.lower():
                            grade_entry["coursework"] = value
                        elif 'نظري' in header or 'theoretical' in header.lower() or 'exam' in header.lower():
                            grade_entry["final_exam"] = value
                        elif 'الدرجة' in header or 'total' in header.lower() or 'grade' in header.lower():
                            grade_entry["total"] = value
                        else:
                            # Store unknown headers as-is
                            grade_entry[header] = value
                    
                    # Only add if we have meaningful data
                    if grade_entry.get("name") and grade_entry.get("code"):
                        grades.append(grade_entry)
                        logger.info(f"✅ DEBUG: Added grade: {grade_entry}")
                    else:
                        logger.info(f"⏭️ DEBUG: Skipped row with insufficient data: {row_data}")
            
            logger.info(f"🎉 DEBUG: Parsed {len(grades)} grades from all tables")
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
    
    def extract_grades_from_html_file(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Extract grades from HTML content using flexible parsing
        Works with any HTML structure containing grades tables
        """
        try:
            logger.info("🔍 Starting flexible HTML grades extraction...")
            soup = BeautifulSoup(html_content, "html.parser")
            all_tables = soup.find_all("table")
            extracted_grades = []

            logger.info(f"📊 Found {len(all_tables)} tables in HTML")

            for table_index, table in enumerate(all_tables):
                headers = [th.text.strip() for th in table.find_all("th")]
                
                # Flexible detection: consider it a grades table if it has at least 2 grade-related keywords
                grade_keywords = ["المقرر", "كود المادة", "الدرجة", "ECTS", "أعمال", "نظري", "course", "code", "grade"]
                grade_keyword_count = sum(any(kw in h for kw in grade_keywords) for h in headers)
                
                if grade_keyword_count >= 2:
                    logger.info(f"✅ Table {table_index + 1}: Found grades table with {grade_keyword_count} grade keywords")
                    logger.info(f"📋 Headers: {headers}")
                    
                    rows = table.find_all("tr")[1:]  # Skip header row
                    logger.info(f"📝 Processing {len(rows)} data rows")
                    
                    for row_index, row in enumerate(rows):
                        cells = [td.text.strip() for td in row.find_all("td")]
                        
                        if cells and len(cells) == len(headers):
                            # Create grade record with header mapping
                            grade_record = dict(zip(headers, cells))
                            
                            # Only add if it has meaningful course data
                            if any(grade_record.get(h) for h in headers if any(kw in h for kw in ["المقرر", "course", "كود المادة", "code"])):
                                extracted_grades.append(grade_record)
                                logger.info(f"✅ Added grade record {row_index + 1}: {grade_record.get('المقرر', 'N/A')} ({grade_record.get('كود المادة', 'N/A')})")
                            else:
                                logger.info(f"⚠️ Skipped row {row_index + 1}: No meaningful course data")
                        else:
                            logger.warning(f"⚠️ Row {row_index + 1}: Cell count mismatch ({len(cells)} vs {len(headers)})")
                else:
                    logger.info(f"ℹ️ Table {table_index + 1}: Not a grades table (only {grade_keyword_count} grade keywords)")

            logger.info(f"🎉 HTML extraction complete: {len(extracted_grades)} grade records found")
            return extracted_grades

        except Exception as e:
            logger.error(f"❌ Error extracting grades from HTML: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return []

    def parse_html_grades_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse grades from a saved HTML file
        """
        try:
            logger.info(f"📁 Reading HTML file: {file_path}")
            with open(file_path, encoding="utf-8") as f:
                html_content = f.read()
            
            logger.info(f"📄 HTML file loaded: {len(html_content)} characters")
            return self.extract_grades_from_html_file(html_content)
            
        except FileNotFoundError:
            logger.error(f"❌ HTML file not found: {file_path}")
            return []
        except Exception as e:
            logger.error(f"❌ Error reading HTML file {file_path}: {e}")
            return [] 