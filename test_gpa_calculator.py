#!/usr/bin/env python3
"""
Test script for GPA calculator functionality
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.analytics import GradeAnalytics

class MockUserStorage:
    def get_user(self, telegram_id):
        return {"username": "test_user"}

def test_gpa_calculation():
    """Test the GPA calculation functionality"""
    print("🧮 Testing GPA Calculator Functionality")
    print("=" * 50)
    
    # Create analytics instance
    analytics = GradeAnalytics(MockUserStorage())
    
    # Test 1: Normal grades
    print("\n📊 Test 1: Normal grades")
    grades = [
        {'total': '85', 'ects': 4.0},
        {'total': '92', 'ects': 3.0},
        {'total': '78', 'ects': 4.0}
    ]
    gpa = analytics._calculate_gpa(grades)
    print(f"Grades: {grades}")
    gpa_str = f"{gpa:.2f}".rstrip('0').rstrip('.') if gpa is not None else "-"
    print(f"Calculated GPA: {gpa_str}" if gpa is not None else "GPA: None")
    
    # Test 2: Grades with percentages below 30
    print("\n📊 Test 2: Grades with percentages below 30")
    grades = [
        {'total': '25', 'ects': 4.0},  # Should get 0 earned points
        {'total': '85', 'ects': 3.0},
        {'total': '92', 'ects': 4.0}
    ]
    gpa = analytics._calculate_gpa(grades)
    print(f"Grades: {grades}")
    gpa_str = f"{gpa:.2f}".rstrip('0').rstrip('.') if gpa is not None else "-"
    print(f"Calculated GPA: {gpa_str}" if gpa is not None else "GPA: None")
    
    # Test 3: Mixed input formats
    print("\n📊 Test 3: Mixed input formats")
    grades = [
        {'total': '85%', 'ects': 4.0},  # With % symbol
        {'total': '92', 'ects': 3.0},   # Clean number
        {'total': '78.5', 'ects': 4.0}  # Decimal
    ]
    gpa = analytics._calculate_gpa(grades)
    print(f"Grades: {grades}")
    gpa_str = f"{gpa:.2f}".rstrip('0').rstrip('.') if gpa is not None else "-"
    print(f"Calculated GPA: {gpa_str}" if gpa is not None else "GPA: None")
    
    # Test 4: Edge cases
    print("\n📊 Test 4: Edge cases")
    grades = [
        {'total': '100', 'ects': 4.0},  # Perfect score
        {'total': '30', 'ects': 3.0},   # Minimum passing
        {'total': '29', 'ects': 4.0}    # Below minimum (should get 0)
    ]
    gpa = analytics._calculate_gpa(grades)
    print(f"Grades: {grades}")
    gpa_str = f"{gpa:.2f}".rstrip('0').rstrip('.') if gpa is not None else "-"
    print(f"Calculated GPA: {gpa_str}" if gpa is not None else "GPA: None")
    
    # Test 5: Invalid grades
    print("\n📊 Test 5: Invalid grades")
    grades = [
        {'total': 'abc', 'ects': 4.0},  # Invalid percentage
        {'total': '85', 'ects': 25.0},  # Invalid ECTS
        {'total': '92', 'ects': 3.0}    # Valid
    ]
    gpa = analytics._calculate_gpa(grades)
    print(f"Grades: {grades}")
    gpa_str = f"{gpa:.2f}".rstrip('0').rstrip('.') if gpa is not None else "-"
    print(f"Calculated GPA: {gpa_str}" if gpa is not None else "GPA: None")
    
    # Test 6: Empty grades
    print("\n📊 Test 6: Empty grades")
    grades = []
    gpa = analytics._calculate_gpa(grades)
    print(f"Grades: {grades}")
    gpa_str = f"{gpa:.2f}".rstrip('0').rstrip('.') if gpa is not None else "-"
    print(f"Calculated GPA: {gpa_str}" if gpa is not None else "GPA: None")
    
    # Test 7: Realistic final GPA calculation
    print("\n📊 Test 7: Realistic final GPA calculation (10 courses)")
    grades = [
        {'total': '95', 'ects': 4.0},
        {'total': '88', 'ects': 3.0},
        {'total': '76', 'ects': 4.0},
        {'total': '65', 'ects': 2.0},
        {'total': '54', 'ects': 3.0},
        {'total': '100', 'ects': 4.0},
        {'total': '29', 'ects': 2.0},   # Below 30, should be 0
        {'total': '85.5', 'ects': 3.0},  # Should be 85
        {'total': '70', 'ects': 4.0},
        {'total': '40', 'ects': 2.0}
    ]
    gpa = analytics._calculate_gpa(grades)
    print(f"Grades: {grades}")
    gpa_str = f"{gpa:.2f}".rstrip('0').rstrip('.') if gpa is not None else "-"
    print(f"Calculated GPA: {gpa_str}" if gpa is not None else "GPA: None")
    
    print("\n" + "=" * 50)
    print("✅ GPA Calculator Tests Completed!")

def test_percentage_extraction():
    """Test percentage extraction logic"""
    print("\n🔍 Testing Percentage Extraction Logic")
    print("=" * 50)
    
    test_inputs = [
        "85",
        "85%", 
        "85.5",
        "85.5%",
        "abc",
        "85abc",
        "abc85",
        "85%abc",
        "100",
        "0",
        "25"
    ]
    
    for text in test_inputs:
        # Extract digits only
        percent_str = ''.join(filter(str.isdigit, text))
        if percent_str:
            percentage = int(percent_str)
            print(f"Input: '{text}' → Extracted: {percentage}")
        else:
            print(f"Input: '{text}' → No digits found")

if __name__ == "__main__":
    print("🚀 Starting GPA Calculator Tests")
    test_gpa_calculation()
    test_percentage_extraction()
    print("\n🎉 All tests completed!") 