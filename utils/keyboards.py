"""
⌨️ Custom Keyboards (Final Version)
"""
from telegram import ReplyKeyboardMarkup

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Returns the main keyboard layout for REGISTERED users."""
    keyboard = [
        ["📊 فحص الدرجات", "❓ المساعدة"],
        ["👤 معلوماتي", "⚙️ الإعدادات"],
        ["📞 الدعم", "🎛️ لوحة التحكم"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_unregistered_keyboard() -> ReplyKeyboardMarkup:
    """Returns the keyboard for UNREGISTERED users, featuring the login button."""
    keyboard = [
        ["🚀 تسجيل الدخول", "❓ المساعدة"], # Prominent login button
        ["📞 الدعم"] # Still allow access to support
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_main_keyboard_with_relogin() -> ReplyKeyboardMarkup:
    """Returns the keyboard for REGISTERED users whose token expired, with relogin option."""
    keyboard = [
        ["🔄 إعادة تسجيل الدخول", "📊 فحص الدرجات"], # Re-login button for known users
        ["👤 معلوماتي", "⚙️ الإعدادات"],
        ["📞 الدعم", "🎛️ لوحة التحكم"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """Returns the admin keyboard layout."""
    keyboard = [
        ["📊 الإحصائيات", "👥 قائمة المستخدمين"],
        ["🔔 إشعار عام", "⚙️ حالة الخادم"], 
        ["🔙 العودة"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Returns a simple keyboard with a cancel button for conversations."""
    keyboard = [["❌ إلغاء"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True) # One-time so it disappears after cancel