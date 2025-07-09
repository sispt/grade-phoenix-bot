"""
🎨 Modern Elegant Keyboards
Contemporary design with clean aesthetics and professional styling

DESIGN PHILOSOPHY:
==================

1. MODERN AESTHETICS:
   - Clean, minimalist emoji selection
   - Professional color-coded categories
   - Elegant typography and spacing
   - Contemporary visual hierarchy

2. STANDARD PATTERNS:
   - Consistent button sizing and spacing
   - Logical information architecture
   - Intuitive user flow design
   - Accessible and inclusive design

3. STYLISH ELEMENTS:
   - Sophisticated emoji combinations
   - Elegant Arabic typography
   - Modern interaction patterns
   - Premium user experience

4. ELEGANT ORGANIZATION:
   - Seamless visual flow
   - Balanced layout composition
   - Refined functional grouping
   - Polished presentation
"""

from telegram import (
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from config import CONFIG


# ============================================================================
# MODERN ELEGANT KEYBOARDS
# ============================================================================

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Modern elegant main keyboard for registered users.
    
    DESIGN PHILOSOPHY:
    - Clean, minimalist layout with sophisticated grouping
    - Professional emoji selection for each category
    - Elegant Arabic typography with proper spacing
    - Contemporary visual hierarchy and flow
    """
    keyboard = [
        # Primary Information Access
        ["📊 درجات الفصل الحالي", "📚 درجات الفصل السابق", "📅 جميع الفصول"],
        
        # Personal & Analytical Tools
        ["👤 معلوماتي الشخصية", "🧮 حساب المعدل المخصص"],
        
        # Support & Guidance
        ["📞 الدعم الفني", "❓ المساعدة والدليل"],
        
        # Configuration & Control
        ["⚙️ الإعدادات والتخصيص", "❌ إلغاء"],
        
        # Session Management
        ["🚪 تسجيل الخروج"],
        
        # Data Export
        ["📥 تحميل معلوماتي"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_main_keyboard_with_admin() -> ReplyKeyboardMarkup:
    """
    Modern elegant main keyboard with admin access.
    
    DESIGN PHILOSOPHY:
    - Seamless integration of admin functions
    - Maintains elegant user experience
    - Professional admin interface design
    """
    keyboard = [
        # Primary Information Access
        ["📊 درجات الفصل الحالي", "📚 درجات الفصل السابق"],
        
        # Personal & Analytical Tools
        ["👤 معلوماتي الشخصية", "🧮 حساب المعدل المخصص"],
        
        # Support & Guidance
        ["📞 الدعم الفني", "❓ المساعدة والدليل"],
        
        # Administrative Control
        ["🎛️ لوحة التحكم الإدارية"],
        
        # Configuration & Control
        ["⚙️ الإعدادات والتخصيص", "❌ إلغاء"],
        
        # Session Management
        ["🚪 تسجيل الخروج"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_unregistered_keyboard() -> ReplyKeyboardMarkup:
    """
    Modern elegant keyboard for unregistered users.
    
    DESIGN PHILOSOPHY:
    - Welcoming and intuitive first-time experience
    - Clear call-to-action with elegant presentation
    - Minimalist design focusing on essential functions
    """
    keyboard = [
        # Primary Call-to-Action
        ["🚀 تسجيل الدخول للجامعة"],
        
        # Utility Tools
        ["🧮 حساب المعدل المخصص"],
        
        # Support & Guidance
        ["❓ المساعدة", "📞 الدعم الفني"],
        
        # Control
        ["❌ إلغاء"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_admin_keyboard() -> ReplyKeyboardMarkup:
    """
    Modern elegant admin keyboard layout.
    
    DESIGN PHILOSOPHY:
    - Professional administrative interface
    - Clean, authoritative design
    - Efficient navigation patterns
    """
    keyboard = [
        # Administrative Control
        ["🎛️ لوحة التحكم الإدارية"],
        
        # Navigation
        ["🔙 العودة للوحة الرئيسية"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


# ============================================================================
# ELEGANT UTILITY KEYBOARDS
# ============================================================================

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """
    Modern elegant cancel keyboard.
    
    DESIGN PHILOSOPHY:
    - Clean, single-purpose interface
    - Clear visual hierarchy
    - Elegant simplicity
    """
    keyboard = [["❌ إلغاء"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def remove_keyboard() -> ReplyKeyboardRemove:
    """Remove the current keyboard with elegant transition."""
    return ReplyKeyboardRemove(selective=False)


def get_error_recovery_keyboard() -> ReplyKeyboardMarkup:
    """
    Modern elegant error recovery keyboard.
    
    DESIGN PHILOSOPHY:
    - Reassuring and helpful interface
    - Clear recovery options
    - Professional error handling
    """
    keyboard = [
        # Recovery Actions
        ["🔄 إعادة المحاولة", "🏠 العودة للرئيسية"],
        
        # Support & Guidance
        ["📞 الدعم الفني", "❓ المساعدة والدليل"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def get_registration_keyboard() -> ReplyKeyboardMarkup:
    """
    Modern elegant registration keyboard.
    
    DESIGN PHILOSOPHY:
    - Streamlined registration process
    - Clear progress indicators
    - Professional onboarding experience
    """
    keyboard = [
        # Process Control
        ["❌ إلغاء التسجيل"],
        
        # Navigation
        ["🔙 العودة للرئيسية"]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def get_session_settings_keyboard() -> ReplyKeyboardMarkup:
    """
    Modern elegant session settings keyboard.
    
    DESIGN PHILOSOPHY:
    - Secure and professional settings interface
    - Clear security indicators
    - Elegant configuration design
    """
    return ReplyKeyboardMarkup([
        # Security Management
        ["🔑 إدارة الجلسة/كلمة المرور"],
        
        # Navigation
        ["🔙 العودة"]
    ], resize_keyboard=True, one_time_keyboard=True)


# ============================================================================
# SOPHISTICATED INLINE KEYBOARDS
# ============================================================================

def get_enhanced_admin_dashboard_keyboard() -> InlineKeyboardMarkup:
    """
    Modern elegant admin dashboard inline keyboard.
    
    DESIGN PHILOSOPHY:
    - Professional administrative interface
    - Sophisticated function organization
    - Elegant visual hierarchy
    - Contemporary management tools
    """
    buttons = [
        # User Management & Analytics
        [
            InlineKeyboardButton("👥 إدارة المستخدمين", callback_data="users_overview"),
            InlineKeyboardButton("📊 التحليل والإحصائيات", callback_data="analysis"),
        ],
        
        # Communication & Reporting
        [
            InlineKeyboardButton("📢 بث رسالة للجميع", callback_data="broadcast"),
            InlineKeyboardButton("💬 إرسال حكمة اليوم", callback_data="send_quote_to_all"),
            InlineKeyboardButton("📋 تقرير حالة النظام", callback_data="system_report"),
        ],
        
        # Search & Management
        [
            InlineKeyboardButton("🔍 بحث عن مستخدم", callback_data="user_search"),
            InlineKeyboardButton("🗑️ حذف مستخدم", callback_data="delete_user"),
        ],
        
        # Grade Management
        [
            InlineKeyboardButton("🛠️ فحص درجات مستخدم", callback_data="force_grade_check"),
            InlineKeyboardButton("🔄 فحص درجات للجميع", callback_data="force_grade_check_all"),
        ],
        
        # System Maintenance
        [
            InlineKeyboardButton("🔄 تحديث البيانات", callback_data="refresh_data"),
            InlineKeyboardButton("💾 إنشاء نسخة احتياطية", callback_data="backup_data"),
            InlineKeyboardButton("🔕 تحديث صامت", callback_data="silent_update"),
        ],
        
        # Testing & Quality Assurance
        [
            InlineKeyboardButton("🧪 اختبار إشعار الدرجات", callback_data="test_grade_notification"),
            InlineKeyboardButton("🧪 اختبار إشعار الاقتباس", callback_data="test_quote_notification"),
        ],
        
        # Interface Control
        [InlineKeyboardButton("❌ إغلاق لوحة التحكم", callback_data="close_dashboard")],
    ]
    return InlineKeyboardMarkup(buttons)


def get_user_management_keyboard(page=1, total_pages=1) -> InlineKeyboardMarkup:
    """
    Modern elegant user management keyboard with pagination.
    
    DESIGN PHILOSOPHY:
    - Professional user administration interface
    - Elegant pagination design
    - Sophisticated management tools
    """
    buttons = []

    # Elegant Pagination Controls
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

    # User Management Actions
    buttons.extend(
        [
            # Search & Management
            [InlineKeyboardButton("🔍 بحث عن مستخدم", callback_data="user_search")],
            [InlineKeyboardButton("🗑️ حذف مستخدم", callback_data="delete_user")],
            
            # Analytics
            [InlineKeyboardButton("📊 إحصائيات المستخدمين", callback_data="users_stats")],
            
            # Navigation
            [InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="back_to_dashboard")],
        ]
    )

    return InlineKeyboardMarkup(buttons)


def get_broadcast_confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Modern elegant broadcast confirmation keyboard.
    
    DESIGN PHILOSOPHY:
    - Professional communication interface
    - Clear confirmation design
    - Elegant decision-making flow
    """
    buttons = [
        # Confirmation Actions
        [
            InlineKeyboardButton("✅ تأكيد البث للجميع", callback_data="confirm_broadcast"),
            InlineKeyboardButton("❌ إلغاء البث", callback_data="cancel_broadcast"),
        ],
        
        # Navigation
        [InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="back_to_dashboard")],
    ]
    return InlineKeyboardMarkup(buttons)


