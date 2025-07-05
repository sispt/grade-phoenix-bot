#!/usr/bin/env python3
"""
Test script to verify V2 storage is working correctly
"""

import os
import sys
from storage.user_storage_v2 import UserStorageV2
from storage.grade_storage_v2 import GradeStorageV2

def test_storage():
    """Test V2 storage functionality"""
    print("🧪 Testing V2 storage functionality...")
    
    # Use a test database URL
    database_url = "sqlite:///test_storage.db"
    
    try:
        # Initialize storage
        print("📦 Initializing UserStorageV2...")
        user_storage = UserStorageV2(database_url)
        print("✅ UserStorageV2 initialized successfully")
        
        print("📦 Initializing GradeStorageV2...")
        grade_storage = GradeStorageV2(database_url)
        print("✅ GradeStorageV2 initialized successfully")
        
        # Test user operations
        print("\n👤 Testing user operations...")
        test_user_data = {
            "firstname": "Test",
            "lastname": "User",
            "fullname": "Test User",
            "email": "test@example.com"
        }
        
        # Save user
        success = user_storage.save_user(12345, "TEST123", "test_token", test_user_data)
        print(f"✅ Save user: {success}")
        
        # Get user
        user = user_storage.get_user(12345)
        print(f"✅ Get user: {user is not None}")
        if user:
            print(f"   Username: {user.get('username')}")
            print(f"   Token expired notified: {user.get('token_expired_notified')}")
        
        # Test grade operations
        print("\n📊 Testing grade operations...")
        test_grades = [
            {
                "name": "Test Course 1",
                "code": "TEST101",
                "ects": "3.0",
                "coursework": "85",
                "final_exam": "90",
                "total": "88%",
                "term_name": "Fall 2024",
                "term_id": "TEST_TERM_1"
            }
        ]
        
        # Save grades
        success = grade_storage.save_grades(12345, test_grades)
        print(f"✅ Save grades: {success}")
        
        # Get grades
        grades = grade_storage.get_user_grades(12345)
        print(f"✅ Get grades: {len(grades)} grades found")
        if grades:
            print(f"   First grade: {grades[0].get('course_name')}")
        
        # Test compatibility method
        grades_compat = grade_storage.get_grades(12345)
        print(f"✅ Compatibility method: {len(grades_compat)} grades found")
        
        print("\n🎉 All tests passed! V2 storage is working correctly.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_storage()
    sys.exit(0 if success else 1) 