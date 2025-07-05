#!/usr/bin/env python3
"""
Test script to verify grade notification system functionality
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone, timedelta

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CONFIG
from storage.user_storage_v2 import UserStorageV2
from storage.grade_storage_v2 import GradeStorageV2
from university.api_client_v2 import UniversityAPIV2

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_grade_notification_system():
    """Test the grade notification system"""
    
    print("🧪 Testing Grade Notification System")
    print("=" * 50)
    
    # Initialize storage
    try:
        user_storage = UserStorageV2(CONFIG["DATABASE_URL"])
        grade_storage = GradeStorageV2(CONFIG["DATABASE_URL"])
        api = UniversityAPIV2()
        print("✅ Storage and API initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize storage: {e}")
        return
    
    # Get all users
    users = user_storage.get_all_users()
    print(f"📊 Found {len(users)} users in database")
    
    if not users:
        print("❌ No users found in database")
        return
    
    # Test with first user
    test_user = users[0]
    telegram_id = test_user.get("telegram_id")
    username = test_user.get("username")
    token = test_user.get("token")
    
    print(f"\n🔍 Testing with user: {username} (ID: {telegram_id})")
    
    if not token:
        print("❌ User has no token - cannot test")
        return
    
    # Test 1: Get current grades
    print("\n1️⃣ Testing current grades fetch...")
    try:
        grades = await api.get_current_grades(token)
        if grades:
            print(f"✅ Found {len(grades)} current grades")
            for grade in grades[:3]:  # Show first 3 grades
                name = grade.get('name', 'N/A')
                total = grade.get('total', 'N/A')
                print(f"   📖 {name}: {total}")
        else:
            print("⚠️ No current grades found")
    except Exception as e:
        print(f"❌ Failed to fetch current grades: {e}")
    
    # Test 2: Get stored grades
    print("\n2️⃣ Testing stored grades retrieval...")
    try:
        stored_grades = grade_storage.get_user_grades(telegram_id)
        print(f"✅ Found {len(stored_grades)} stored grades")
        for grade in stored_grades[:3]:  # Show first 3 grades
            name = grade.get('course_name', 'N/A')
            total = grade.get('total_grade_value', 'N/A')
            print(f"   📖 {name}: {total}")
    except Exception as e:
        print(f"❌ Failed to get stored grades: {e}")
    
    # Test 3: Test grade comparison (simulate notification logic)
    print("\n3️⃣ Testing grade comparison logic...")
    try:
        # Get fresh grades
        fresh_grades = await api.get_current_grades(token)
        if fresh_grades and stored_grades:
            # Transform fresh grades to match stored format
            fresh_formatted = []
            for grade in fresh_grades:
                fresh_formatted.append({
                    'course_name': grade.get('name'),
                    'course_code': grade.get('code'),
                    'coursework_grade': grade.get('coursework'),
                    'final_exam_grade': grade.get('final_exam'),
                    'total_grade_value': grade.get('total'),
                })
            
            # Simple comparison
            changes = []
            stored_map = {g.get('course_code') or g.get('course_name'): g for g in stored_grades}
            
            for fresh_grade in fresh_formatted:
                key = fresh_grade.get('course_code') or fresh_grade.get('course_name')
                stored_grade = stored_map.get(key)
                
                if stored_grade:
                    # Check for changes
                    if (fresh_grade.get('total_grade_value') != stored_grade.get('total_grade_value') or
                        fresh_grade.get('coursework_grade') != stored_grade.get('coursework_grade') or
                        fresh_grade.get('final_exam_grade') != stored_grade.get('final_exam_grade')):
                        changes.append({
                            'course': fresh_grade.get('course_name'),
                            'old_total': stored_grade.get('total_grade_value'),
                            'new_total': fresh_grade.get('total_grade_value')
                        })
            
            if changes:
                print(f"✅ Found {len(changes)} grade changes:")
                for change in changes:
                    print(f"   📚 {change['course']}: {change['old_total']} → {change['new_total']}")
            else:
                print("✅ No grade changes detected")
        else:
            print("⚠️ Cannot compare - missing fresh or stored grades")
    except Exception as e:
        print(f"❌ Failed to compare grades: {e}")
    
    # Test 4: Test notification message format
    print("\n4️⃣ Testing notification message format...")
    try:
        from utils.analytics import GradeAnalytics
        analytics = GradeAnalytics(user_storage)
        
        if fresh_grades:
            message = await analytics.format_current_grades_with_quote(telegram_id, fresh_grades)
            print("✅ Notification message format test:")
            print(f"   Length: {len(message)} characters")
            print(f"   Contains quote: {'نعم' if 'اقتباس' in message else 'لا'}")
            print(f"   Preview: {message[:200]}...")
        else:
            print("⚠️ No fresh grades to format")
    except Exception as e:
        print(f"❌ Failed to format notification message: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Grade notification system test completed!")

async def test_admin_force_grade_check():
    """Test the admin force grade check functionality"""
    
    print("\n🧪 Testing Admin Force Grade Check")
    print("=" * 50)
    
    # Initialize storage
    try:
        user_storage = UserStorageV2(CONFIG["DATABASE_URL"])
        grade_storage = GradeStorageV2(CONFIG["DATABASE_URL"])
        api = UniversityAPIV2()
        print("✅ Storage and API initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize storage: {e}")
        return
    
    # Get all users
    users = user_storage.get_all_users()
    print(f"📊 Found {len(users)} users in database")
    
    if not users:
        print("❌ No users found in database")
        return
    
    # Test force grade check for all users
    print("\n🔄 Testing force grade check for all users...")
    
    notified_count = 0
    total_users = len(users)
    
    for i, user in enumerate(users, 1):
        telegram_id = user.get("telegram_id")
        username = user.get("username")
        token = user.get("token")
        
        print(f"   [{i}/{total_users}] Checking {username}...")
        
        if not token:
            print(f"      ⚠️ No token for {username}")
            continue
        
        try:
            # Test token validity
            if not await api.test_token(token):
                print(f"      ❌ Invalid token for {username}")
                continue
            
            # Get user data
            user_data = await api.get_user_data(token)
            if not user_data or "grades" not in user_data:
                print(f"      ⚠️ No grade data for {username}")
                continue
            
            new_grades = user_data.get("grades", [])
            old_grades = grade_storage.get_user_grades(telegram_id)
            
            # Simple comparison
            changes = []
            if old_grades and new_grades:
                stored_map = {g.get('course_code') or g.get('course_name'): g for g in old_grades}
                
                for grade in new_grades:
                    key = grade.get('code') or grade.get('name')
                    stored_grade = stored_map.get(key)
                    
                    if stored_grade:
                        if (grade.get('total') != stored_grade.get('total_grade_value') or
                            grade.get('coursework') != stored_grade.get('coursework_grade') or
                            grade.get('final_exam') != stored_grade.get('final_exam_grade')):
                            changes.append(grade.get('name', 'Unknown'))
            
            if changes:
                print(f"      ✅ Found {len(changes)} changes for {username}")
                notified_count += 1
            else:
                print(f"      ✅ No changes for {username}")
                
        except Exception as e:
            print(f"      ❌ Error checking {username}: {e}")
    
    print(f"\n📊 Force grade check summary:")
    print(f"   Total users: {total_users}")
    print(f"   Users with changes: {notified_count}")
    print(f"   Success rate: {(notified_count/total_users)*100:.1f}%")

if __name__ == "__main__":
    async def main():
        await test_grade_notification_system()
        await test_admin_force_grade_check()
    
    asyncio.run(main()) 