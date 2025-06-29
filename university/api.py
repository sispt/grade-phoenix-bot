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
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return "data" in data and data["data"] and data["data"]["getGUI"]
                    else:
                        return False
                        
        except Exception as e:
            logger.error(f"Error testing token: {e}")
            return False
    
    async def get_user_data(self, token: str) -> Optional[Dict[str, Any]]:
        """Get user data including grades"""
        try:
            # Get user info
            user_info = await self._get_user_info(token)
            if not user_info:
                return None
            
            # Get grades
            grades = await self._get_grades(token)
            
            # Combine data
            user_data = {
                **user_info,
                "grades": grades
            }
            
            logger.info(f"User data retrieved successfully")
            return user_data
            
        except Exception as e:
            logger.error(f"Error getting user data: {e}")
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
            
            variables = {
                "name": "homepage",
                "params": []
            }
            
            payload = {
                "query": grades_query,
                "variables": variables
            }
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "data" in data and data["data"] and data["data"]["getPage"]:
                            return self._parse_grades_from_html(data["data"]["getPage"])
                    
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting grades: {e}")
            return []
    
    def _parse_grades_from_html(self, page_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse grades from HTML response"""
        try:
            logger.info("DEBUG: Starting HTML parsing")
            grades = []
            
            if "panels" in page_data:
                logger.info(f"DEBUG: Found {len(page_data['panels'])} panels")
                for panel in page_data["panels"]:
                    if "blocks" in panel:
                        logger.info(f"DEBUG: Found {len(panel['blocks'])} blocks in panel")
                        for block in panel["blocks"]:
                            logger.info(f"DEBUG: Processing block with title: {block.get('title', 'No title')}")
                            # Look specifically for the student card block like in beehouse
                            if block.get("title") == "بطاقة الطالب":
                                logger.info("DEBUG: Found student card block!")
                                # Parse grades from HTML body
                                html_body = block.get("body", "")
                                if html_body:
                                    logger.info(f"DEBUG: HTML body length: {len(html_body)}")
                                    parsed_grades = self._extract_grades_from_html(html_body)
                                    grades.extend(parsed_grades)
                                    logger.info(f"DEBUG: Found {len(parsed_grades)} grades in student card")
                                else:
                                    logger.warning("DEBUG: No HTML body in student card block")
                                break  # Found the student card, no need to continue
                        if grades:
                            break  # Found grades, no need to continue
            else:
                logger.warning("DEBUG: No panels found in page data")
            
            logger.info(f"Parsed {len(grades)} grades from HTML")
            return grades
            
        except Exception as e:
            logger.error(f"Error parsing grades from HTML: {e}")
            return []
    
    def _extract_grades_from_html(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract grades from HTML content"""
        try:
            logger.info("DEBUG: Starting HTML table parsing")
            grades = []
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for ant-table structure
            table = soup.find("table")
            if not table:
                logger.warning("DEBUG: No table found in HTML")
                return []
            
            logger.info("DEBUG: Found table, parsing ant-table structure")
            
            # Find thead to get headers
            thead = table.find("thead", class_="ant-table-thead")
            if not thead:
                logger.warning("DEBUG: No thead found")
                return []
            
            # Extract headers from th elements
            headers = []
            for th in thead.find_all("th", class_="ant-table-cell"):
                header_text = th.get_text(strip=True)
                if header_text:  # Only add non-empty headers
                    headers.append(header_text)
                    logger.info(f"DEBUG: Found header: {header_text}")
            
            if not headers:
                logger.warning("DEBUG: No valid headers found")
                return []
            
            logger.info(f"DEBUG: Table headers: {headers}")
            
            # Find tbody to get rows
            tbody = table.find("tbody", class_="ant-table-tbody")
            if not tbody:
                logger.warning("DEBUG: No tbody found")
                return []
            
            # Parse each row
            for row in tbody.find_all("tr"):
                cells = row.find_all("td", class_="ant-table-cell")
                if len(cells) != len(headers):
                    logger.warning(f"DEBUG: Row has {len(cells)} cells but {len(headers)} headers, skipping")
                    continue
                
                # Extract data from each cell
                row_data = {}
                valid_row = False
                
                for i, cell in enumerate(cells):
                    cell_text = cell.get_text(strip=True)
                    row_data[headers[i]] = cell_text
                    logger.info(f"DEBUG: Cell {i} ({headers[i]}): {cell_text}")
                    
                    # Check if this row has any meaningful data
                    if cell_text and cell_text != "":
                        valid_row = True
                
                # Only add courses that have some meaningful data
                if valid_row:
                    grades.append(row_data)
                    logger.info(f"DEBUG: Added grade entry: {row_data}")
                else:
                    logger.info(f"DEBUG: Skipped empty grade entry: {row_data}")
            
            logger.info(f"DEBUG: Total grades parsed: {len(grades)}")
            return grades
            
        except Exception as e:
            logger.error(f"Error extracting grades from HTML: {e}")
            return [] 