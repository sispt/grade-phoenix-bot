import asyncio
import aiohttp
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
PASSWORD = "0951202512"  # use a likely guess if you want to test success

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

GRAPHQL_PAYLOAD = {
    "query": """
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
}

async def test_login_and_query():
    print("🔐 [1] Attempting Login...")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(LOGIN_URL, json=LOGIN_PAYLOAD, headers=HEADERS) as login_resp:
                login_data = await login_resp.json()
                print(f"\n[🔁] Login Status: {login_resp.status}")
                print(f"[📄] Login Response: {login_data}\n")

                token = login_data.get("data", {}).get("login")
                if not token:
                    print("❌ Login failed or unauthorized.")
                    return

                print("✅ Login successful. Token obtained.")
                print("📡 [2] Sending GraphQL request with token...")

                # Add auth header and send graphql query
                headers_with_token = HEADERS.copy()
                headers_with_token["Authorization"] = f"Bearer {token}"

                async with session.post(GRAPHQL_URL, json=GRAPHQL_PAYLOAD, headers=headers_with_token) as gql_resp:
                    gql_data = await gql_resp.json()
                    print(f"\n[🔁] GraphQL Status: {gql_resp.status}")
                    print(f"[📄] GraphQL Response:\n{gql_data}")

        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Starting full login + GraphQL test")
    print("=" * 60)
    print(f"⏰ {datetime.now()}\n")
    asyncio.run(test_login_and_query())