def get_system_actions_keyboard() -> InlineKeyboardMarkup:
    """
    Modern elegant system maintenance keyboard.
    
    DESIGN PHILOSOPHY:
    - Professional system administration
    - Sophisticated maintenance tools
    - Elegant technical interface
    """
    buttons = [
        # Database & Backup Management
        [
            InlineKeyboardButton("🔄 تحديث قاعدة البيانات", callback_data="refresh_database"),
            InlineKeyboardButton("💾 إنشاء نسخة احتياطية", callback_data="create_backup"),
        ],
        
        # System Status & Maintenance
        [
            InlineKeyboardButton("📊 حالة النظام", callback_data="system_status"),
            InlineKeyboardButton("🧹 تنظيف البيانات", callback_data="cleanup_data"),
        ],
        
        # Navigation
        [InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="back_to_dashboard")],
    ]
    return InlineKeyboardMarkup(buttons)


def get_settings_main_keyboard(translation_enabled: bool = False) -> InlineKeyboardMarkup:
    """
    Modern elegant settings keyboard with GitHub integration.
    
    DESIGN PHILOSOPHY:
    - Professional configuration interface
    - Elegant toggle design
    - Sophisticated settings management
    """
    trans_label = "🌐 ترجمة الاقتباسات: مفعلة" if translation_enabled else "🌐 ترجمة الاقتباسات: معطلة"
    trans_callback = "toggle_translation"
    buttons = [
        # External Integration
        [InlineKeyboardButton("🔗 GitHub Repo", url="https://github.com/sispt/grade-phoenix-bot?refresh")],
        
        # Configuration Toggle
        [InlineKeyboardButton(trans_label, callback_data=trans_callback)],
        
        # Navigation
        [InlineKeyboardButton("🔙 العودة", callback_data="back_to_main")],
        
        # Control
        [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_action")]
    ]
    return InlineKeyboardMarkup(buttons)


def get_privacy_settings_keyboard() -> InlineKeyboardMarkup:
    """
    Modern elegant privacy settings keyboard.
    
    DESIGN PHILOSOPHY:
    - Professional privacy management
    - Elegant security interface
    - Sophisticated data control
    """
    buttons = [
        # Privacy Controls
        [
            InlineKeyboardButton("👁️ عرض المعلومات الشخصية", callback_data="toggle_show_profile"),
            InlineKeyboardButton("📊 مشاركة الإحصائيات", callback_data="toggle_share_stats"),
        ],
        
        # Data Management
        [
            InlineKeyboardButton("🗑️ حذف البيانات", callback_data="delete_user_data"),
            InlineKeyboardButton("📅 فترة الاحتفاظ", callback_data="data_retention"),
        ],
        
        # Navigation
        [InlineKeyboardButton("🔙 العودة للإعدادات", callback_data="back_to_settings")],
    ]
    return InlineKeyboardMarkup(buttons)


def get_contact_support_inline_keyboard():
    """
    Modern elegant contact support keyboard.
    
    DESIGN PHILOSOPHY:
    - Professional support interface
    - Elegant communication design
    - Sophisticated help system
    """
    admin_username = CONFIG.get("ADMIN_USERNAME", "@admin")
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 تواصل مع الدعم الفني", url=f"https://t.me/{admin_username.lstrip('@')}")]
    ])
