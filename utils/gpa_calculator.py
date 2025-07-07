"""
📊 GPA Calculator Utility
Handles GPA calculations using credit.csv mapping and provides both automatic and custom calculation features
"""

import csv
import os
import re
from typing import List, Dict, Any, Optional, Tuple
from utils.logger import get_bot_logger

logger = get_bot_logger()

class GPACalculator:
    """GPA Calculator using credit.csv mapping"""
    
    def __init__(self, credit_csv_path: str = "storage/credit.csv"):
        self.credit_csv_path = credit_csv_path
        self.percentage_to_points = self._load_credit_mapping()
    
    def _load_credit_mapping(self) -> Dict[int, float]:
        """Load percentage to earned points mapping from credit.csv"""
        mapping = {}
        try:
            if not os.path.exists(self.credit_csv_path):
                logger.error(f"Credit CSV file not found: {self.credit_csv_path}")
                return mapping
            
            with open(self.credit_csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        percentage = int(row['percentage'])
                        earned_points = float(row['earned_points'])
                        mapping[percentage] = earned_points
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Invalid row in credit.csv: {row}, error: {e}")
                        continue
            
            logger.info(f"Loaded {len(mapping)} percentage-to-points mappings")
            return mapping
            
        except Exception as e:
            logger.error(f"Error loading credit mapping: {e}")
            return mapping
    
    def get_earned_points(self, percentage: float) -> float:
        """Get earned points for a given percentage (truncate to integer)"""
        if not self.percentage_to_points:
            logger.error("Credit mapping not loaded")
            return 0.0
        
        # Truncate percentage to integer (do not round)
        int_percentage = int(percentage)
        
        # Find the closest percentage in our mapping
        if int_percentage in self.percentage_to_points:
            return self.percentage_to_points[int_percentage]
        
        # If exact match not found, find the closest one
        closest_percentage = min(self.percentage_to_points.keys(), 
                               key=lambda x: abs(x - int_percentage))
        return self.percentage_to_points[closest_percentage]
    
    def calculate_gpa_from_grades(self, grades: List[Dict[str, Any]]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate GPA from a list of grades
        
        Args:
            grades: List of grade dictionaries with 'total' and 'ects' fields
            
        Returns:
            Tuple of (gpa, details_dict)
        """
        total_weighted_points = 0.0
        total_credits = 0.0
        valid_courses = 0
        invalid_courses = []
        
        for grade in grades:
            total_grade = grade.get('total', '')
            ects_credits = grade.get('ects', 0.0)
            course_name = grade.get('name', 'Unknown Course')
            
            # Skip if no grade or not published
            if not total_grade or total_grade == 'لم يتم النشر' or total_grade.strip() == '':
                invalid_courses.append({
                    'name': course_name,
                    'reason': 'Grade not published'
                })
                continue
            
            # Extract numeric percentage from grade
            percentage = self._extract_percentage(total_grade)
            if percentage is None:
                invalid_courses.append({
                    'name': course_name,
                    'reason': f'Invalid grade format: {total_grade}'
                })
                continue
            
            # Get earned points for this percentage
            earned_points = self.get_earned_points(percentage)
            
            # Calculate weighted points
            weighted_points = earned_points * ects_credits
            
            total_weighted_points += weighted_points
            total_credits += ects_credits
            valid_courses += 1
            
            logger.debug(f"Course: {course_name}, Percentage: {percentage}%, "
                        f"Earned Points: {earned_points}, Credits: {ects_credits}, "
                        f"Weighted: {weighted_points}")
        
        # Calculate GPA
        if total_credits > 0:
            gpa = total_weighted_points / total_credits
        else:
            gpa = 0.0
        
        # Format GPA to 3 digits (remove trailing zeros)
        formatted_gpa = self._format_gpa(gpa)
        
        details = {
            'gpa': formatted_gpa,
            'total_weighted_points': total_weighted_points,
            'total_credits': total_credits,
            'valid_courses': valid_courses,
            'invalid_courses': invalid_courses,
            'total_courses': len(grades)
        }
        
        return formatted_gpa, details
    
    def calculate_custom_gpa(self, courses: List[Dict[str, Any]]) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate GPA from custom course data
        
        Args:
            courses: List of course dictionaries with 'percentage' and 'credits' fields
            
        Returns:
            Tuple of (gpa, details_dict)
        """
        total_weighted_points = 0.0
        total_credits = 0.0
        valid_courses = 0
        invalid_courses = []
        
        for i, course in enumerate(courses, 1):
            percentage = course.get('percentage')
            credits = course.get('credits')
            course_name = course.get('name', f'Course {i}')
            
            # Validate inputs
            if percentage is None or credits is None:
                invalid_courses.append({
                    'name': course_name,
                    'reason': 'Missing percentage or credits'
                })
                continue
            
            try:
                percentage = float(percentage)
                credits = float(credits)
            except (ValueError, TypeError):
                invalid_courses.append({
                    'name': course_name,
                    'reason': f'Invalid values: percentage={percentage}, credits={credits}'
                })
                continue
            
            # Validate ranges
            if not (0 <= percentage <= 100):
                invalid_courses.append({
                    'name': course_name,
                    'reason': f'Percentage out of range: {percentage}%'
                })
                continue
            
            if credits <= 0:
                invalid_courses.append({
                    'name': course_name,
                    'reason': f'Invalid credits: {credits}'
                })
                continue
            
            # Get earned points for this percentage
            earned_points = self.get_earned_points(percentage)
            
            # Calculate weighted points
            weighted_points = earned_points * credits
            
            total_weighted_points += weighted_points
            total_credits += credits
            valid_courses += 1
            
            logger.debug(f"Custom Course: {course_name}, Percentage: {percentage}%, "
                        f"Earned Points: {earned_points}, Credits: {credits}, "
                        f"Weighted: {weighted_points}")
        
        # Calculate GPA
        if total_credits > 0:
            gpa = total_weighted_points / total_credits
        else:
            gpa = 0.0
        
        # Format GPA to 3 digits (remove trailing zeros)
        formatted_gpa = self._format_gpa(gpa)
        
        details = {
            'gpa': formatted_gpa,
            'total_weighted_points': total_weighted_points,
            'total_credits': total_credits,
            'valid_courses': valid_courses,
            'invalid_courses': invalid_courses,
            'total_courses': len(courses)
        }
        
        return formatted_gpa, details
    
    def _extract_percentage(self, grade_text: str) -> Optional[float]:
        """Extract numeric percentage from grade text"""
        if not grade_text or not isinstance(grade_text, str):
            return None
        
        # Remove common non-numeric characters
        cleaned = re.sub(r'[^\d.]', '', grade_text)
        
        try:
            percentage = float(cleaned)
            # Ensure it's within valid range
            if 0 <= percentage <= 100:
                return percentage
            else:
                logger.warning(f"Percentage out of range: {percentage}")
                return None
        except ValueError:
            logger.warning(f"Could not extract percentage from: {grade_text}")
            return None
    
    def _format_gpa(self, gpa: float) -> float:
        """Format GPA to exactly 2 digits with proper rounding and trailing zero removal"""
        if gpa == 0.0:
            return 0.0
        
        # Use decimal for precise rounding to 2 decimal places
        from decimal import Decimal, ROUND_HALF_UP
        rounded = float(Decimal(str(gpa)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        
        # Convert to string with exactly 2 decimal places
        gpa_str = f"{rounded:.2f}"
        
        # Remove trailing zeros from the right side
        gpa_str = gpa_str.rstrip('0')
        
        # If we end up with just a decimal point, remove it
        if gpa_str.endswith('.'):
            gpa_str = gpa_str[:-1]
        
        # Convert back to float
        return float(gpa_str) if gpa_str else 0.0
    
    def get_gpa_description(self, gpa: float) -> str:
        """Get descriptive text for GPA range"""
        if gpa >= 3.7:
            return "ممتاز (Excellent)"
        elif gpa >= 3.3:
            return "جيد جداً (Very Good)"
        elif gpa >= 2.7:
            return "جيد (Good)"
        elif gpa >= 2.0:
            return "مقبول (Acceptable)"
        elif gpa >= 1.0:
            return "ضعيف (Weak)"
        else:
            return "راسب (Failed)" 