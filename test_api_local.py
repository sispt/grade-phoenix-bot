#!/usr/bin/env python3
"""
🔍 Standalone University API Test Script
Test the university login and API endpoints locally
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Optional, Any

# Configuration - Edit these values
CONFIG = {
    # Test URLs - Updated to use correct staging endpoints only
    "URLS_TO_TEST": [
        "https://api.staging.sis.shamuniversity.com/portal"
    ],
    
    # API Headers - Updated to match BeeHouse v2.1 exact structure
    "API_HEADERS": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Content-Type": "application/json",
        "x-lang": "ar",
        "Accept": "application/json",
        "Origin": "https://api.staging.sis.shamuniversity.com",
        "Referer": "https://api.staging.sis.shamuniversity.com",
    },
    
    "TIMEOUT": 30,
    "MAX_RETRIES": 3
}

class APITester:
    """Standalone API tester"""
    
    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=CONFIG["TIMEOUT"])
    
    async def test_endpoint(self, url: str, username: str, password: str) -> Dict[str, Any]:
        """Test a specific endpoint"""
        print(f"\n🔍 Testing URL: {url}")
        print("=" * 80)
        
        payload = {
            "username": username,
            "password": password
        }
        
        # Update headers with correct referer and origin
        headers = CONFIG["API_HEADERS"].copy()
        
        print(f"📤 Request Details:")
        print(f"   Method: POST")
        print(f"   URL: {url}")
        print(f"   Headers: {json.dumps(headers, indent=2)}")
        print(f"   Payload: {json.dumps(payload, indent=2)}")
        
        for attempt in range(CONFIG["MAX_RETRIES"]):
            try:
                print(f"\n🔄 Attempt {attempt + 1}/{CONFIG['MAX_RETRIES']}")
                
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(url, headers=headers, json=payload) as response:
                        print(f"📡 Response Status: {response.status}")
                        print(f"📡 Response Headers: {dict(response.headers)}")
                        
                        # Get response content
                        try:
                            response_text = await response.text()
                            print(f"📄 Response Length: {len(response_text)} characters")
                            print(f"📄 Raw Response (first 1000 chars): {response_text[:1000]}")
                            
                            if len(response_text) > 1000:
                                print(f"📄 Response (chars 1000-2000): {response_text[1000:2000]}")
                            
                            print(f"📄 Full Response: {response_text}")
                            
                            # Try to parse JSON
                            try:
                                if response_text.strip():
                                    data = json.loads(response_text)
                                    print(f"✅ JSON Parsed Successfully:")
                                    print(f"   {json.dumps(data, indent=2, ensure_ascii=False)}")
                                    
                                    # Check for token
                                    token = data.get("token") or data.get("access_token") or data.get("auth_token")
                                    if token:
                                        print(f"🎉 TOKEN FOUND: {token[:20]}...")
                                        return {
                                            "success": True,
                                            "url": url,
                                            "status": response.status,
                                            "token": token,
                                            "data": data
                                        }
                                    else:
                                        print(f"❌ No token found in response")
                                        print(f"   Available keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                                else:
                                    print(f"⚠️ Empty response body")
                                    
                            except json.JSONDecodeError as json_error:
                                print(f"❌ JSON Parse Error: {json_error}")
                                print(f"   Response is not valid JSON")
                                
                        except Exception as read_error:
                            print(f"❌ Failed to read response: {read_error}")
                        
                        # Check specific status codes
                        if response.status == 401:
                            print(f"❌ 401 Unauthorized - Invalid credentials")
                        elif response.status == 403:
                            print(f"❌ 403 Forbidden - Access denied")
                        elif response.status == 404:
                            print(f"❌ 404 Not Found - Wrong endpoint")
                        elif response.status == 500:
                            print(f"❌ 500 Server Error - Try again")
                        elif response.status == 200:
                            print(f"✅ 200 OK - Request successful")
                        else:
                            print(f"⚠️ Unexpected status: {response.status}")
                        
                        # If we got a 200 but no token, this might be the right endpoint but wrong format
                        if response.status == 200:
                            return {
                                "success": False,
                                "url": url,
                                "status": response.status,
                                "message": "200 OK but no token found - might need different payload format",
                                "data": response_text
                            }
                        
                        # Wait before retry
                        if attempt < CONFIG["MAX_RETRIES"] - 1:
                            wait_time = 2 ** attempt
                            print(f"⏳ Waiting {wait_time} seconds before retry...")
                            await asyncio.sleep(wait_time)
                            
            except asyncio.TimeoutError:
                print(f"⏰ Timeout error (attempt {attempt + 1})")
                if attempt < CONFIG["MAX_RETRIES"] - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
            except aiohttp.ClientError as client_error:
                print(f"🌐 Network error (attempt {attempt + 1}): {client_error}")
                if attempt < CONFIG["MAX_RETRIES"] - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
            except Exception as e:
                print(f"❌ Unexpected error (attempt {attempt + 1}): {e}")
                if attempt < CONFIG["MAX_RETRIES"] - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
        
        return {
            "success": False,
            "url": url,
            "message": "All attempts failed"
        }
    
    async def test_all_endpoints(self, username: str, password: str):
        """Test all configured endpoints"""
        print("🚀 Starting API Endpoint Tests")
        print("=" * 80)
        print(f"👤 Username: {username}")
        print(f"🔑 Password: {'*' * len(password)}")
        print(f"📊 Testing {len(CONFIG['URLS_TO_TEST'])} endpoints")
        
        results = []
        
        for url in CONFIG["URLS_TO_TEST"]:
            result = await self.test_endpoint(url, username, password)
            results.append(result)
            
            if result.get("success"):
                print(f"\n🎉 SUCCESS! Found working endpoint: {url}")
                print(f"   Token: {result['token'][:20]}...")
                break
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        successful = [r for r in results if r.get("success")]
        if successful:
            print(f"✅ {len(successful)} successful endpoint(s) found:")
            for result in successful:
                print(f"   • {result['url']}")
        else:
            print(f"❌ No successful endpoints found")
            print("\n🔍 Troubleshooting suggestions:")
            print("   1. Check if the university website is accessible")
            print("   2. Verify the correct login URL from the university website")
            print("   3. Check if credentials are correct")
            print("   4. Try different URL patterns")
            print("   5. Check if the API requires different authentication method")
        
        return results

def main():
    """Main function"""
    print("🔍 University API Test Script")
    print("=" * 50)
    
    # Get credentials from user
    username = input("Enter username: ").strip()
    if not username:
        print("❌ Username is required")
        return
    
    password = input("Enter password: ").strip()
    if not password:
        print("❌ Password is required")
        return
    
    # Confirm
    print(f"\n📋 Test Configuration:")
    print(f"   Username: {username}")
    print(f"   Password: {'*' * len(password)}")
    print(f"   Endpoints to test: {len(CONFIG['URLS_TO_TEST'])}")
    
    confirm = input("\nProceed with testing? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("❌ Test cancelled")
        return
    
    # Run tests
    tester = APITester()
    try:
        results = asyncio.run(tester.test_all_endpoints(username, password))
        
        # Save results to file
        with open("api_test_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: api_test_results.json")
        
    except KeyboardInterrupt:
        
        print("\n\n⏹️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

if __name__ == "__main__":
    main() 