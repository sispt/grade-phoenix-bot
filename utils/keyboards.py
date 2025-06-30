"""
⌨️ Custom Keyboards
"""
from telegram import ReplyKeyboardMarkup

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Returns the main keyboard layout."""
    keyboard = [
        ["📊 فحص الدرجات", "❓ المساعدة"],
        ["👤 معلوماتي", "⚙️ الإعدادات"],
        ["📞 الدعم", "🎛️ لوحة التحكم"]
    ]
    # Key: resize_keyboard=True makes it fit the screen better.
    # Key: one_time_keyboard=False makes it persistent.
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_main_keyboard_with_relogin() -> ReplyKeyboardMarkup:
    """Returns the main keyboard with a 'relogin' option (e.g., when token expires)."""
    keyboard = [
        ["🚀 تسجيل الدخول", "📊 فحص الدرجات"], # Added explicit "Register" button
        ["👤 معلوماتي", "⚙️ الإعدادات"],
        ["📞 الدعم", "🎛️ لوحة التحكم"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """Returns the admin keyboard layout."""
    keyboard = [
        ["📊 إحصائيات", "👥 إدارة المستخدمين"],
        ["🔔 إشعار عام", "⚙️ حالة الخادم"], # Changed button text to match dashboard
        ["🔙 العودة"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Returns a simple keyboard with a cancel button for conversations."""
    keyboard = [["❌ إلغاء"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True) # One-time so it disappears after cancel