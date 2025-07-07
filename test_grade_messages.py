#!/usr/bin/env python3
"""
Test script for grade analytics message formatting (current and old grades)
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.analytics import GradeAnalytics

class MockUserStorage:
    def get_user(self, telegram_id):
        return {"username": "test_user"}

async def test_grade_messages():
    analytics = GradeAnalytics(MockUserStorage())
    telegram_id = 123456

    # Test Case 1: All courses completed
    print("\n===== Test Case 1: All Courses Completed =====")
    current_grades = [
        {'name': 'Math', 'code': 'MATH101', 'coursework': '40', 'final_exam': '45', 'total': '85', 'ects': 4.0},
        {'name': 'Physics', 'code': 'PHYS101', 'coursework': '38', 'final_exam': '54', 'total': '92', 'ects': 3.0},
        {'name': 'Chemistry', 'code': 'CHEM101', 'coursework': '30', 'final_exam': '48', 'total': '78', 'ects': 4.0},
    ]
    msg = await analytics.format_current_grades_with_quote(telegram_id, current_grades)
    print(msg)

    # Test Case 2: No courses completed
    print("\n===== Test Case 2: No Courses Completed =====")
    current_grades = [
        {'name': 'Math', 'code': 'MATH101', 'coursework': 'لم يتم النشر', 'final_exam': 'لم يتم النشر', 'total': 'لم يتم النشر', 'ects': 4.0},
        {'name': 'Physics', 'code': 'PHYS101', 'coursework': 'لم يتم النشر', 'final_exam': 'لم يتم النشر', 'total': 'لم يتم النشر', 'ects': 3.0},
        {'name': 'Chemistry', 'code': 'CHEM101', 'coursework': 'لم يتم النشر', 'final_exam': 'لم يتم النشر', 'total': 'لم يتم النشر', 'ects': 4.0},
    ]
    msg = await analytics.format_current_grades_with_quote(telegram_id, current_grades)
    print(msg)

    # Test Case 3: Partial completion (2/4 courses)
    print("\n===== Test Case 3: Partial Completion (2/4) =====")
    current_grades = [
        {'name': 'Math', 'code': 'MATH101', 'coursework': '40', 'final_exam': '45', 'total': '85', 'ects': 4.0},
        {'name': 'Physics', 'code': 'PHYS101', 'coursework': '38', 'final_exam': '54', 'total': '92', 'ects': 3.0},
        {'name': 'Chemistry', 'code': 'CHEM101', 'coursework': 'لم يتم النشر', 'final_exam': 'لم يتم النشر', 'total': 'لم يتم النشر', 'ects': 4.0},
        {'name': 'Biology', 'code': 'BIO101', 'coursework': 'لم يتم النشر', 'final_exam': 'لم يتم النشر', 'total': 'لم يتم النشر', 'ects': 3.0},
    ]
    msg = await analytics.format_current_grades_with_quote(telegram_id, current_grades)
    print(msg)

    # Test Case 4: Single course completed
    print("\n===== Test Case 4: Single Course Completed (1/3) =====")
    current_grades = [
        {'name': 'Math', 'code': 'MATH101', 'coursework': '40', 'final_exam': '45', 'total': '85', 'ects': 4.0},
        {'name': 'Physics', 'code': 'PHYS101', 'coursework': 'لم يتم النشر', 'final_exam': 'لم يتم النشر', 'total': 'لم يتم النشر', 'ects': 3.0},
        {'name': 'Chemistry', 'code': 'CHEM101', 'coursework': 'لم يتم النشر', 'final_exam': 'لم يتم النشر', 'total': 'لم يتم النشر', 'ects': 4.0},
    ]
    msg = await analytics.format_current_grades_with_quote(telegram_id, current_grades)
    print(msg)

    # Example: Old grades
    old_grades = [
        {'name': 'Biology', 'code': 'BIO101', 'coursework': '35', 'final_exam': '50', 'total': '85', 'ects': 4.0, 'term_name': 'الفصل الدراسي السابق'},
        {'name': 'History', 'code': 'HIST101', 'coursework': '40', 'final_exam': '45', 'total': '92', 'ects': 3.0, 'term_name': 'الفصل الدراسي السابق'},
        {'name': 'Art', 'code': 'ART101', 'coursework': '30', 'final_exam': '48', 'total': '78', 'ects': 4.0, 'term_name': 'الفصل الدراسي السابق'},
        {'name': 'Failing', 'code': 'FAIL102', 'coursework': '10', 'final_exam': '15', 'total': '29', 'ects': 2.0, 'term_name': 'الفصل الدراسي السابق'},
    ]
    print("\n===== Old Grades Message =====")
    msg = await analytics.format_old_grades_with_analysis(telegram_id, old_grades)
    print(msg)

if __name__ == "__main__":
    asyncio.run(test_grade_messages()) 