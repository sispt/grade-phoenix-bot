"""
University API Client Integration
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

    async def test_token(self, token: str) -> bool:
        try:
            headers = {**self.api_headers, "Authorization": f"Bearer {token}"}
            payload = {"query": UNIVERSITY_QUERIES["TEST_TOKEN"]}
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("data", {}).get("me") is not None
            return False
        except Exception as e:
            logger.error(f"Error testing token: {e}")
            return False

    async def get_user_data(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            headers = {**self.api_headers, "Authorization": f"Bearer {token}"}
            payload = {"query": UNIVERSITY_QUERIES["GET_USER_DATA"]}
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_user_data(data)
            return None
        except Exception as e:
            logger.error(f"Error getting user data: {e}")
            return None

    async def get_old_grades(self, token: str) -> Optional[List[Dict[str, Any]]]:
        try:
            headers = {**self.api_headers, "Authorization": f"Bearer {token}"}
            payload = {"query": UNIVERSITY_QUERIES["GET_OLD_GRADES"]}
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_old_grades(data)
            return None
        except Exception as e:
            logger.error(f"Error getting old grades: {e}")
            return None

    async def _get_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            headers = {**self.api_headers, "Authorization": f"Bearer {token}"}
            payload = {"query": UNIVERSITY_QUERIES["GET_USER_INFO"]}
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_user_info(data)
            return None
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None

    def _parse_user_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            user_data = data.get("data", {}).get("me", {})
            grades = data.get("data", {}).get("grades", [])
            
            return {
                "firstname": user_data.get("firstname"),
                "lastname": user_data.get("lastname"),
                "fullname": f"{user_data.get('firstname', '')} {user_data.get('lastname', '')}".strip(),
                "email": user_data.get("email"),
                "grades": self._parse_grades(grades)
            }
        except Exception as e:
            logger.error(f"Error parsing user data: {e}")
            return {}

    def _parse_old_grades(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            old_grades = data.get("data", {}).get("oldGrades", [])
            return self._parse_grades(old_grades)
        except Exception as e:
            logger.error(f"Error parsing old grades: {e}")
            return []

    def _parse_user_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            user_info = data.get("data", {}).get("me", {})
            return {
                "firstname": user_info.get("firstname"),
                "lastname": user_info.get("lastname"),
                "fullname": f"{user_info.get('firstname', '')} {user_info.get('lastname', '')}".strip(),
                "email": user_info.get("email")
            }
        except Exception as e:
            logger.error(f"Error parsing user info: {e}")
            return {}

    def _parse_grades(self, grades_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        try:
            parsed_grades = []
            for grade in grades_data:
                parsed_grade = {
                    "name": grade.get("course", {}).get("name"),
                    "code": grade.get("course", {}).get("code"),
                    "ects": grade.get("course", {}).get("ects"),
                    "coursework": grade.get("coursework"),
                    "final_exam": grade.get("finalExam"),
                    "total": grade.get("total")
                }
                parsed_grades.append(parsed_grade)
            return parsed_grades
        except Exception as e:
            logger.error(f"Error parsing grades: {e}")
            return [] 