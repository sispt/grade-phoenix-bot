"""
⚙️ User Settings Management
Handles user preferences and configuration settings.
"""
from typing import Dict, Any, Optional
from datetime import datetime
import json
import os

class UserSettings:
    """Manages user settings and preferences"""
    
    def __init__(self, user_storage):
        self.user_storage = user_storage
        self.settings_file = "data/user_settings.json"
        self._ensure_settings_file()
    
    def _ensure_settings_file(self):
        """Ensure settings file exists with default structure"""
        if not os.path.exists(self.settings_file):
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
    
    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get user settings, create defaults if not exist"""
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                all_settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            all_settings = {}
        
        user_id_str = str(user_id)
        if user_id_str not in all_settings:
            # Create default settings
            all_settings[user_id_str] = self._get_default_settings()
            self._save_all_settings(all_settings)
        
        return all_settings[user_id_str]
    
    def update_user_setting(self, user_id: int, setting_key: str, value: Any) -> bool:
        """Update a specific user setting"""
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                all_settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            all_settings = {}
        
        user_id_str = str(user_id)
        if user_id_str not in all_settings:
            all_settings[user_id_str] = self._get_default_settings()
        
        all_settings[user_id_str][setting_key] = value
        all_settings[user_id_str]['last_updated'] = datetime.now().isoformat()
        
        return self._save_all_settings(all_settings)
    
    def _get_default_settings(self) -> Dict[str, Any]:
        """Get default user settings"""
        return {
            # Notification Settings
            'notifications': {
                'grade_notifications': True,
                'broadcast_notifications': True,
                'notification_time': 'immediate',  # immediate, daily, weekly
                'notification_sound': True,
                'notification_vibration': True
            },
            
            # Privacy Settings
            'privacy': {
                'show_profile_info': True,
                'share_statistics': False,
                'data_retention_days': 365
            },
            
            # Language Settings
            'language': {
                'preferred_language': 'ar',  # ar, en, auto
                'auto_detect': True
            },
            
            # Grade Display Settings
            'grade_display': {
                'show_percentage': True,
                'show_letter_grade': False,
                'show_gpa': True,
                'display_format': 'detailed',  # simple, detailed, compact
                'show_charts': True,
                'time_period': 'current_semester'  # current_semester, all_time, custom
            },
            
            # UI Settings
            'ui': {
                'theme': 'default',  # default, dark, light
                'compact_mode': False,
                'show_emojis': True,
                'keyboard_layout': 'standard'  # standard, compact, minimal
            },
            
            # System Settings
            'system': {
                'auto_backup': True,
                'sync_frequency': 'daily',  # hourly, daily, weekly
                'debug_mode': False,
                'beta_features': False
            },
            
            # Timestamps
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
    
    def _save_all_settings(self, all_settings: Dict[str, Any]) -> bool:
        """Save all settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(all_settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def get_settings_summary(self, user_id: int) -> str:
        """Get a human-readable summary of user settings"""
        settings = self.get_user_settings(user_id)
        
        summary = "⚙️ **إعداداتك الحالية:**\n\n"
        
        # Notification settings
        notif = settings['notifications']
        summary += "🔔 **الإشعارات:**\n"
        summary += f"• إشعارات الدرجات: {'✅' if notif['grade_notifications'] else '❌'}\n"
        summary += f"• إشعارات البث: {'✅' if notif['broadcast_notifications'] else '❌'}\n"
        summary += f"• وقت الإشعارات: {notif['notification_time']}\n\n"
        
        # Privacy settings
        privacy = settings['privacy']
        summary += "🔒 **الخصوصية:**\n"
        summary += f"• عرض المعلومات: {'✅' if privacy['show_profile_info'] else '❌'}\n"
        summary += f"• مشاركة الإحصائيات: {'✅' if privacy['share_statistics'] else '❌'}\n\n"
        
        # Language settings
        lang = settings['language']
        summary += "🌐 **اللغة:**\n"
        summary += f"• اللغة المفضلة: {lang['preferred_language']}\n"
        summary += f"• الكشف التلقائي: {'✅' if lang['auto_detect'] else '❌'}\n\n"
        
        # Grade display settings
        grade = settings['grade_display']
        summary += "📊 **عرض الدرجات:**\n"
        summary += f"• تنسيق العرض: {grade['display_format']}\n"
        summary += f"• الرسوم البيانية: {'✅' if grade['show_charts'] else '❌'}\n"
        
        return summary
    
    def reset_to_defaults(self, user_id: int) -> bool:
        """Reset user settings to defaults"""
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                all_settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            all_settings = {}
        
        user_id_str = str(user_id)
        all_settings[user_id_str] = self._get_default_settings()
        
        return self._save_all_settings(all_settings)
    
    def export_settings(self, user_id: int) -> Dict[str, Any]:
        """Export user settings for backup"""
        settings = self.get_user_settings(user_id)
        return {
            'user_id': user_id,
            'export_date': datetime.now().isoformat(),
            'settings': settings
        }
    
    def import_settings(self, user_id: int, settings_data: Dict[str, Any]) -> bool:
        """Import user settings from backup"""
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                all_settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            all_settings = {}
        
        user_id_str = str(user_id)
        all_settings[user_id_str] = settings_data.get('settings', self._get_default_settings())
        all_settings[user_id_str]['last_updated'] = datetime.now().isoformat()
        
        return self._save_all_settings(all_settings)

# Settings categories for keyboard generation
SETTINGS_CATEGORIES = {
    'notifications': {
        'title': '🔔 إعدادات الإشعارات',
        'description': 'تخصيص إعدادات الإشعارات والتنبيهات',
        'icon': '🔔'
    },
    'privacy': {
        'title': '🔒 إعدادات الخصوصية',
        'description': 'إدارة الخصوصية والأمان',
        'icon': '🔒'
    },
    'language': {
        'title': '🌐 إعدادات اللغة',
        'description': 'تغيير اللغة والترجمة',
        'icon': '🌐'
    },
    'grade_display': {
        'title': '📊 إعدادات عرض الدرجات',
        'description': 'تخصيص طريقة عرض الدرجات',
        'icon': '📊'
    },
    'ui': {
        'title': '🎨 إعدادات الواجهة',
        'description': 'تخصيص مظهر البوت',
        'icon': '🎨'
    },
    'system': {
        'title': '⚙️ إعدادات النظام',
        'description': 'إعدادات النظام المتقدمة',
        'icon': '⚙️'
    }
} 