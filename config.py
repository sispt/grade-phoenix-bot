"""
Configuration file for Telegram University Bot
"""
import os
from datetime import datetime

# Bot Configuration
CONFIG = {
    # Telegram Bot Token
    "TELEGRAM_TOKEN": os.getenv("TELEGRAM_TOKEN", "your_bot_token_here"),
    
    # Admin Configuration
    "ADMIN_ID": int(os.getenv("ADMIN_ID", "123456789")),  # Admin Telegram ID
    "ADMIN_USERNAME": os.getenv("ADMIN_USERNAME", "@Abdulrahman_lab"),
    "ADMIN_EMAIL": os.getenv("ADMIN_EMAIL", "tox098123@gmail.com"),
    
    # University API Configuration
    "UNIVERSITY_API_URL": "https://sis.shamuniversity.com/graphql",
    "UNIVERSITY_NAME": "جامعة الشام",
    "UNIVERSITY_WEBSITE": "https://sis.shamuniversity.com",
    
    # Bot Settings
    "BOT_NAME": "بوت الإشعارات الجامعية",
    "BOT_VERSION": "2.0.0",
    "BOT_DESCRIPTION": "بوت متقدم لإشعارات الدرجات مع لوحة تحكم إدارية شاملة",
    
    # Check Interval (in minutes)
    "GRADE_CHECK_INTERVAL": 5,
    
    # Notification Settings
    "ENABLE_NOTIFICATIONS": True,
    "ENABLE_ERROR_NOTIFICATIONS": True,
    "MAX_RETRY_ATTEMPTS": 3,
    
    # Storage Settings
    "DATA_DIR": "data",
    "BACKUP_ENABLED": True,
    "BACKUP_INTERVAL_HOURS": 24,
    "MAX_BACKUP_FILES": 10,
    "BACKUP_DIR": "backups",
    "LOGS_DIR": "logs",
    
    # Security Settings
    "ENCRYPT_PASSWORDS": True,
    "LOG_ADMIN_ACTIONS": True,
    "SESSION_TIMEOUT_HOURS": 24,
    
    # API Headers
    "API_HEADERS": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Referer": "https://sis.shamuniversity.com/",
        "Origin": "https://sis.shamuniversity.com",
        "Connection": "keep-alive",
        "Content-Type": "application/json"
    },
    
    # Timezone
    "TIMEZONE": "UTC+3",
    
    # Logging
    "LOG_LEVEL": "INFO",
    "LOG_FILE": "bot.log",
    "LOG_MAX_SIZE_MB": 10,
    "LOG_BACKUP_COUNT": 5,
    
    # Performance
    "MAX_CONCURRENT_REQUESTS": 10,
    "REQUEST_TIMEOUT_SECONDS": 30,
    "CACHE_DURATION_MINUTES": 5,
    # Development
    "DEBUG_MODE": False,
    "TEST_MODE": False,
    "ENABLE_METRICS": True,
}

# Admin Features Configuration
ADMIN_CONFIG = {
    # Dashboard Settings
    "DASHBOARD_REFRESH_INTERVAL": 60,  # seconds
    "SHOW_DETAILED_STATS": True,
    "SHOW_USER_ACTIVITY": True,
    
    # User Management
    "MAX_USERS_PER_PAGE": 10,
    "ENABLE_USER_SEARCH": True,
    "ENABLE_USER_EXPORT": True,
    "ENABLE_USER_DELETION": True,
    
    # Grade Checking
    "BATCH_CHECK_ENABLED": True,
    "BATCH_CHECK_SIZE": 50,
    "BATCH_CHECK_DELAY": 2,  # seconds between batches
    
    # Notifications
    "BROADCAST_ENABLED": True,
    "BROADCAST_MAX_LENGTH": 4096,
    "BROADCAST_CONFIRMATION": True,
    
    # Backup
    "BACKUP_COMPRESSION": True,
    "BACKUP_ENCRYPTION": False,
    "BACKUP_RETENTION_DAYS": 30,
    
    # Monitoring
    "ERROR_LOG_RETENTION_DAYS": 7,
    "ACTIVITY_LOG_RETENTION_DAYS": 30,
    "PERFORMANCE_MONITORING": True,
    
    # Security
    "ADMIN_ACTION_LOGGING": True,
    "ADMIN_SESSION_TIMEOUT": 3600,  # seconds
    "REQUIRE_ADMIN_CONFIRMATION": True,
}

# University API Queries
UNIVERSITY_QUERIES = {
    "LOGIN": """
    mutation Login($username: String!, $password: String!) {
        login(username: $username, password: $password) {
            token
            user {
                id
                username
                fullname
                email
            }
        }
    }
    """,
    
    "GET_USER_INFO": """
    {
      getGUI {
        user {
          id
          firstname
          lastname
          fullname
          email
          username
        }
      }
    }
    """,
    
    "GET_GRADES": """
    query getPage($name: String!, $params: [PageParam!]) {
      getPage(name: $name, params: $params) {
        panels {
          blocks {
            title
            body
          }
        }
      }
    }
    """,
    
    "TEST_TOKEN": """
    query TestToken {
        getGUI {
            user {
                id
                username
            }
        }
    }
    """,
}

