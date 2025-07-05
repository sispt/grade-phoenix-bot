"""
⌨️ Custom Keyboards (Enhanced Version)
Improved UX with clearer labels and better organization
"""

from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from config import CONFIG


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Main keyboard for registered users."""
    keyboard = [
        ["📊 درجات الفصل الحالي", "📚 درجات الفصل السابق"],
        ["👤 معلوماتي الشخصية", "⚙️ الإعدادات والتخصيص"],
        ["📞 الدعم الفني", "❓ المساعدة والدليل"],
        ["❌ إلغاء"],
        ["🚪 تسجيل الخروج"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_unregistered_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard for unregistered users."""
    keyboard = [
        ["🚀 تسجيل الدخول للجامعة"],
        ["❓ المساعدة", "📞 الدعم الفني"],
        ["❌ إلغاء"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """Admin keyboard layout."""
    keyboard = [["🎛️ لوحة التحكم الإدارية"], ["🔙 العودة للوحة الرئيسية"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard with a cancel button."""
    keyboard = [["❌ إلغاء"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def remove_keyboard() -> ReplyKeyboardRemove:
    """Remove the current keyboard."""
    return ReplyKeyboardRemove(selective=False)


def get_error_recovery_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard for error recovery options."""
    keyboard = [
        ["🔄 إعادة المحاولة", "🏠 العودة للرئيسية"],
        ["📞 الدعم الفني", "❓ المساعدة والدليل"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def get_registration_keyboard() -> ReplyKeyboardMarkup:
    """Keyboard for registration process."""
    keyboard = [["❌ إلغاء التسجيل"], ["🔙 العودة للرئيسية"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def get_enhanced_admin_dashboard_keyboard() -> InlineKeyboardMarkup:
    """Admin dashboard inline keyboard."""
    buttons = [
        # Button groups for admin dashboard
        [
            InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="users_overview"),
            InlineKeyboardButton("📊 التحليل والإحصائيات", callback_data="analysis"),
        ],
        [
            InlineKeyboardButton("📢 بث رسالة للجميع", callback_data="broadcast"),
            InlineKeyboardButton(
                "💬 إرسال حكمة اليوم", callback_data="send_quote_to_all"
            ),
            InlineKeyboardButton("📋 تقرير حالة النظام", callback_data="system_report"),
        ],
        [
            InlineKeyboardButton("🔍 بحث عن مستخدم", callback_data="user_search"),
            InlineKeyboardButton("🗑️ حذف مستخدم", callback_data="delete_user"),
        ],
        [
            InlineKeyboardButton("🛠️ فحص درجات مستخدم", callback_data="force_grade_check"),
            InlineKeyboardButton("🔄 فحص درجات للجميع", callback_data="force_grade_check_all"),
        ],
        [
            InlineKeyboardButton("🔄 تحديث البيانات", callback_data="refresh_data"),
            InlineKeyboardButton("💾 إنشاء نسخة احتياطية", callback_data="backup_data"),
        ],
        [InlineKeyboardButton("❌ إغلاق لوحة التحكم", callback_data="close_dashboard")],
    ]
    return InlineKeyboardMarkup(buttons)


def get_user_management_keyboard(page=1, total_pages=1) -> InlineKeyboardMarkup:
    """Keyboard for user management with pagination."""
    buttons = []

    # Pagination controls
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ السابق", callback_data=f"view_users:{page-1}")
        )
    nav_buttons.append(
        InlineKeyboardButton(f"📄 {page}/{total_pages}", callback_data="current_page")
    )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton("التالي ➡️", callback_data=f"view_users:{page+1}")
        )
    if nav_buttons:
        buttons.append(nav_buttons)

    # User management actions
    buttons.extend(
        [
            [InlineKeyboardButton("🔍 بحث عن مستخدم", callback_data="user_search")],
            [InlineKeyboardButton("🗑️ حذف مستخدم", callback_data="delete_user")],
            [
                InlineKeyboardButton(
                    "📊 إحصائيات المستخدمين", callback_data="users_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 العودة للوحة التحكم", callback_data="back_to_dashboard"
                )
            ],
        ]
    )

    return InlineKeyboardMarkup(buttons)


def get_broadcast_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for broadcast confirmation."""
    buttons = [
        [
            InlineKeyboardButton(
                "✅ تأكيد البث للجميع", callback_data="confirm_broadcast"
            ),
            InlineKeyboardButton("❌ إلغاء البث", callback_data="cancel_broadcast"),
        ],
        [
            InlineKeyboardButton(
                "🔙 العودة للوحة التحكم", callback_data="back_to_dashboard"
            )
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def get_system_actions_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for system maintenance."""
    buttons = [
        [
            InlineKeyboardButton(
                "🔄 تحديث قاعدة البيانات", callback_data="refresh_database"
            ),
            InlineKeyboardButton(
                "💾 إنشاء نسخة احتياطية", callback_data="create_backup"
            ),
        ],
        [
            InlineKeyboardButton("📊 حالة النظام", callback_data="system_status"),
            InlineKeyboardButton("🧹 تنظيف البيانات", callback_data="cleanup_data"),
        ],
        [
            InlineKeyboardButton(
                "🔙 العودة للوحة التحكم", callback_data="back_to_dashboard"
            )
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def get_settings_main_keyboard() -> InlineKeyboardMarkup:
    """Main settings keyboard with GitHub button only."""
    buttons = [
        [
            InlineKeyboardButton("🔗 GitHub Repo", url="https://github.com/sispt/grade-phoenix-bot?refresh"),
        ],
        [
            InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")
        ],
        [
            InlineKeyboardButton("❌ إلغاء", callback_data="cancel_action")
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def get_notification_settings_keyboard() -> InlineKeyboardMarkup:
    """Notification settings keyboard."""
    buttons = [
        [
            InlineKeyboardButton(
                "📊 إشعارات الدرجات", callback_data="toggle_grade_notifications"
            ),
            InlineKeyboardButton(
                "📢 إشعارات البث", callback_data="toggle_broadcast_notifications"
            ),
        ],
        [
            InlineKeyboardButton("⏰ وقت الإشعارات", callback_data="notification_time"),
            InlineKeyboardButton(
                "🔊 صوت الإشعارات", callback_data="toggle_notification_sound"
            ),
        ],
        [
            InlineKeyboardButton(
                "📳 اهتزاز الإشعارات", callback_data="toggle_notification_vibration"
            )
        ],
        [InlineKeyboardButton("🔙 العودة للإعدادات", callback_data="back_to_settings")],
    ]
    return InlineKeyboardMarkup(buttons)


def get_privacy_settings_keyboard() -> InlineKeyboardMarkup:
    """Privacy settings keyboard."""
    buttons = [
        [
            InlineKeyboardButton(
                "👁️ عرض المعلومات الشخصية", callback_data="toggle_show_profile"
            ),
            InlineKeyboardButton(
                "📊 مشاركة الإحصائيات", callback_data="toggle_share_stats"
            ),
        ],
        [
            InlineKeyboardButton("🗑️ حذف البيانات", callback_data="delete_user_data"),
            InlineKeyboardButton("📅 فترة الاحتفاظ", callback_data="data_retention"),
        ],
        [InlineKeyboardButton("🔙 العودة للإعدادات", callback_data="back_to_settings")],
    ]
    return InlineKeyboardMarkup(buttons)


def get_language_settings_keyboard() -> InlineKeyboardMarkup:
    """Language settings keyboard."""
    buttons = [
        [
            InlineKeyboardButton("🇸🇦 العربية", callback_data="set_language_ar"),
            InlineKeyboardButton("🇺🇸 English", callback_data="set_language_en"),
        ],
        [
            InlineKeyboardButton("🔄 تلقائي", callback_data="set_language_auto"),
            InlineKeyboardButton(
                "🔍 الكشف التلقائي", callback_data="toggle_auto_detect"
            ),
        ],
        [InlineKeyboardButton("🔙 العودة للإعدادات", callback_data="back_to_settings")],
    ]
    return InlineKeyboardMarkup(buttons)


def get_ui_settings_keyboard() -> InlineKeyboardMarkup:
    """UI settings keyboard."""
    buttons = [
        [
            InlineKeyboardButton("🎨 المظهر", callback_data="ui_theme"),
            InlineKeyboardButton(
                "📱 الوضع المضغوط", callback_data="toggle_compact_mode"
            ),
        ],
        [
            InlineKeyboardButton("😊 الإيموجي", callback_data="toggle_show_emojis"),
            InlineKeyboardButton(
                "⌨️ تخطيط لوحة المفاتيح", callback_data="keyboard_layout"
            ),
        ],
        [InlineKeyboardButton("🔙 العودة للإعدادات", callback_data="back_to_settings")],
    ]
    return InlineKeyboardMarkup(buttons)


def get_system_settings_keyboard() -> InlineKeyboardMarkup:
    """System settings keyboard."""
    buttons = [
        [
            InlineKeyboardButton(
                "💾 النسخ الاحتياطي التلقائي", callback_data="toggle_auto_backup"
            ),
            InlineKeyboardButton("🔄 تكرار المزامنة", callback_data="sync_frequency"),
        ],
        [
            InlineKeyboardButton("🐛 وضع التصحيح", callback_data="toggle_debug_mode"),
            InlineKeyboardButton(
                "🧪 الميزات التجريبية", callback_data="toggle_beta_features"
            ),
        ],
        [
            InlineKeyboardButton("📤 تصدير الإعدادات", callback_data="export_settings"),
            InlineKeyboardButton(
                "📥 استيراد الإعدادات", callback_data="import_settings"
            ),
        ],
        [InlineKeyboardButton("🔙 العودة للإعدادات", callback_data="back_to_settings")],
    ]
    return InlineKeyboardMarkup(buttons)


def get_grade_display_settings_keyboard() -> InlineKeyboardMarkup:
    """Grade display settings keyboard."""
    buttons = [
        [
            InlineKeyboardButton(
                "📋 تنسيق العرض", callback_data="grade_display_format"
            ),
            InlineKeyboardButton(
                "📈 الرسوم البيانية", callback_data="toggle_grade_charts"
            ),
        ],
        [
            InlineKeyboardButton(
                "📊 النسبة المئوية", callback_data="toggle_show_percentage"
            ),
            InlineKeyboardButton(
                "🎯 الدرجة الحرفية", callback_data="toggle_letter_grade"
            ),
        ],
        [
            InlineKeyboardButton(
                "📅 الفترة الزمنية", callback_data="grade_time_period"
            ),
            InlineKeyboardButton("📊 المعدل التراكمي", callback_data="toggle_show_gpa"),
        ],
        [
            InlineKeyboardButton(
                "💭 الاقتباسات الفلسفية", callback_data="toggle_philosophical_quotes"
            ),
            InlineKeyboardButton(
                "🔍 الملاحظات والتحليل", callback_data="toggle_insights"
            ),
        ],
        [InlineKeyboardButton("🏆 الإنجازات", callback_data="toggle_achievements")],
        [InlineKeyboardButton("🔙 العودة للإعدادات", callback_data="back_to_settings")],
    ]
    return InlineKeyboardMarkup(buttons)


def get_contact_support_inline_keyboard():
    """Inline keyboard with a Contact Support button."""
    admin_username = CONFIG.get("ADMIN_USERNAME", "@admin")
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 تواصل مع الدعم الفني", url=f"https://t.me/{admin_username.lstrip('@')}")]
    ])
