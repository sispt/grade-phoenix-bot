#!/usr/bin/env python3
"""
Test script to check grade data format and average calculation
"""

import asyncio
import logging
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.analytics import GradeAnalytics
from storage.user_storage_v2 import UserStorageV2

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_grade_format():
    """Test grade data format and average calculation"""
    
    # Get credentials from user input
    username = input("Enter university username: ").strip()
    password = input("Enter university password: ").strip()
    
    if not username or not password:
        print("❌ Username and password are required")
        return
    
    print(f"\n🔍 Testing grade format for username: {username}")
    print("=" * 50)
    
    # Initialize API client
    from university.api_client import UniversityAPI
    api = UniversityAPI()
    
    # Step 1: Login
    print("1️⃣ Attempting login...")
    token = await api.login(username, password)
    
    if not token:
        print("❌ Login failed")
        return
    
    print(f"✅ Login successful, token length: {len(token)}")
    
    # Step 2: Get current grades
    print("\n2️⃣ Fetching current grades...")
    grades = await api.get_current_grades(token)
    
    if not grades:
        print("❌ No grades found")
        return
    
    print(f"✅ Found {len(grades)} grades")
    
    # Step 3: Analyze grade format
    print("\n3️⃣ Analyzing grade format...")
    print("-" * 30)
    
    for i, grade in enumerate(grades, 1):
        name = grade.get('name', 'N/A')
        code = grade.get('code', 'N/A')
        total = grade.get('total', 'N/A')
        coursework = grade.get('coursework', 'N/A')
        final_exam = grade.get('final_exam', 'N/A')
        
        print(f"📖 Grade {i}: {name} ({code})")
        print(f"   Total: '{total}' (type: {type(total)})")
        print(f"   Coursework: '{coursework}'")
        print(f"   Final Exam: '{final_exam}'")
        
        # Test float conversion
        if total and total != 'لم يتم النشر':
            try:
                float_val = float(total)
                print(f"   ✅ Float conversion: {float_val}")
            except ValueError as e:
                print(f"   ❌ Float conversion failed: {e}")
                # Try to extract number
                import re
                numbers = re.findall(r'\d+', str(total))
                if numbers:
                    print(f"   🔍 Found numbers: {numbers}")
                    try:
                        extracted = float(numbers[0])
                        print(f"   ✅ Extracted number: {extracted}")
                    except:
                        print(f"   ❌ Failed to convert extracted number")
        else:
            print(f"   ⏭️ Skipped (not published)")
        print()
    
    # Step 4: Test average calculation
    print("4️⃣ Testing average calculation...")
    print("-" * 30)
    
    analytics = GradeAnalytics(None)  # We don't need user storage for this test
    
    # Test the current calculation method
    avg_grade = analytics._calculate_average_grade(grades)
    print(f"📊 Current method average: {avg_grade}")
    
    # Test with improved parsing
    total_grades = []
    for grade in grades:
        total = grade.get("total")
        if total and total != 'لم يتم النشر':
            # Try direct conversion first
            try:
                total_grades.append(float(total))
                continue
            except ValueError:
                pass
            
            # Try to extract number from text like "87 %"
            import re
            numbers = re.findall(r'\d+', str(total))
            if numbers:
                try:
                    total_grades.append(float(numbers[0]))
                except:
                    continue
    
    if total_grades:
        improved_avg = sum(total_grades) / len(total_grades)
        print(f"📊 Improved method average: {improved_avg:.2f}%")
        print(f"📊 Grades used: {total_grades}")
    else:
        print("📊 No numeric grades found for average calculation")
    
    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    try:
        asyncio.run(test_grade_format())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True) 