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
        try:
            logger.info(f"DEBUG: Attempting login to {self.login_url}")
            
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
                    else:
                        logger.error(f"Login request failed with status: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error during login for user {username}: {e}")
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
            grades = []
            
            if "panels" in page_data:
                for panel in page_data["panels"]:
                    if "blocks" in panel:
                        for block in panel["blocks"]:
                            if block.get("title") and "grade" in block.get("title", "").lower():
                                # Parse grades from HTML body
                                html_body = block.get("body", "")
                                if html_body:
                                    parsed_grades = self._extract_grades_from_html(html_body)
                                    grades.extend(parsed_grades)
            
            logger.info(f"Parsed {len(grades)} grades from HTML")
            return grades
            
        except Exception as e:
            logger.error(f"Error parsing grades from HTML: {e}")
            return []
    
    def _extract_grades_from_html(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract grades from HTML content"""
        try:
            grades = []
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for table rows or div elements containing grade information
            # This is a simplified parser - you may need to adjust based on actual HTML structure
            rows = soup.find_all(['tr', 'div'])
            
            for row in rows:
                text = row.get_text().strip()
                if any(keyword in text.lower() for keyword in ['course', 'grade', 'practical', 'theoretical']):
                    # Extract course information
                    course_info = self._extract_course_info(row)
                    if course_info:
                        grades.append(course_info)
            
            return grades
            
        except Exception as e:
            logger.error(f"Error extracting grades from HTML: {e}")
            return []
    
    def _extract_course_info(self, element) -> Optional[Dict[str, Any]]:
        """Extract course information from HTML element"""
        try:
            text = element.get_text().strip()
            
            # This is a simplified extraction - adjust based on actual HTML structure
            # You may need to implement more sophisticated parsing based on the actual university system
            
            # Example parsing (adjust as needed):
            lines = text.split('\n')
            course_name = ""
            practical_grade = ""
            theoretical_grade = ""
            final_grade = ""
            
            for line in lines:
                line = line.strip()
                if line and len(line) > 3:
                    if not course_name and any(keyword in line.lower() for keyword in ['course', 'subject']):
                        course_name = line
                    elif any(char.isdigit() for char in line) and len(line) <= 10:
                        # This might be a grade
                        if not practical_grade:
                            practical_grade = line
                        elif not theoretical_grade:
                            theoretical_grade = line
                        elif not final_grade:
                            final_grade = line
            
            if course_name:
                return {
                    "course_name": course_name,
                    "practical_grade": practical_grade,
                    "theoretical_grade": theoretical_grade,
                    "final_grade": final_grade
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting course info: {e}")
            return None 