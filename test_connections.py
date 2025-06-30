import requests
import json
import getpass
from pprint import pprint
from bs4 import BeautifulSoup

# --- CONFIGURATION (Based on our final, correct setup) ---

# Note: We use the /portal URL for login, but /graphql for data fetching.
LOGIN_URL = "https://api.staging.sis.shamuniversity.com/portal"
API_URL = "https://api.staging.sis.shamuniversity.com/graphql"

# These are the headers that make the request look like a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "x-lang": "ar",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://staging.sis.shamuniversity.com",
    "Referer": "https://staging.sis.shamuniversity.com/",
}

# --- GRAPHQL QUERIES ---

LOGIN_MUTATION = """
mutation signinUser($username: String!, $password: String!) {
    login(username: $username, password: $password)
}
"""

GET_GRADES_QUERY = """
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

def get_token(username, password):
    """Attempts to log in and retrieve an authentication token."""
    print(f"\n[1] Attempting to log in as {username} at {LOGIN_URL}...")
    
    login_payload = {
        "operationName": "signinUser",
        "variables": {"username": username, "password": password},
        "query": LOGIN_MUTATION
    }
    
    try:
        response = requests.post(LOGIN_URL, headers=HEADERS, json=login_payload, timeout=20)
        
        print(f"    -> Login Response Status: {response.status_code}")
        
        if response.status_code != 200 or not response.text.strip():
            print(f"    -> ERROR: Failed to log in. Server sent status {response.status_code} with response: {response.text[:200]}")
            return None
            
        data = response.json()
        token = data.get("data", {}).get("login")
        
        if token:
            print("    -> SUCCESS: Login successful, token received.")
            return token
        else:
            print(f"    -> ERROR: Login failed. Response did not contain a token. Errors: {data.get('errors')}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"    -> FATAL ERROR: A network error occurred: {e}")
        return None
    except json.JSONDecodeError:
        print(f"    -> FATAL ERROR: Server returned an invalid JSON response. Raw text: {response.text[:200]}")
        return None

def fetch_grades(token):
    """Uses the token to fetch the grades page."""
    print(f"\n[2] Fetching grades page from {API_URL}...")
    
    # Add the Authorization header for this request
    headers_with_token = HEADERS.copy()
    headers_with_token['Authorization'] = f"Bearer {token}"
    
    grades_payload = {
        "operationName": "getPage",
        "variables": {
            "name": "test_student_tracks",
            "params": [{"name": "t_grade_id", "value": "10459"}] # Using ID from HAR log
        },
        "query": GET_GRADES_QUERY
    }
    
    try:
        response = requests.post(API_URL, headers=headers_with_token, json=grades_payload, timeout=20)
        
        print(f"    -> Grades Page Response Status: {response.status_code}")
        print("-" * 50)
        print("RAW RESPONSE TEXT:")
        print(response.text)
        print("-" * 50)
        
        if not response.text.strip():
            print("\n    -> RESULT: The server returned an EMPTY response for the grades page.")
            return

        # Try to parse and display the structured data
        try:
            data = response.json()
            print("\nSTRUCTURED JSON RESPONSE:")
            pprint(data)
            
            # Extract the HTML body with the grades table
            html_body = data['data']['getPage']['panels'][0]['blocks'][1]['body']
            soup = BeautifulSoup(html_body, 'html.parser')
            table = soup.find('table')
            
            if table:
                print("\n" + "="*20 + " PARSED GRADES TABLE " + "="*20)
                for row in table.find_all('tr'):
                    headers = [th.get_text(strip=True) for th in row.find_all('th')]
                    if headers:
                        print(" | ".join(headers))
                        print("-" * (len(" | ".join(headers)) + 5))
                    
                    cells = [td.get_text(strip=True) for td in row.find_all('td')]
                    if cells:
                        print(" | ".join(cells))
                print("=" * (len(" PARSED GRADES TABLE ") + 42))

        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"\n    -> Could not fully parse the response. This might be an error page. Error: {e}")

    except requests.exceptions.RequestException as e:
        print(f"    -> FATAL ERROR: A network error occurred while fetching grades: {e}")

if __name__ == "__main__":
    print("--- University API Connection Test Script ---")
    username = input("Enter university username: ")
    password = getpass.getpass("Enter university password: ")

    auth_token = get_token(username, password)

    if auth_token:
        fetch_grades(auth_token)
    else:
        print("\n[!] Could not proceed to fetch grades due to login failure.")
    
    print("\n--- Script finished ---")