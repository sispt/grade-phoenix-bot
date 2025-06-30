#!/usr/bin/env python3
"""
🧪 Test Script for GraphQL Course Grades Parser
Tests the new parse_course_grades_from_graphql function
"""

import json
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from university.api import UniversityAPI

def create_sample_graphql_response():
    """Create a sample GraphQL response for testing"""
    return {
        "data": {
            "getPage": {
                "panels": [
                    {
                        "blocks": [
                            {
                                "name": "testpage_track_10459",
                                "body": """
                                <table>
                                    <thead>
                                        <tr>
                                            <th>المقرر</th>
                                            <th>كود المادة</th>
                                            <th>رصيد ECTS</th>
                                            <th>درجة الأعمال</th>
                                            <th>درجة النظري</th>
                                            <th>الدرجة</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>اللغة العربية (1)</td>
                                            <td>ARAB100</td>
                                            <td>2</td>
                                            <td>38</td>
                                            <td>49</td>
                                            <td>87 %</td>
                                        </tr>
                                        <tr>
                                            <td>الرياضيات (1)</td>
                                            <td>MATH101</td>
                                            <td>3</td>
                                            <td>42</td>
                                            <td>45</td>
                                            <td>87 %</td>
                                        </tr>
                                        <tr>
                                            <td>الفيزياء (1)</td>
                                            <td>PHYS101</td>
                                            <td>4</td>
                                            <td>35</td>
                                            <td>52</td>
                                            <td>87 %</td>
                                        </tr>
                                    </tbody>
                                </table>
                                """
                            },
                            {
                                "name": "other_block",
                                "body": "<p>This is not the grades block</p>"
                            }
                        ]
                    }
                ]
            }
        }
    }

def test_graphql_grades_parser():
    """Test the GraphQL grades parser function"""
    print("🧪 Testing GraphQL Course Grades Parser")
    print("=" * 50)
    
    # Create API instance
    api = UniversityAPI()
    
    # Create sample response
    sample_response = create_sample_graphql_response()
    
    print("📋 Sample GraphQL Response Structure:")
    print(json.dumps(sample_response, indent=2, ensure_ascii=False))
    print("\n" + "=" * 50)
    
    # Parse the grades
    print("🔍 Parsing course grades...")
    grades = api.parse_course_grades_from_graphql(sample_response)
    
    print(f"\n✅ Parsed {len(grades)} course grades:")
    print("=" * 50)
    
    for i, grade in enumerate(grades, 1):
        print(f"\n📚 Course {i}:")
        print(f"   المقرر (Course): {grade['course']}")
        print(f"   كود المادة (Code): {grade['code']}")
        print(f"   رصيد ECTS (ECTS): {grade['ects']}")
        print(f"   درجة الأعمال (Practical): {grade['practical']}")
        print(f"   درجة النظري (Theoretical): {grade['theoretical']}")
        print(f"   الدرجة (Total): {grade['total']}")
    
    print("\n" + "=" * 50)
    print("🎉 Test completed successfully!")
    
    return grades

def test_with_real_data_structure():
    """Test with a more realistic data structure"""
    print("\n🧪 Testing with Realistic Data Structure")
    print("=" * 50)
    
    # More realistic response structure
    realistic_response = {
        "data": {
            "getPage": {
                "panels": [
                    {
                        "blocks": [
                            {
                                "name": "header_block",
                                "body": "<h1>Student Grades</h1>"
                            },
                            {
                                "name": "testpage_track_10459",
                                "body": """
                                <table class="grades-table">
                                    <thead>
                                        <tr>
                                            <th>المقرر</th>
                                            <th>كود المادة</th>
                                            <th>رصيد ECTS</th>
                                            <th>درجة الأعمال</th>
                                            <th>درجة النظري</th>
                                            <th>الدرجة</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        <tr>
                                            <td>برمجة الحاسوب</td>
                                            <td>CS101</td>
                                            <td>4</td>
                                            <td>45</td>
                                            <td>48</td>
                                            <td>93 %</td>
                                        </tr>
                                        <tr>
                                            <td>قواعد البيانات</td>
                                            <td>CS201</td>
                                            <td>3</td>
                                            <td>40</td>
                                            <td>50</td>
                                            <td>90 %</td>
                                        </tr>
                                    </tbody>
                                </table>
                                """
                            }
                        ]
                    }
                ]
            }
        }
    }
    
    api = UniversityAPI()
    grades = api.parse_course_grades_from_graphql(realistic_response)
    
    print(f"✅ Parsed {len(grades)} grades from realistic structure:")
    for grade in grades:
        print(f"   {grade['course']} ({grade['code']}) - {grade['total']}")

if __name__ == "__main__":
    try:
        # Test basic functionality
        test_graphql_grades_parser()
        
        # Test with realistic structure
        test_with_real_data_structure()
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc() 