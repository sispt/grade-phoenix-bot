"""
Configuration for the Telegram University Bot.
"""

import os
import re
import logging

# Regex for semantic versioning
SEMVER_REGEX = r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$'

# Logging for config validation
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("config")

# Get version from environment
raw_version = os.getenv("BOT_VERSION", "1.0.0-dev")
if re.match(SEMVER_REGEX, raw_version):
    validated_version = raw_version
else:
    logger.error(f"Invalid BOT_VERSION '{raw_version}' (must be valid SemVer). Using '0.0.0-invalid'.")
    validated_version = "0.0.0-invalid"

# Bot configuration
CONFIG = {
    # Telegram bot token
    "TELEGRAM_TOKEN": os.getenv("TELEGRAM_TOKEN", "your_bot_token_here"),
    # Admin configuration
    "ADMIN_ID": int(os.getenv("ADMIN_ID", "123456789")),  # Telegram ID for admin
    "ADMIN_USERNAME": os.getenv("ADMIN_USERNAME", "@admin_username"),
    "ADMIN_EMAIL": os.getenv("ADMIN_EMAIL", "admin@example.com"),
    "ADMIN_NAME": os.getenv("ADMIN_NAME", "Admin User"),
    # Database configuration
    "DATABASE_URL": os.getenv("DATABASE_URL", "sqlite:///./data/bot.db"),
    "USE_POSTGRESQL": bool(os.getenv("DATABASE_URL", "").startswith("postgresql")),
    # University API configuration
    "UNIVERSITY_LOGIN_URL": "https://api.staging.sis.shamuniversity.com/portal",  # /portal for login
    "UNIVERSITY_API_URL": "https://api.staging.sis.shamuniversity.com/graphql",  # /graphql for API
    "UNIVERSITY_WEBSITE": "https://staging.sis.shamuniversity.com",
    "UNIVERSITY_NAME": "جامعة الشام",
    # Bot settings
    "BOT_NAME": "grade-phoenix-bot",
    "BOT_VERSION": validated_version,
    "BOT_DESCRIPTION": "بوت متقدم لإشعارات الدرجات مع لوحة تحكم إدارية شاملة - grade-phoenix-bot",
    # Grade check interval (minutes)
    "GRADE_CHECK_INTERVAL": int(
        os.getenv("GRADE_CHECK_INTERVAL", "15")
    ),  # fallback if not set
    # Notification settings
    # User experience settings
    "SHOW_LOADING_MESSAGES": True,
    "ENABLE_TYPING_INDICATOR": True,
    "MESSAGE_TIMEOUT_SECONDS": 30,
    "MAX_MESSAGE_LENGTH": 4096,
    # Storage settings
    "DATA_DIR": "data",
    "BACKUP_ENABLED": True,
    "BACKUP_INTERVAL_HOURS": 24,
    "MAX_BACKUP_FILES": 10,
    "BACKUP_DIR": "backups",
    "LOGS_DIR": "logs",
    # Security settings
    "ENCRYPT_PASSWORDS": True,
    "LOG_ADMIN_ACTIONS": True,
    "SESSION_TIMEOUT_HOURS": 24,
    # API headers (BeeHouse v2.1)
    "API_HEADERS": {
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9,ar;q=0.8",
        "Connection": "keep-alive",
        "Content-Type": "application/json",
        "Origin": "https://staging.sis.shamuniversity.com",
        "Referer": "https://staging.sis.shamuniversity.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
        "x-lang": "ar",
    },
    # Timezone
    "TIMEZONE": "UTC+3",
    # Logging
    "LOG_LEVEL": "DEBUG",
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

# Admin features
ADMIN_CONFIG = {
    # Dashboard settings
    "DASHBOARD_REFRESH_INTERVAL": 60,  # refresh interval in seconds
    "SHOW_DETAILED_STATS": True,
    "SHOW_USER_ACTIVITY": True,
    # User management
    "MAX_USERS_PER_PAGE": 10,
    "ENABLE_USER_SEARCH": True,
    "ENABLE_USER_EXPORT": True,
    "ENABLE_USER_DELETION": True,
    # Grade checking
    "BATCH_CHECK_ENABLED": True,
    "BATCH_CHECK_SIZE": 50,
    "BATCH_CHECK_DELAY": 2,  # delay between batches (seconds)
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
    "ADMIN_SESSION_TIMEOUT": 3600,  # admin session timeout (seconds)
    "REQUIRE_ADMIN_CONFIRMATION": True,
}

# University API queries
UNIVERSITY_QUERIES = {
    "LOGIN": """
    mutation signinUser($username: String!, $password: String!) {
        login(username: $username, password: $password)
    }
    """,
    "GET_USER_INFO": """
    query {
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
    "GET_HOMEPAGE": """
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
    "GET_COURSE_GRADES": """
    query getStudentGrades($t_grade_id: String!) {
      getStudentGrades(t_grade_id: $t_grade_id) {
        courses {
          id
          name
          code
          ects
          coursework
          final_exam
          total_grade
          letter_grade
          semester
          year
        }
      }
    }
    """,
    "GET_STUDENT_COURSES": """
    query getStudentCourses($t_grade_id: String!) {
      getStudentCourses(t_grade_id: $t_grade_id) {
        courses {
          id
          name
          code
          ects
          instructor
          semester
          year
        }
      }
    }
    """,
    "GET_GRADE_DETAILS": """
    query getGradeDetails($course_id: String!) {
      getGradeDetails(course_id: $course_id) {
        course {
          id
          name
          code
        }
        grades {
          component
          grade
          weight
          max_grade
        }
        total_grade
        letter_grade
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

# Message templates
MESSAGE_TEMPLATES = {
    "WELCOME": """
🎓 مرحباً {name}!

مرحباً بك في نظام الإشعارات الجامعية! 📚

✨ **المميزات:**
• 🔔 إشعارات فورية عند تحديث الدرجات
• 📊 عرض الدرجات الحالية
• 🔄 فحص دوري تلقائي
• �� واجهة سهلة الاستخدام

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
🔔 **grade-phoenix-bot**
👨‍💻 المطور: عبدالرحمن عبدالقادر
📧 البريد الإلكتروني: tox098123@gmail.com
    """,
}

# Error messages
ERROR_MESSAGES = {
    "LOGIN_FAILED": "🔐 تأكد من بياناتك وحاول مرة أخرى.",
    "NETWORK_ERROR": "🌐 تحقق من الاتصال وحاول مرة أخرى.",
    "API_ERROR": "🔧 جاري إصلاح النظام، حاول بعد قليل.",
    "TOKEN_EXPIRED": "⏰ انتهت الجلسة، سجل دخولك مرة أخرى.",
    "NO_GRADES": "لا توجد درجات حالياً، سنخبرك فور توفرها.",
    "GENERAL_ERROR": "🤝 حدث شيء غير متوقع، نحن هنا لمساعدتك.",
}

# Success messages
SUCCESS_MESSAGES = {
    "LOGIN_SUCCESS": "✅ تم تسجيل الدخول بنجاح!",
    "GRADES_UPDATED": "📊 تم تحديث الدرجات بنجاح!",
    "SETTINGS_SAVED": "⚙️ تم حفظ الإعدادات بنجاح!",
    "BROADCAST_SENT": "🔔 تم إرسال الإشعار العام بنجاح!",
    "BACKUP_CREATED": "💾 تم إنشاء النسخة الاحتياطية بنجاح!",
}

# Info messages
INFO_MESSAGES = {
    "NOT_REGISTERED": "❌ لم يتم تسجيلك بعد. اضغط على '🚀 تسجيل الدخول' أولاً.",
    "NO_PERMISSION": "🚫 ليس لديك صلاحية لهذه العملية.",
    "MAINTENANCE": "🔧 البوت في الصيانة. حاول لاحقاً.",
    "COMING_SOON": "🚧 هذه الميزة ستكون متاحة قريباً.",
}

# Validation rules
VALIDATION_RULES = {
    "USERNAME_MIN_LENGTH": 3,
    "USERNAME_MAX_LENGTH": 20,
    "PASSWORD_MIN_LENGTH": 6,
    "PASSWORD_MAX_LENGTH": 50,
    "MESSAGE_MAX_LENGTH": 4096,
    "BROADCAST_MAX_LENGTH": 4096,
}

# File paths
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

# Debug flag: set True to enable raw HTML debug output
PRINT_HTML_DEBUG = False

# Export config
__all__ = [
    "CONFIG",
    "ADMIN_CONFIG",
    "UNIVERSITY_QUERIES",
    "MESSAGE_TEMPLATES",
    "ERROR_MESSAGES",
    "SUCCESS_MESSAGES",
    "VALIDATION_RULES",
    "FILE_PATHS",
]
