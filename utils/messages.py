"""
📝 Message Templates
"""
from config import CONFIG

def get_welcome_message() -> str:
    """Get welcome message"""
    return (
        "مرحباً بك في نظام الإشعارات الجامعية.\n\n"
        "سجل دخولك لمتابعة درجاتك.\n\n"
        "المطور: @sisp_t\n"
        "— THE DIE IS CAST · based on beehouse"
    )

def get_help_message() -> str:
    """Get help message"""
    return (
        "استخدم القائمة الرئيسية للتنقل.\n\n"
        "• تسجيل الدخول: لإدخال بياناتك\n"
        "• عرض الدرجات: لرؤية نتائجك\n"
        "• الإعدادات: لتغيير الإعدادات\n\n"
        "للمساعدة: @sisp_t\n"
        "— THE DIE IS CAST · based on beehouse"
    )

def get_error_message(error_type: str = "عام") -> str:
    """Get error message"""
    error_messages = {
        "login_failed": "فشل تسجيل الدخول. تحقق من بياناتك.\n— THE DIE IS CAST · based on beehouse",
        "network_error": "خطأ في الاتصال. حاول لاحقاً.\n— THE DIE IS CAST · based on beehouse",
        "api_error": "النظام غير متاح. حاول لاحقاً.\n— THE DIE IS CAST · based on beehouse",
        "token_expired": "انتهت الجلسة. سجل دخولك مجدداً.\n— THE DIE IS CAST · based on beehouse",
        "no_grades": "لا توجد درجات متاحة حالياً.\n— THE DIE IS CAST · based on beehouse",
        "general": "حدث خطأ. حاول لاحقاً.\n— THE DIE IS CAST · based on beehouse"
    }
    return error_messages.get(error_type, error_messages["general"])

def get_success_message(action: str) -> str:
    """Get success message"""
    success_messages = {
        "login": "✅ **تم تسجيل الدخول بنجاح!**\n\nيمكنك الآن فحص درجاتك واستلام الإشعارات.",
        "grades_updated": "📊 **تم تحديث الدرجات بنجاح!**\n\nتم فحص درجاتك وتحديثها.",
        "settings_saved": "⚙️ **تم حفظ الإعدادات بنجاح!**\n\nتم تحديث إعداداتك.",
        "profile_updated": "👤 **تم تحديث الملف الشخصي بنجاح!**\n\nتم تحديث معلوماتك الشخصية."
    }
    
    return success_messages.get(action, "✅ تم تنفيذ العملية بنجاح!")

def get_info_message(info_type: str) -> str:
    """Get info message"""
    info_messages = {
        "not_registered": "❌ **لم يتم تسجيلك بعد**\n\nاضغط على '🚀 تسجيل الدخول' أولاً لإدخال بياناتك الجامعية.",
        "no_permission": "🚫 **ليس لديك صلاحية**\n\nهذه الميزة متاحة للمطور فقط.",
        "maintenance": "🔧 **البوت في الصيانة**\n\nيرجى المحاولة لاحقاً أو التواصل مع الدعم الفني.",
        "coming_soon": "🚧 **قريباً**\n\nهذه الميزة ستكون متاحة قريباً."
    }
    
    return info_messages.get(info_type, "ℹ️ معلومات")

def get_registration_success_message(username: str) -> str:
    """Get registration success message"""
    return (
        f"تم تسجيل الدخول بنجاح.\n\n"
        f"مرحباً {username}.\n\n"
        f"يمكنك الآن متابعة درجاتك في نظام الإشعارات الجامعية.\n\n"
        f"— THE DIE IS CAST · based on beehouse"
    ) 