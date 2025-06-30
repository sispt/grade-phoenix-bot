"""
🧪 Test HTML Grades Extraction
"""
import asyncio
import json
from university.api import UniversityAPI

async def test_html_extraction():
    """Test HTML grades extraction"""
    print("🧪 Testing HTML Grades Extraction...")
    
    api = UniversityAPI()
    
    # Test parsing Homepage.html
    grades = api.parse_html_grades_file("Homepage.html")
    
    print(f"✅ Extracted {len(grades)} grade records:")
    for i, grade in enumerate(grades, 1):
        course_name = grade.get('المقرر', 'N/A')
        course_code = grade.get('كود المادة', 'N/A')
        final_grade = grade.get('الدرجة', 'N/A')
        print(f"  {i}. {course_name} ({course_code}) - {final_grade}")
    
    # Save to file for verification
    with open("test_html_results.json", "w", encoding="utf-8") as f:
        json.dump(grades, f, ensure_ascii=False, indent=2)
    print("\n💾 Results saved to test_html_results.json")

if __name__ == "__main__":
    asyncio.run(test_html_extraction()) 