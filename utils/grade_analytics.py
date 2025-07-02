"""
📊 Grade Analytics & Quote Support
Enhanced grade display with motivational quotes and daily wisdom.
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import os
import random
import math
import requests
import asyncio
import logging

# Configure logging
logger = logging.getLogger(__name__)

class GradeAnalytics:
    """Handles grade analytics with motivational quotes and wisdom"""
    
    def __init__(self, user_storage):
        self.user_storage = user_storage
        self.analytics_file = "data/grade_analytics.json"
        self.achievements_file = "data/achievements.json"
        self.daily_quotes_file = "data/daily_quotes.json"
        self._ensure_files()
    
    def _ensure_files(self):
        """Ensure analytics and achievements files exist"""
        for file_path in [self.analytics_file, self.achievements_file, self.daily_quotes_file]:
            if not os.path.exists(file_path):
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({}, f, ensure_ascii=False, indent=2)
    
    async def get_daily_quote(self) -> Optional[Dict[str, str]]:
        """Get a daily quote from working APIs with philosophy categories"""
        # Try multiple working APIs in order of preference
        apis = [
            self._try_zenquotes_api,
            self._try_adviceslip_api,
            self._try_local_fallback
        ]
        
        for api_func in apis:
            try:
                quote = await api_func()
                if quote:
                    return quote
            except Exception as e:
                logger.warning(f"API {api_func.__name__} failed: {e}")
                continue
        
        return None
    
    async def _try_local_fallback(self) -> Optional[Dict[str, str]]:
        """Local fallback with motivational quotes when all APIs fail"""
        fallback_quotes = [
            {"text": "The unexamined life is not worth living.", "author": "Socrates", "philosophy": "wisdom"},
            {"text": "Wisdom begins in wonder.", "author": "Socrates", "philosophy": "wisdom"},
            {"text": "The only true wisdom is in knowing you know nothing.", "author": "Socrates", "philosophy": "wisdom"},
            {"text": "Life is what happens when you're busy making other plans.", "author": "John Lennon", "philosophy": "life"},
            {"text": "The journey of a thousand miles begins with one step.", "author": "Lao Tzu", "philosophy": "wisdom"},
            {"text": "Be the change you wish to see in the world.", "author": "Mahatma Gandhi", "philosophy": "wisdom"},
            {"text": "In the middle of difficulty lies opportunity.", "author": "Albert Einstein", "philosophy": "wisdom"},
            {"text": "The future belongs to those who believe in the beauty of their dreams.", "author": "Eleanor Roosevelt", "philosophy": "motivation"},
            {"text": "Success is not final, failure is not fatal: it is the courage to continue that counts.", "author": "Winston Churchill", "philosophy": "perseverance"},
            {"text": "The mind is everything. What you think you become.", "author": "Buddha", "philosophy": "wisdom"}
        ]
        
        selected_quote = random.choice(fallback_quotes)
        return {
            'text': selected_quote['text'],
            'author': selected_quote['author'],
            'philosophy': selected_quote['philosophy'],
            'context': 'local_fallback'
        }
    
    async def get_scenario_quote(self, scenario: str) -> Optional[Dict[str, str]]:
        """Get a scenario-specific quote from working APIs with philosophy categories"""
        # Define scenario-specific philosophy categories
        scenario_categories = {
            'improvement': ['success', 'achievement', 'growth', 'motivation'],
            'setback': ['perseverance', 'resilience', 'overcoming', 'challenge'],
            'excellence': ['excellence', 'mastery', 'perfection', 'achievement'],
            'struggle': ['struggle', 'difficulty', 'perseverance', 'strength'],
            'consistency': ['discipline', 'consistency', 'habits', 'focus'],
            'reflection': ['wisdom', 'philosophy', 'thinking', 'awareness'],
            'growth': ['growth', 'development', 'learning', 'progress'],
            'breakthrough': ['breakthrough', 'innovation', 'discovery', 'achievement'],
            'first_grade': ['beginning', 'start', 'journey', 'first_step']
        }
        
        # Try multiple working APIs in order of preference
        apis = [
            lambda: self._try_zenquotes_api_with_philosophy(scenario_categories.get(scenario, ['wisdom'])),
            lambda: self._try_adviceslip_api_with_philosophy(scenario_categories.get(scenario, ['wisdom'])),
            lambda: self._try_scenario_local_fallback(scenario)
        ]
        
        for api_func in apis:
            try:
                quote = await api_func()
                if quote:
                    return quote
            except Exception as e:
                logger.warning(f"API {api_func.__name__} failed for scenario {scenario}: {e}")
                continue
        
        return None

    async def _try_zenquotes_api(self) -> Optional[Dict[str, str]]:
        """Try Zen Quotes API - working and reliable"""
        try:
            url = 'https://zenquotes.io/api/random'
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'text': data[0].get('q', ''),
                    'author': data[0].get('a', 'Unknown'),
                    'philosophy': 'wisdom',
                    'context': 'daily_wisdom'
                }
        except Exception as e:
            logger.warning(f"Zen Quotes API error: {e}")
        return None

    async def _try_zenquotes_api_with_philosophy(self, categories: List[str]) -> Optional[Dict[str, str]]:
        """Try Zen Quotes API with philosophy categories"""
        try:
            url = 'https://zenquotes.io/api/random'
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'text': data[0].get('q', ''),
                    'author': data[0].get('a', 'Unknown'),
                    'philosophy': random.choice(categories) if categories else 'wisdom',
                    'context': 'scenario_wisdom'
                }
        except Exception as e:
            logger.warning(f"Zen Quotes API with philosophy error: {e}")
        return None

    async def _try_adviceslip_api(self) -> Optional[Dict[str, str]]:
        """Try Advice Slip API - working and reliable"""
        try:
            url = 'https://api.adviceslip.com/advice'
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                slip = data.get('slip', {})
                return {
                    'text': slip.get('advice', ''),
                    'author': 'Advice Slip',
                    'philosophy': 'wisdom',
                    'context': 'daily_advice'
                }
        except Exception as e:
            logger.warning(f"Advice Slip API error: {e}")
        return None

    async def _try_adviceslip_api_with_philosophy(self, categories: List[str]) -> Optional[Dict[str, str]]:
        """Try Advice Slip API with philosophy categories"""
        try:
            url = 'https://api.adviceslip.com/advice'
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                slip = data.get('slip', {})
                return {
                    'text': slip.get('advice', ''),
                    'author': 'Advice Slip',
                    'philosophy': random.choice(categories) if categories else 'wisdom',
                    'context': 'scenario_advice'
                }
        except Exception as e:
            logger.warning(f"Advice Slip API with philosophy error: {e}")
        return None
    

    
    async def _try_scenario_local_fallback(self, scenario: str) -> Optional[Dict[str, str]]:
        """Local fallback with scenario-specific quotes when all APIs fail"""
        scenario_quotes = {
            'improvement': [
                {"text": "Success is not final, failure is not fatal: it is the courage to continue that counts.", "author": "Winston Churchill", "philosophy": "perseverance"},
                {"text": "The only way to do great work is to love what you do.", "author": "Steve Jobs", "philosophy": "motivation"},
                {"text": "Progress is impossible without change.", "author": "George Bernard Shaw", "philosophy": "growth"}
            ],
            'setback': [
                {"text": "The gem cannot be polished without friction, nor man perfected without trials.", "author": "Chinese Proverb", "philosophy": "resilience"},
                {"text": "When we least expect it, life sets us a challenge to test our courage and willingness to change.", "author": "Paulo Coelho", "philosophy": "challenge"},
                {"text": "The greatest glory in living lies not in never falling, but in rising every time we fall.", "author": "Nelson Mandela", "philosophy": "perseverance"}
            ],
            'excellence': [
                {"text": "Excellence is never an accident. It is always the result of high intention, sincere effort, and intelligent execution.", "author": "Aristotle", "philosophy": "excellence"},
                {"text": "The quality of a person's life is in direct proportion to their commitment to excellence.", "author": "Vince Lombardi", "philosophy": "excellence"},
                {"text": "We are what we repeatedly do. Excellence, then, is not an act, but a habit.", "author": "Aristotle", "philosophy": "consistency"}
            ],
            'struggle': [
                {"text": "The struggle you're in today is developing the strength you need for tomorrow.", "author": "Robert T. Kiyosaki", "philosophy": "strength"},
                {"text": "Character cannot be developed in ease and quiet. Only through experience of trial and suffering can the soul be strengthened.", "author": "Helen Keller", "philosophy": "perseverance"},
                {"text": "The only way to achieve the impossible is to believe it is possible.", "author": "Charles Kingsleigh", "philosophy": "belief"}
            ],
            'consistency': [
                {"text": "Consistency is the hallmark of the unimaginative.", "author": "Oscar Wilde", "philosophy": "consistency"},
                {"text": "Small daily improvements are the key to long-term success.", "author": "John Maxwell", "philosophy": "discipline"},
                {"text": "Success is the sum of small efforts, repeated day in and day out.", "author": "Robert Collier", "philosophy": "habits"}
            ],
            'reflection': [
                {"text": "The unexamined life is not worth living.", "author": "Socrates", "philosophy": "wisdom"},
                {"text": "Wisdom comes from experience, and experience comes from mistakes.", "author": "Anonymous", "philosophy": "thinking"},
                {"text": "The mind is everything. What you think you become.", "author": "Buddha", "philosophy": "awareness"}
            ],
            'growth': [
                {"text": "Growth is the only evidence of life.", "author": "John Henry Newman", "philosophy": "growth"},
                {"text": "The only person you are destined to become is the person you decide to be.", "author": "Ralph Waldo Emerson", "philosophy": "development"},
                {"text": "Change is the end result of all true learning.", "author": "Leo Buscaglia", "philosophy": "learning"}
            ],
            'breakthrough': [
                {"text": "Breakthroughs happen when you see the same thing as everyone else but think something different.", "author": "Albert Szent-Gyorgyi", "philosophy": "innovation"},
                {"text": "The moment of breakthrough is when you realize that what you've been doing isn't working.", "author": "Anonymous", "philosophy": "discovery"},
                {"text": "Every breakthrough is a breakdown of old patterns.", "author": "Anonymous", "philosophy": "achievement"}
            ],
            'first_grade': [
                {"text": "The journey of a thousand miles begins with one step.", "author": "Lao Tzu", "philosophy": "beginning"},
                {"text": "Every expert was once a beginner.", "author": "Robert T. Kiyosaki", "philosophy": "first_step"},
                {"text": "The beginning is the most important part of the work.", "author": "Plato", "philosophy": "journey"}
            ]
        }
        
        quotes = scenario_quotes.get(scenario, scenario_quotes['reflection'])
        selected_quote = random.choice(quotes)
        return {
            'text': selected_quote['text'],
            'author': selected_quote['author'],
            'philosophy': selected_quote['philosophy'],
            'context': f'scenario_{scenario}_fallback'
        }
    
    async def get_grade_notification_quote(self, old_grades: List[Dict], new_grades: List[Dict]) -> Optional[Dict[str, str]]:
        """Get a contextual quote for grade notification based on changes"""
        if not old_grades or not new_grades:
            return await self.get_scenario_quote('reflection')
        
        # Analyze grade changes
        changes = []
        total_improvement = 0
        total_decline = 0
        improvement_count = 0
        decline_count = 0
        
        for new_grade in new_grades:
            course_code = new_grade.get('code', '')
            new_total = new_grade.get('total', '0')
            
            # Find corresponding old grade
            old_grade = next((g for g in old_grades if g.get('code') == course_code), None)
            if old_grade:
                old_total = old_grade.get('total', '0')
                
                # Convert to numbers
                try:
                    old_num = float(str(old_total).replace('%', '').replace(' ', ''))
                    new_num = float(str(new_total).replace('%', '').replace(' ', ''))
                    
                    if new_num != old_num:
                        change = new_num - old_num
                        changes.append({
                            'course': new_grade.get('course', ''),
                            'old': old_num,
                            'new': new_num,
                            'change': change,
                            'improvement': change > 0
                        })
                        
                        if change > 0:
                            total_improvement += change
                            improvement_count += 1
                        else:
                            total_decline += abs(change)
                            decline_count += 1
                except (ValueError, TypeError):
                    continue
        
        if not changes:
            return await self.get_scenario_quote('reflection')
        
        # Determine scenario based on changes
        if len(changes) == 1:
            change = changes[0]
            if change['improvement']:
                if change['new'] >= 95:
                    return await self.get_scenario_quote('excellence')
                elif change['change'] >= 10:
                    return await self.get_scenario_quote('breakthrough')
                else:
                    return await self.get_scenario_quote('improvement')
            else:
                if change['change'] <= -15:
                    return await self.get_scenario_quote('struggle')
                else:
                    return await self.get_scenario_quote('setback')
        else:
            # Multiple changes
            if improvement_count > decline_count:
                if total_improvement > 20:
                    return await self.get_scenario_quote('breakthrough')
                else:
                    return await self.get_scenario_quote('improvement')
            elif decline_count > improvement_count:
                if total_decline > 20:
                    return await self.get_scenario_quote('struggle')
                else:
                    return await self.get_scenario_quote('setback')
            else:
                return await self.get_scenario_quote('consistency')
    
    async def get_analysis_quote(self, analytics: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Get a contextual quote for grade analysis based on performance"""
        summary = analytics.get('summary', {})
        avg_grade = summary.get('average_grade', 0)
        total_courses = summary.get('total_courses', 0)
        
        # First time with grades
        if total_courses <= 1:
            return await self.get_scenario_quote('first_grade')
        
        # Performance-based scenarios
        if avg_grade >= 95:
            return await self.get_scenario_quote('excellence')
        elif avg_grade >= 85:
            return await self.get_scenario_quote('improvement')
        elif avg_grade >= 75:
            return await self.get_scenario_quote('growth')
        elif avg_grade >= 65:
            return await self.get_scenario_quote('consistency')
        else:
            return await self.get_scenario_quote('reflection')
    
    async def get_achievement_quote(self, achievement_type: str) -> Optional[Dict[str, str]]:
        """Get a contextual quote for achievement unlocks"""
        achievement_scenarios = {
            'first_5_courses': 'growth',
            'first_10_courses': 'excellence',
            'excellent_grade': 'excellence',
            'excellent_streak': 'consistency',
            'consistent_performer': 'consistency'
        }
        
        scenario = achievement_scenarios.get(achievement_type, 'improvement')
        return await self.get_scenario_quote(scenario)
    
    def get_quote_for_scenario(self, scenario: str) -> Optional[Dict[str, str]]:
        """Get a quote for a specific scenario - API only now"""
        # Return None to force API usage
        return None
    
    def analyze_grades(self, user_id: int, grades: List[Dict]) -> Dict[str, Any]:
        """Analyze user grades and generate philosophical insights"""
        if not grades:
            return self._get_empty_analytics()
        
        # Calculate basic statistics
        total_courses = len(grades)
        total_ects = sum(float(grade.get('ects', 0)) for grade in grades)
        
        # Extract numeric grades
        numeric_grades = []
        for grade in grades:
            total_grade = grade.get('total', '0')
            if isinstance(total_grade, str):
                total_grade = total_grade.replace('%', '').replace(' ', '')
            try:
                numeric_grades.append(float(total_grade))
            except (ValueError, TypeError):
                continue
        
        if not numeric_grades:
            return self._get_empty_analytics()
        
        # Calculate statistics
        avg_grade = sum(numeric_grades) / len(numeric_grades)
        max_grade = max(numeric_grades)
        min_grade = min(numeric_grades)
        
        # Grade distribution (without negative labels)
        grade_distribution = self._calculate_grade_distribution(numeric_grades)
        
        # Insights
        insights = self._generate_insights(numeric_grades, avg_grade)
        
        # Achievements
        achievements = self._check_achievements(user_id, numeric_grades, total_courses)
        
        # No hardcoded quotes - API only
        quote = None
        
        return {
            'summary': {
                'total_courses': total_courses,
                'total_ects': total_ects,
                'average_grade': round(avg_grade, 2),
                'highest_grade': max_grade,
                'lowest_grade': min_grade,
                'grade_emoji': self._get_grade_emoji(avg_grade)
            },
            'distribution': grade_distribution,
            'insights': insights,
            'achievements': achievements,
            'philosophical_quote': quote,
            'last_updated': datetime.now().isoformat()
        }
    
    def _get_empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure"""
        return {
            'summary': {
                'total_courses': 0,
                'total_ects': 0,
                'average_grade': 0,
                'highest_grade': 0,
                'lowest_grade': 0,
                'grade_emoji': '📚'
            },
            'distribution': {},
            'insights': ['ابدأ رحلتك الأكاديمية'],
            'achievements': [],
            'philosophical_quote': None,
            'last_updated': datetime.now().isoformat()
        }
    
    def _calculate_grade_distribution(self, grades: List[float]) -> Dict[str, int]:
        """Calculate grade distribution without labels"""
        distribution = {
            '90-100': 0,
            '80-89': 0,
            '70-79': 0,
            '60-69': 0,
            '50-59': 0,
            '0-49': 0
        }
        
        for grade in grades:
            if grade >= 90:
                distribution['90-100'] += 1
            elif grade >= 80:
                distribution['80-89'] += 1
            elif grade >= 70:
                distribution['70-79'] += 1
            elif grade >= 60:
                distribution['60-69'] += 1
            elif grade >= 50:
                distribution['50-59'] += 1
            else:
                distribution['0-49'] += 1
        
        return distribution
    
    def _generate_insights(self, grades: List[float], avg_grade: float) -> List[str]:
        """Generate insights about grades"""
        return []
    
    def _check_achievements(self, user_id: int, grades: List[float], total_courses: int) -> List[Dict]:
        """Check and award philosophical achievements"""
        achievements = []
        
        # Load existing achievements
        try:
            with open(self.achievements_file, 'r', encoding='utf-8') as f:
                all_achievements = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            all_achievements = {}
        
        user_id_str = str(user_id)
        if user_id_str not in all_achievements:
            all_achievements[user_id_str] = []
        
        user_achievements = all_achievements[user_id_str]
        existing_achievement_ids = [a['id'] for a in user_achievements]
        
        # Check for new achievements
        new_achievements = []
        
        # Academic milestones
        if total_courses >= 5 and 'first_5_courses' not in existing_achievement_ids:
            new_achievements.append({
                'id': 'first_5_courses',
                'title': '🎓 5 مواد',
                'description': 'أكملت 5 مواد دراسية',
                'icon': '🎓',
                'unlocked_at': datetime.now().isoformat()
            })
        
        if total_courses >= 10 and 'first_10_courses' not in existing_achievement_ids:
            new_achievements.append({
                'id': 'first_10_courses',
                'title': '📚 10 مواد',
                'description': 'أكملت 10 مواد دراسية',
                'icon': '📚',
                'unlocked_at': datetime.now().isoformat()
            })
        
        # Performance achievements
        if grades and max(grades) >= 95 and 'excellent_grade' not in existing_achievement_ids:
            new_achievements.append({
                'id': 'excellent_grade',
                'title': '🏆 95%+',
                'description': 'حصلت على درجة 95% أو أعلى',
                'icon': '🏆',
                'unlocked_at': datetime.now().isoformat()
            })
        
        if grades and sum(1 for g in grades if g >= 90) >= 3 and 'excellent_streak' not in existing_achievement_ids:
            new_achievements.append({
                'id': 'excellent_streak',
                'title': '⭐ 3 ممتاز',
                'description': '3 درجات ممتازة على الأقل',
                'icon': '⭐',
                'unlocked_at': datetime.now().isoformat()
            })
        
        # Consistency achievements
        if len(grades) >= 3:
            variance = sum((g - sum(grades)/len(grades)) ** 2 for g in grades) / len(grades)
            if variance < 30 and 'consistent_performer' not in existing_achievement_ids:
                new_achievements.append({
                    'id': 'consistent_performer',
                    'title': '🎯 متسق',
                    'description': 'درجاتك متسقة ومستقرة',
                    'icon': '🎯',
                    'unlocked_at': datetime.now().isoformat()
                })
        
        # Add new achievements
        if new_achievements:
            user_achievements.extend(new_achievements)
            all_achievements[user_id_str] = user_achievements
            
            with open(self.achievements_file, 'w', encoding='utf-8') as f:
                json.dump(all_achievements, f, ensure_ascii=False, indent=2)
        
        return user_achievements
    
    def _get_grade_emoji(self, avg_grade: float) -> str:
        """Get appropriate emoji for grade level"""
        if avg_grade >= 90:
            return "🏆"
        elif avg_grade >= 80:
            return "⭐"
        elif avg_grade >= 70:
            return "📈"
        elif avg_grade >= 60:
            return "💭"
        else:
            return "🔄"
    
    def get_grade_display_options(self, user_id: int) -> Dict[str, Any]:
        """Get user's grade display preferences"""
        try:
            with open(self.analytics_file, 'r', encoding='utf-8') as f:
                all_preferences = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            all_preferences = {}
        
        user_id_str = str(user_id)
        if user_id_str not in all_preferences:
            all_preferences[user_id_str] = self._get_default_display_options()
        
        return all_preferences[user_id_str]
    
    def _get_default_display_options(self) -> Dict[str, Any]:
        """Get default grade display options"""
        return {
            'display_format': 'detailed',
            'show_charts': True,
            'show_percentage': True,
            'show_letter_grade': False,
            'show_gpa': True,
            'show_achievements': True,
            'show_philosophical': True,
            'show_insights': True,
            'time_period': 'current_semester',
            'sort_by': 'grade_desc'
        }
    
    def update_display_option(self, user_id: int, option: str, value: Any) -> bool:
        """Update user's display preference"""
        try:
            with open(self.analytics_file, 'r', encoding='utf-8') as f:
                all_preferences = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            all_preferences = {}
        
        user_id_str = str(user_id)
        if user_id_str not in all_preferences:
            all_preferences[user_id_str] = self._get_default_display_options()
        
        all_preferences[user_id_str][option] = value
        all_preferences[user_id_str]['last_updated'] = datetime.now().isoformat()
        
        try:
            with open(self.analytics_file, 'w', encoding='utf-8') as f:
                json.dump(all_preferences, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    async def format_grades_with_analytics(self, user_id: int, grades: List[Dict]) -> str:
        """Format grades with philosophical analytics"""
        analytics = self.analyze_grades(user_id, grades)
        preferences = self.get_grade_display_options(user_id)
        
        # Build the formatted message
        message = "📊 **تحليل درجاتك**\n\n"
        
        # Summary section
        summary = analytics['summary']
        message += f"🎯 **الملخص العام:**\n"
        message += f"• عدد المواد: {summary['total_courses']}\n"
        message += f"• مجموع الساعات: {summary['total_ects']}\n"
        message += f"• المعدل العام: {summary['average_grade']}% {summary['grade_emoji']}\n"
        message += f"• أعلى درجة: {summary['highest_grade']}%\n"
        message += f"• أدنى درجة: {summary['lowest_grade']}%\n\n"
        
        # Quote from API
        if preferences['show_philosophical']:
            quote = await self.get_analysis_quote(analytics)
            if quote:
                message += f"💭 **اقتباس:**\n"
                message += f"\"{quote['text']}\"\n"
                message += f"— {quote['author']}\n\n"
        
        # Insights
        if preferences['show_insights'] and analytics['insights']:
            message += "🔍 **ملاحظات:**\n"
            for insight in analytics['insights']:
                message += f"• {insight}\n"
            message += "\n"
        
        # Achievements
        if preferences['show_achievements'] and analytics['achievements']:
            message += "🏆 **إنجازاتك:**\n"
            for achievement in analytics['achievements'][-3:]:
                message += f"{achievement['icon']} {achievement['title']}\n"
            message += "\n"
        
        # Grade distribution
        if preferences['show_charts']:
            message += "📊 **التوزيع:**\n"
            for range_name, count in analytics['distribution'].items():
                if count > 0:
                    bar = "█" * min(count, 5)
                    message += f"• {range_name}%: {bar} ({count})\n"
            message += "\n"
        
        return message
    
    async def get_grade_notification(self, old_grades: List[Dict], new_grades: List[Dict]) -> Optional[str]:
        """Generate notification for grade changes using API quotes"""
        if not old_grades or not new_grades:
            return None
        
        # Get contextual quote from API
        quote = await self.get_grade_notification_quote(old_grades, new_grades)
        if not quote:
            return None
        
        # Find changed grades
        changes = []
        for new_grade in new_grades:
            course_code = new_grade.get('code', '')
            new_total = new_grade.get('total', '0')
            
            # Find corresponding old grade
            old_grade = next((g for g in old_grades if g.get('code') == course_code), None)
            if old_grade:
                old_total = old_grade.get('total', '0')
                
                # Convert to numbers
                try:
                    old_num = float(str(old_total).replace('%', '').replace(' ', ''))
                    new_num = float(str(new_total).replace('%', '').replace(' ', ''))
                    
                    if new_num != old_num:
                        changes.append({
                            'course': new_grade.get('course', ''),
                            'old': old_num,
                            'new': new_num,
                            'improvement': new_num > old_num
                        })
                except (ValueError, TypeError):
                    continue
        
        if not changes:
            return None
        
        # Generate notification with API quote
        if len(changes) == 1:
            change = changes[0]
            if change['improvement']:
                messages = [
                    f"🎉 {change['course']} تحسن من {change['old']}% إلى {change['new']}%\n\n💭 \"{quote['text']}\"\n— {quote['author']}",
                    f"🚀 {change['course']} ارتفع من {change['old']}% إلى {change['new']}%\n\n💭 \"{quote['text']}\"\n— {quote['author']}",
                    f"⭐ {change['course']} تحسن بمقدار {change['new'] - change['old']}%\n\n💭 \"{quote['text']}\"\n— {quote['author']}"
                ]
            else:
                messages = [
                    f"📉 {change['course']} انخفض من {change['old']}% إلى {change['new']}%\n\n💭 \"{quote['text']}\"\n— {quote['author']}",
                    f"🔄 {change['course']} يحتاج مراجعة\n\n💭 \"{quote['text']}\"\n— {quote['author']}",
                    f"💡 {change['course']} دعوة للتفكير\n\n💭 \"{quote['text']}\"\n— {quote['author']}"
                ]
        else:
            improvements = [c for c in changes if c['improvement']]
            if improvements:
                messages = [
                    f"🎊 {len(improvements)} مواد تحسنت!\n\n💭 \"{quote['text']}\"\n— {quote['author']}",
                    f"🌟 {len(improvements)} تحسينات جديدة!\n\n💭 \"{quote['text']}\"\n— {quote['author']}",
                    f"🏆 {len(improvements)} مواد ارتفعت درجاتها!\n\n💭 \"{quote['text']}\"\n— {quote['author']}"
                ]
            else:
                messages = [
                    f"📊 {len(changes)} مواد تغيرت درجاتها\n\n💭 \"{quote['text']}\"\n— {quote['author']}",
                    f"💡 {len(changes)} تحديثات جديدة\n\n💭 \"{quote['text']}\"\n— {quote['author']}",
                    f"📈 {len(changes)} تغييرات في الدرجات\n\n💭 \"{quote['text']}\"\n— {quote['author']}"
                ]
        
        return random.choice(messages) 