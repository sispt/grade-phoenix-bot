"""
⌨️ Custom Keyboards (Enhanced Version)
"""
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton

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
    """Returns the admin keyboard layout - simplified to match dashboard functionality."""
    keyboard = [
        ["🎛️ لوحة التحكم"], # Single button to access the inline dashboard
        ["🔙 العودة"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Returns a simple keyboard with a cancel button for conversations."""
    keyboard = [["❌ إلغاء"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True) # One-time so it disappears after cancel

def remove_keyboard() -> ReplyKeyboardRemove:
    """Returns a keyboard removal markup to hide the current keyboard."""
    return ReplyKeyboardRemove(remove_keyboard=True, selective=False)

def get_error_recovery_keyboard() -> ReplyKeyboardMarkup:
    """Returns a keyboard for error recovery scenarios."""
    keyboard = [
        ["🔄 إعادة المحاولة", "🏠 العودة للرئيسية"],
        ["📞 الدعم", "❓ المساعدة"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

def get_enhanced_admin_dashboard_keyboard() -> InlineKeyboardMarkup:
    """Returns an enhanced admin dashboard inline keyboard with better organization."""
    buttons = [
        # Main actions row
        [InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="users_overview"),
         InlineKeyboardButton("📊 التحليل والإحصائيات", callback_data="analysis")],
        
        # Communication row
        [InlineKeyboardButton("📢 بث رسالة", callback_data="broadcast"),
         InlineKeyboardButton("📋 تقرير النظام", callback_data="system_report")],
        
        # User management actions
        [InlineKeyboardButton("🔍 بحث عن مستخدم", callback_data="user_search"),
         InlineKeyboardButton("🗑️ حذف مستخدم", callback_data="delete_user")],
        
        # System actions
        [InlineKeyboardButton("🔄 تحديث البيانات", callback_data="refresh_data"),
         InlineKeyboardButton("💾 نسخة احتياطية", callback_data="backup_data")],
        
        # Close button
        [InlineKeyboardButton("❌ إغلاق لوحة التحكم", callback_data="close_dashboard")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_user_management_keyboard(page=1, total_pages=1) -> InlineKeyboardMarkup:
    """Returns a keyboard for user management with pagination."""
    buttons = []
    
    # Navigation row
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"view_users:{page-1}"))
    nav_buttons.append(InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="current_page"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("التالي ➡️", callback_data=f"view_users:{page+1}"))
    if nav_buttons:
        buttons.append(nav_buttons)
    
    # Action buttons
    buttons.extend([
        [InlineKeyboardButton("🔍 بحث عن مستخدم", callback_data="user_search")],
        [InlineKeyboardButton("🗑️ حذف مستخدم", callback_data="delete_user")],
        [InlineKeyboardButton("📊 إحصائيات المستخدمين", callback_data="users_stats")],
        [InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="back_to_dashboard")]
    ])
    
    return InlineKeyboardMarkup(buttons)

def get_broadcast_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Returns a keyboard for broadcast confirmation."""
    buttons = [
        [InlineKeyboardButton("✅ تأكيد البث", callback_data="confirm_broadcast"),
         InlineKeyboardButton("❌ إلغاء", callback_data="cancel_broadcast")],
        [InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="back_to_dashboard")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_system_actions_keyboard() -> InlineKeyboardMarkup:
    """Returns a keyboard for system maintenance actions."""
    buttons = [
        [InlineKeyboardButton("🔄 تحديث قاعدة البيانات", callback_data="refresh_database"),
         InlineKeyboardButton("💾 إنشاء نسخة احتياطية", callback_data="create_backup")],
        [InlineKeyboardButton("📊 حالة النظام", callback_data="system_status"),
         InlineKeyboardButton("🧹 تنظيف البيانات", callback_data="cleanup_data")],
        [InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="back_to_dashboard")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_settings_main_keyboard() -> InlineKeyboardMarkup:
    """Returns the main settings keyboard with categories."""
    buttons = [
        [InlineKeyboardButton("🔔 إعدادات الإشعارات", callback_data="settings_notifications"),
         InlineKeyboardButton("🔒 إعدادات الخصوصية", callback_data="settings_privacy")],
        [InlineKeyboardButton("🌐 إعدادات اللغة", callback_data="settings_language"),
         InlineKeyboardButton("📊 إعدادات عرض الدرجات", callback_data="settings_grade_display")],
        [InlineKeyboardButton("🎨 إعدادات الواجهة", callback_data="settings_ui"),
         InlineKeyboardButton("⚙️ إعدادات النظام", callback_data="settings_system")],
        [InlineKeyboardButton("📋 ملخص الإعدادات", callback_data="settings_summary"),
         InlineKeyboardButton("🔄 إعادة تعيين", callback_data="settings_reset")],
        [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_notification_settings_keyboard() -> InlineKeyboardMarkup:
    """Returns keyboard for notification settings."""
    buttons = [
        [InlineKeyboardButton("📊 إشعارات الدرجات", callback_data="toggle_grade_notifications"),
         InlineKeyboardButton("📢 إشعارات البث", callback_data="toggle_broadcast_notifications")],
        [InlineKeyboardButton("⏰ وقت الإشعارات", callback_data="notification_time"),
         InlineKeyboardButton("🔊 صوت الإشعارات", callback_data="toggle_notification_sound")],
        [InlineKeyboardButton("📳 اهتزاز الإشعارات", callback_data="toggle_notification_vibration")],
        [InlineKeyboardButton("🔙 العودة للإعدادات", callback_data="back_to_settings")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_privacy_settings_keyboard() -> InlineKeyboardMarkup:
    """Returns keyboard for privacy settings."""
    buttons = [
        [InlineKeyboardButton("👁️ عرض المعلومات الشخصية", callback_data="toggle_show_profile"),
         InlineKeyboardButton("📊 مشاركة الإحصائيات", callback_data="toggle_share_stats")],
        [InlineKeyboardButton("🗑️ حذف البيانات", callback_data="delete_user_data"),
         InlineKeyboardButton("📅 فترة الاحتفاظ", callback_data="data_retention")],
        [InlineKeyboardButton("🔙 العودة للإعدادات", callback_data="back_to_settings")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_language_settings_keyboard() -> InlineKeyboardMarkup:
    """Returns keyboard for language settings."""
    buttons = [
        [InlineKeyboardButton("🇸🇦 العربية", callback_data="set_language_ar"),
         InlineKeyboardButton("🇺🇸 English", callback_data="set_language_en")],
        [InlineKeyboardButton("🔄 تلقائي", callback_data="set_language_auto"),
         InlineKeyboardButton("🔍 الكشف التلقائي", callback_data="toggle_auto_detect")],
        [InlineKeyboardButton("🔙 العودة للإعدادات", callback_data="back_to_settings")]
    ]
    return InlineKeyboardMarkup(buttons)



def get_ui_settings_keyboard() -> InlineKeyboardMarkup:
    """Returns keyboard for UI settings."""
    buttons = [
        [InlineKeyboardButton("🎨 المظهر", callback_data="ui_theme"),
         InlineKeyboardButton("📱 الوضع المضغوط", callback_data="toggle_compact_mode")],
        [InlineKeyboardButton("😊 الإيموجي", callback_data="toggle_show_emojis"),
         InlineKeyboardButton("⌨️ تخطيط لوحة المفاتيح", callback_data="keyboard_layout")],
        [InlineKeyboardButton("🔙 العودة للإعدادات", callback_data="back_to_settings")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_system_settings_keyboard() -> InlineKeyboardMarkup:
    """Returns keyboard for system settings."""
    buttons = [
        [InlineKeyboardButton("💾 النسخ الاحتياطي التلقائي", callback_data="toggle_auto_backup"),
         InlineKeyboardButton("🔄 تكرار المزامنة", callback_data="sync_frequency")],
        [InlineKeyboardButton("🐛 وضع التصحيح", callback_data="toggle_debug_mode"),
         InlineKeyboardButton("🧪 الميزات التجريبية", callback_data="toggle_beta_features")],
        [InlineKeyboardButton("📤 تصدير الإعدادات", callback_data="export_settings"),
         InlineKeyboardButton("📥 استيراد الإعدادات", callback_data="import_settings")],
        [InlineKeyboardButton("🔙 العودة للإعدادات", callback_data="back_to_settings")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_grade_display_settings_keyboard() -> InlineKeyboardMarkup:
    """Returns keyboard for grade display settings."""
    buttons = [
        [InlineKeyboardButton("📋 تنسيق العرض", callback_data="grade_display_format"),
         InlineKeyboardButton("📈 الرسوم البيانية", callback_data="toggle_grade_charts")],
        [InlineKeyboardButton("📊 النسبة المئوية", callback_data="toggle_show_percentage"),
         InlineKeyboardButton("🎯 الدرجة الحرفية", callback_data="toggle_letter_grade")],
        [InlineKeyboardButton("📅 الفترة الزمنية", callback_data="grade_time_period"),
         InlineKeyboardButton("📊 المعدل التراكمي", callback_data="toggle_show_gpa")],
        [InlineKeyboardButton("💭 الاقتباسات", callback_data="toggle_philosophical_quotes"),
         InlineKeyboardButton("🔍 الملاحظات", callback_data="toggle_insights")],
        [InlineKeyboardButton("🏆 الإنجازات", callback_data="toggle_achievements")],
        [InlineKeyboardButton("🔙 العودة للإعدادات", callback_data="back_to_settings")]
    ]
    return InlineKeyboardMarkup(buttons)