#!/usr/bin/env python3
"""
Railway URL Helper Script
Helps identify the correct Railway URL for webhook configuration
"""
import os
import sys

def check_railway_env():
    """Check all Railway environment variables"""
    print("🔍 Checking Railway Environment Variables...")
    print("=" * 50)
    
    railway_vars = [
        "RAILWAY_STATIC_URL",
        "RAILWAY_PUBLIC_DOMAIN", 
        "RAILWAY_DOMAIN",
        "RAILWAY_APP_NAME",
        "WEBHOOK_URL",
        "PORT"
    ]
    
    found_vars = {}
    for var in railway_vars:
        value = os.getenv(var)
        if value:
            found_vars[var] = value
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
    
    print("\n" + "=" * 50)
    
    if found_vars:
        print("🎯 Recommended webhook URL construction:")
        
        # Try to construct the best URL
        if "WEBHOOK_URL" in found_vars:
            webhook_url = found_vars["WEBHOOK_URL"]
            print(f"   Use WEBHOOK_URL directly: {webhook_url}")
        elif "RAILWAY_STATIC_URL" in found_vars:
            webhook_url = f"https://{found_vars['RAILWAY_STATIC_URL']}/YOUR_BOT_TOKEN"
            print(f"   Use RAILWAY_STATIC_URL: {webhook_url}")
        elif "RAILWAY_PUBLIC_DOMAIN" in found_vars:
            webhook_url = f"https://{found_vars['RAILWAY_PUBLIC_DOMAIN']}/YOUR_BOT_TOKEN"
            print(f"   Use RAILWAY_PUBLIC_DOMAIN: {webhook_url}")
        elif "RAILWAY_APP_NAME" in found_vars:
            webhook_url = f"https://{found_vars['RAILWAY_APP_NAME']}.up.railway.app/YOUR_BOT_TOKEN"
            print(f"   Use RAILWAY_APP_NAME: {webhook_url}")
        else:
            print("   ⚠️ No Railway URL found, using fallback")
    else:
        print("❌ No Railway environment variables found!")
        print("   This script should be run on Railway platform")
    
    print("\n💡 To set a custom webhook URL:")
    print("   Set WEBHOOK_URL environment variable in Railway dashboard")
    print("   Example: https://your-app-name.up.railway.app/YOUR_BOT_TOKEN")

if __name__ == "__main__":
    check_railway_env() 