"""
⌨️ Keyboard Layouts
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from config import CONFIG

def get_main_keyboard():
    """Get main keyboard for regular users"""
    keyboard = [
        [
            KeyboardButton("🚀 تسجيل الدخول"),
            KeyboardButton("📊 فحص الدرجات")
        ],
        [
            KeyboardButton("👤 معلوماتي"),
            KeyboardButton("⚙️ الإعدادات")
        ],
        [
            KeyboardButton("❓ المساعدة"),
            KeyboardButton("📞 الدعم")
        ]
    ]
    
    # Add admin keyboard if user is admin
    if CONFIG.get("ADMIN_ID"):
        keyboard.append([KeyboardButton("🎛️ لوحة التحكم")])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_main_keyboard_with_relogin():
    """Get main keyboard with re-login option for users with expired sessions"""
    keyboard = [
        [
            KeyboardButton("🚀 تسجيل الدخول"),
            KeyboardButton("📊 فحص الدرجات")
        ],
        [
            KeyboardButton("🔄 إعادة تسجيل الدخول"),
            KeyboardButton("👤 معلوماتي")
        ],
        [
            KeyboardButton("⚙️ الإعدادات"),
            KeyboardButton("❓ المساعدة")
        ],
        [
            KeyboardButton("📞 الدعم")
        ]
    ]
    
    # Add admin keyboard if user is admin
    if CONFIG.get("ADMIN_ID"):
        keyboard.append([KeyboardButton("🎛️ لوحة التحكم")])
    
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_admin_keyboard():
    """Get admin keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("📊 إحصائيات مفصلة", callback_data="admin_stats"),
            InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton("🔔 إشعار عام", callback_data="admin_broadcast"),
            InlineKeyboardButton("🔄 فحص جميع الدرجات", callback_data="admin_check_grades")
        ],
        [
            InlineKeyboardButton("💾 نسخة احتياطية", callback_data="admin_backup"),
            InlineKeyboardButton("⚙️ الإعدادات", callback_data="admin_settings")
        ],
        [
            InlineKeyboardButton("🔙 العودة", callback_data="admin_dashboard")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def get_cancel_keyboard():
    """Get cancel keyboard"""
    keyboard = [[KeyboardButton("❌ إلغاء")]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True) 