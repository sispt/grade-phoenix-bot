import asyncio
import aiohttp
import json
from datetime import datetime

LOGIN_URL = "https://api.staging.sis.shamuniversity.com/portal"
GRAPHQL_URL = "https://api.staging.sis.shamuniversity.com/graphql"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "x-lang": "ar",
    "Accept": "application/json",
    "Origin": "https://api.staging.sis.shamuniversity.com",
    "Referer": "https://api.staging.sis.shamuniversity.com"
}

USERNAME = "ENG2425041"
PASSWORD = "0951202512"

LOGIN_PAYLOAD = {
    "operationName": "signinUser",
    "variables": {
        "username": USERNAME,
        "password": PASSWORD
    },
    "query": """
        mutation signinUser($username: String!, $password: String!) {
            login(username: $username, password: $password)
        }
    """
}

# Comprehensive list of possible page names and queries
API_TESTS = [
    # Test different page names
    {
        "name": "final_courses_grades_page",
        "query": """
        query getPage($name: String!) {
          getPage(name: $name) {
            panels {
              blocks {
                title
                body
              }
            }
          }
        }
        """,
        "variables": {"name": "final_courses_grades_page"}
    },
    {
        "name": "student_academic_record",
        "query": """
        query getPage($name: String!) {
          getPage(name: $name) {
            panels {
              blocks {
                title
                body
              }
            }
          }
        }
        """,
        "variables": {"name": "student_academic_record"}
    },
    {
        "name": "academic_record",
        "query": """
        query getPage($name: String!) {
          getPage(name: $name) {
            panels {
              blocks {
                title
                body
              }
            }
          }
        }
        """,
        "variables": {"name": "academic_record"}
    },
    {
        "name": "student_grades_detailed",
        "query": """
        query getPage($name: String!) {
          getPage(name: $name) {
            panels {
              blocks {
                title
                body
              }
            }
          }
        }
        """,
        "variables": {"name": "student_grades_detailed"}
    },
    # Test with different parameters
    {
        "name": "test_student_tracks_with_student_id",
        "query": """
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
        """,
        "variables": {
            "name": "test_student_tracks",
            "params": [
                {"name": "student_id", "value": "ENG2425041"},
                {"name": "t_grade_id", "value": "1"}
            ]
        }
    },
    {
        "name": "student_grades_with_student_id",
        "query": """
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
        """,
        "variables": {
            "name": "student_grades",
            "params": [
                {"name": "student_id", "value": "ENG2425041"}
            ]
        }
    },
    # Test different term IDs
    {
        "name": "test_student_tracks_term_2",
        "query": """
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
        """,
        "variables": {
            "name": "test_student_tracks",
            "params": [
                {"name": "t_grade_id", "value": "2"}
            ]
        }
    },
    # Test REST-like endpoints
    {
        "name": "grades_rest_endpoint",
        "method": "GET",
        "url": "https://api.staging.sis.shamuniversity.com/grades",
        "headers": {"Authorization": "Bearer {token}"}
    },
    {
        "name": "student_grades_rest",
        "method": "GET", 
        "url": "https://api.staging.sis.shamuniversity.com/student/grades",
        "headers": {"Authorization": "Bearer {token}"}
    }
]

def check_for_detailed_grades(data):
    """Check if response contains detailed grades table"""
    if not isinstance(data, dict):
        return False
    
    # Check GraphQL response
    if "data" in data and data["data"]:
        page_data = data["data"].get("getPage")
        if page_data and "panels" in page_data:
            for panel in page_data["panels"]:
                for block in panel.get("blocks", []):
                    body = block.get("body", "")
                    if body and "المقرر" in body and "كود المادة" in body and "درجة الأعمال" in body:
                        return True
    
    # Check REST response
    if isinstance(data, list) or (isinstance(data, dict) and "grades" in data):
        return True
    
    return False

async def test_api_endpoint(session, token, test_info):
    """Test a single API endpoint"""
    print(f"🔍 Testing: {test_info['name']}")
    
    try:
        if test_info.get("method") == "GET":
            # REST endpoint test
            url = test_info["url"].format(token=token)
            headers = {**HEADERS, "Authorization": f"Bearer {token}"}
            async with session.get(url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if check_for_detailed_grades(data):
                        print(f"✅ Found detailed grades in REST endpoint!")
                        return True
                else:
                    print(f"❌ REST endpoint failed: {resp.status}")
                    return False
        else:
            # GraphQL endpoint test
            payload = {
                "query": test_info["query"],
                "variables": test_info["variables"]
            }
            headers_with_token = {**HEADERS, "Authorization": f"Bearer {token}"}
            
            async with session.post(GRAPHQL_URL, json=payload, headers=headers_with_token) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    # Save response for analysis
                    filename = f"api_test_{test_info['name']}.json"
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
                    if check_for_detailed_grades(data):
                        print(f"✅ Found detailed grades in GraphQL!")
                        return True
                    else:
                        print(f"❌ No detailed grades found")
                        return False
                else:
                    print(f"❌ GraphQL failed: {resp.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error testing {test_info['name']}: {e}")
        return False

async def main():
    print("🧪 Comprehensive API Test for Detailed Grades")
    print("=" * 60)
    print(f"⏰ {datetime.now()}\n")
    
    async with aiohttp.ClientSession() as session:
        # Login first
        print("🔐 Logging in...")
        async with session.post(LOGIN_URL, json=LOGIN_PAYLOAD, headers=HEADERS) as login_resp:
            login_data = await login_resp.json()
            token = login_data.get("data", {}).get("login")
            if not token:
                print("❌ Login failed.")
                return
            print("✅ Login successful!\n")
        
        # Test all endpoints
        found_grades = False
        for test_info in API_TESTS:
            success = await test_api_endpoint(session, token, test_info)
            if success:
                found_grades = True
                print(f"🎉 SUCCESS: {test_info['name']} contains detailed grades!")
                print(f"💾 Response saved to api_test_{test_info['name']}.json")
                break
            print()
        
        if not found_grades:
            print("❌ No detailed grades found in any API endpoint.")
            print("💡 This means the API does not provide detailed grades data.")
            print("💡 You may need to:")
            print("   1. Contact the university for API access")
            print("   2. Use alternative methods (HTML parsing, etc.)")
            print("   3. Wait for system updates")

if __name__ == "__main__":
    asyncio.run(main()) 