# Message Templates
MESSAGE_TEMPLATES = {
    "WELCOME": """
🎓 مرحباً {name}!

مرحباً بك في بوت الإشعارات الجامعية! 📚

✨ **المميزات:**
• 🔔 إشعارات فورية عند تحديث الدرجات
• 📊 عرض الدرجات الحالية
• 🔄 فحص دوري تلقائي
• 📱 واجهة سهلة الاستخدام

🎯 **للبدء:**
اضغط على "🚀 تسجيل الدخول" لإدخال بياناتك الجامعية
    """,
    
    "GRADE_UPDATE": """
🎓 **تم تحديث درجاتك!**

📚 **المادة:** {course_name}
🔬 **العملي:** {practical_grade}
✍️ **التحريري:** {theoretical_grade}
🎯 **النهائي:** {final_grade}

🕒 **تاريخ التحديث:** {update_time}
    """,
    
    "ADMIN_DASHBOARD": """
🎛️ **لوحة التحكم الإدارية**

📊 **إحصائيات المستخدمين:**
• 👥 إجمالي المستخدمين: {total_users}
• ✅ المستخدمين النشطين: {active_users}
• ❌ المستخدمين غير النشطين: {inactive_users}
• 📈 نسبة النشاط: {activity_rate:.1f}%

🔔 **الإشعارات:**
• 📤 إجمالي الإشعارات: {total_notifications}
• ⚠️ الأخطاء (24 ساعة): {recent_errors}
    """,
    
    "BROADCAST_FOOTER": """
---
🔔 **بوت الإشعارات الجامعية**
👨‍💻 المطور: عبدالرحمن عبدالقادر
📧 البريد الإلكتروني: tox098123@gmail.com
    """,
}

# Error Messages
ERROR_MESSAGES = {
    "LOGIN_FAILED": "❌ فشل تسجيل الدخول. تأكد من صحة بياناتك.",
    "NETWORK_ERROR": "🌐 خطأ في الاتصال. تحقق من الإنترنت.",
    "API_ERROR": "🔧 خطأ في النظام. حاول لاحقاً.",
    "TOKEN_EXPIRED": "⏰ انتهت صلاحية الجلسة. سجل دخولك مرة أخرى.",
    "NO_GRADES": "📭 لا توجد درجات متاحة حالياً.",
    "GENERAL_ERROR": "❌ حدث خطأ. حاول مرة أخرى.",
}

# Success Messages
SUCCESS_MESSAGES = {
    "LOGIN_SUCCESS": "✅ تم تسجيل الدخول بنجاح!",
    "GRADES_UPDATED": "📊 تم تحديث الدرجات بنجاح!",
    "SETTINGS_SAVED": "⚙️ تم حفظ الإعدادات بنجاح!",
    "BROADCAST_SENT": "🔔 تم إرسال الإشعار العام بنجاح!",
    "BACKUP_CREATED": "💾 تم إنشاء النسخة الاحتياطية بنجاح!",
}

# Info Messages
INFO_MESSAGES = {
    "NOT_REGISTERED": "❌ لم يتم تسجيلك بعد. اضغط على '🚀 تسجيل الدخول' أولاً.",
    "NO_PERMISSION": "🚫 ليس لديك صلاحية لهذه العملية.",
    "MAINTENANCE": "🔧 البوت في الصيانة. حاول لاحقاً.",
    "COMING_SOON": "🚧 هذه الميزة ستكون متاحة قريباً.",
}

# Validation Rules
VALIDATION_RULES = {
    "USERNAME_MIN_LENGTH": 3,
    "USERNAME_MAX_LENGTH": 20,
    "PASSWORD_MIN_LENGTH": 6,
    "PASSWORD_MAX_LENGTH": 50,
    "MESSAGE_MAX_LENGTH": 4096,
    "BROADCAST_MAX_LENGTH": 4096,
}

# File Paths
FILE_PATHS = {
    "DATA_DIR": "data",
    "LOGS_DIR": "logs",
    "BACKUP_DIR": "backups",
    "CONFIG_FILE": "config.py",
    "STORAGE_FILE": "storage.py",
    "ADMIN_STATS_FILE": "admin_stats.json",
    "USER_DATA_FILE": "data/users.json",
    "GRADES_FILE_PREFIX": "data/grades_",
}

# Export configuration
__all__ = [
    'CONFIG', 'ADMIN_CONFIG', 'UNIVERSITY_QUERIES', 
    'MESSAGE_TEMPLATES', 'ERROR_MESSAGES', 'SUCCESS_MESSAGES',
    'VALIDATION_RULES', 'FILE_PATHS'
]
