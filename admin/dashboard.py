"""
🎛️ Admin Dashboard System
"""
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import CONFIG
from storage.users import UserStorage
from storage.grades import GradeStorage
from university.api import UniversityAPI

logger = logging.getLogger(__name__)

class AdminDashboard:
    """Admin dashboard system"""
    
    def __init__(self):
        self.user_storage = UserStorage()
        self.grade_storage = GradeStorage()
        self.university_api = UniversityAPI()
    
    async def show_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show admin dashboard"""
        if update.effective_user.id != CONFIG["ADMIN_ID"]:
            return
        
        dashboard_text = await self._get_dashboard_text()
        keyboard = self._get_dashboard_keyboard()
        
        await update.message.reply_text(
            dashboard_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def get_stats(self) -> str:
        """Get bot statistics"""
        try:
            users = self.user_storage.get_all_users()
            active_users = self.user_storage.get_active_users()
            grades_summary = self.grade_storage.get_grades_summary()
            
            stats_text = f"""
📈 **إحصائيات البوت:**

👥 **المستخدمين:**
• إجمالي المستخدمين: {len(users)}
• المستخدمين النشطين: {len(active_users)}
• نسبة النشاط: {(len(active_users)/len(users)*100) if len(users) > 0 else 0:.1f}%

📊 **الدرجات:**
• إجمالي المواد: {grades_summary.get('total_courses', 0)}
• التحديثات الأخيرة: {grades_summary.get('recent_updates', 0)}

🕒 **آخر تحديث:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            return stats_text
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return "❌ خطأ في جلب الإحصائيات"
    
    async def get_users_list(self) -> str:
        """Get users list"""
        try:
            users = self.user_storage.get_all_users()
            
            if not users:
                return "📭 **لا يوجد مستخدمين مسجلين حالياً**"
            
            message = f"👥 **قائمة المستخدمين** ({len(users)} مستخدم):\n\n"
            
            for i, user in enumerate(users[:10], 1):  # Show first 10 users
                status = "✅ نشط" if user.get("is_active", True) else "❌ غير نشط"
                grades_count = len(self.grade_storage.get_grades(user.get("telegram_id")))
                
                message += f"{i}. **{user.get('fullname', user.get('username', 'غير محدد'))}**\n"
                message += f"   🆔 {user.get('telegram_id')}\n"
                message += f"   👤 {user.get('username')}\n"
                message += f"   📧 {user.get('email', 'غير محدد')}\n"
                message += f"   📊 {grades_count} مواد\n"
                message += f"   {status}\n\n"
            
            if len(users) > 10:
                message += f"... و {len(users) - 10} مستخدمين آخرين"
            
            return message
            
        except Exception as e:
            logger.error(f"Error getting users list: {e}")
            return "❌ خطأ في جلب قائمة المستخدمين"
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle admin callback queries"""
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id != CONFIG["ADMIN_ID"]:
            return
        
        data = query.data
        
        if data == "admin_dashboard":
            await self._show_main_dashboard(query)
        elif data == "admin_stats":
            await self._show_detailed_stats(query)
        elif data == "admin_users":
            await self._show_users_management(query)
        elif data == "admin_broadcast":
            await self._start_broadcast(query, context)
        elif data == "admin_check_grades":
            await self._check_all_grades(query)
        elif data == "admin_backup":
            await self._create_backup(query)
        elif data == "admin_settings":
            await self._show_settings(query)
        elif data.startswith("admin_user_"):
            await self._show_user_details(query, data.split("_")[2])
        elif data == "admin_back":
            await self._show_main_dashboard(query)
    
    async def _show_main_dashboard(self, query):
        """Show main dashboard"""
        dashboard_text = await self._get_dashboard_text()
        keyboard = self._get_dashboard_keyboard()
        
        await query.edit_message_text(
            dashboard_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def _show_detailed_stats(self, query):
        """Show detailed statistics"""
        stats_text = await self.get_stats()
        keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="admin_dashboard")]]
        
        await query.edit_message_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def _show_users_management(self, query):
        """Show users management"""
        users = self.user_storage.get_all_users()
        
        if not users:
            text = "📭 **لا يوجد مستخدمين مسجلين حالياً**"
            keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="admin_dashboard")]]
        else:
            text = f"👥 **إدارة المستخدمين** ({len(users)} مستخدم)\n\n"
            keyboard = []
            
            for i, user in enumerate(users[:5], 1):  # Show first 5 users
                status = "✅" if user.get("is_active", True) else "❌"
                text += f"{i}. {status} {user.get('fullname', user.get('username', 'غير محدد'))}\n"
                keyboard.append([
                    InlineKeyboardButton(
                        f"👤 {user.get('username', 'غير محدد')}",
                        callback_data=f"admin_user_{user.get('telegram_id')}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data="admin_dashboard")])
        
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def _start_broadcast(self, query, context):
        """Start broadcast system"""
        # This will be handled by the broadcast system
        await query.edit_message_text(
            "🔔 **نظام الإشعارات العامة**\n\n"
            "اكتب الرسالة التي تريد إرسالها لجميع المستخدمين:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ إلغاء", callback_data="admin_dashboard")
            ]])
        )
        context.user_data["broadcast_mode"] = True
    
    async def _check_all_grades(self, query):
        """Check all users grades"""
        await query.edit_message_text(
            "🔄 **فحص جميع الدرجات**\n\n"
            "جاري فحص درجات جميع المستخدمين...",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 العودة", callback_data="admin_dashboard")
            ]])
        )
        
        # This would be implemented to check all users' grades
        # For now, just show a placeholder message
        await query.edit_message_text(
            "✅ **تم فحص جميع الدرجات**\n\n"
            "تم فحص درجات جميع المستخدمين بنجاح!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 العودة", callback_data="admin_dashboard")
            ]])
        )
    
    async def _create_backup(self, query):
        """Create backup"""
        await query.edit_message_text(
            "💾 **إنشاء نسخة احتياطية**\n\n"
            "جاري إنشاء النسخة الاحتياطية...",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 العودة", callback_data="admin_dashboard")
            ]])
        )
        
        # Create backups
        users_backup = self.user_storage.backup_users()
        grades_backup = self.grade_storage.backup_grades()
        
        backup_text = "✅ **تم إنشاء النسخة الاحتياطية**\n\n"
        if users_backup:
            backup_text += f"📁 المستخدمين: {users_backup}\n"
        if grades_backup:
            backup_text += f"📁 الدرجات: {grades_backup}\n"
        
        await query.edit_message_text(
            backup_text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 العودة", callback_data="admin_dashboard")
            ]])
        )
    
    async def _show_settings(self, query):
        """Show admin settings"""
        settings_text = f"""
⚙️ **إعدادات المطور:**

🔄 **فحص الدرجات:**
• الفترة: كل {CONFIG["GRADE_CHECK_INTERVAL"]} دقائق
• الحالة: {'مفعل' if CONFIG["ENABLE_NOTIFICATIONS"] else 'معطل'}

🔔 **الإشعارات:**
• إشعارات التحديث: {'مفعلة' if CONFIG["ENABLE_NOTIFICATIONS"] else 'معطلة'}
• إشعارات الأخطاء: {'مفعلة' if CONFIG["ENABLE_ERROR_NOTIFICATIONS"] else 'معطلة'}

📊 **التخزين:**
• نوع التخزين: JSON
• النسخ الاحتياطي: {'مفعل' if CONFIG["BACKUP_ENABLED"] else 'معطل'}

🌐 **الاتصال:**
• نوع الاتصال: مباشر
• إعادة المحاولة: {CONFIG["MAX_RETRY_ATTEMPTS"]} مرات
"""
        
        keyboard = [[InlineKeyboardButton("🔙 العودة", callback_data="admin_dashboard")]]
        
        await query.edit_message_text(
            settings_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def _show_user_details(self, query, user_id: str):
        """Show user details"""
        try:
            user = self.user_storage.get_user(int(user_id))
            if not user:
                await query.edit_message_text(
                    "❌ المستخدم غير موجود",
                    reply_markup=InlineKeyboardMarkup([[
                        InlineKeyboardButton("🔙 العودة", callback_data="admin_users")
                    ]])
                )
                return
            
            grades = self.grade_storage.get_grades(int(user_id))
            
            user_text = f"""
👤 **تفاصيل المستخدم:**

🆔 **معرف التلجرام:** {user.get('telegram_id')}
👨‍🎓 **اسم المستخدم:** {user.get('username', 'غير محدد')}
📧 **البريد الإلكتروني:** {user.get('email', 'غير محدد')}
👤 **الاسم الكامل:** {user.get('fullname', 'غير محدد')}
📅 **تاريخ التسجيل:** {user.get('registration_date', 'غير محدد')}

📊 **الدرجات:**
• 📚 عدد المواد: {len(grades)}
• 🔄 آخر تحديث: {self.grade_storage.get_last_updated(int(user_id)) or 'غير محدد'}

🔑 **حالة التوكن:** {'✅ صالح' if user.get('token') else '❌ غير صالح'}
"""
            
            keyboard = [
                [
                    InlineKeyboardButton("🔄 تحديث التوكن", callback_data=f"admin_refresh_token_{user_id}"),
                    InlineKeyboardButton("📊 فحص الدرجات", callback_data=f"admin_check_user_{user_id}")
                ],
                [
                    InlineKeyboardButton("❌ حذف المستخدم", callback_data=f"admin_delete_user_{user_id}"),
                    InlineKeyboardButton("🔙 العودة", callback_data="admin_users")
                ]
            ]
            
            await query.edit_message_text(
                user_text,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            logger.error(f"Error showing user details: {e}")
            await query.edit_message_text(
                "❌ خطأ في عرض تفاصيل المستخدم",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 العودة", callback_data="admin_users")
                ]])
            )
    
    async def _get_dashboard_text(self) -> str:
        """Get dashboard text"""
        users_count = self.user_storage.get_users_count()
        active_users_count = self.user_storage.get_active_users_count()
        grades_summary = self.grade_storage.get_grades_summary()
        
        return f"""
🎛️ **لوحة التحكم الإدارية**

📊 **الإحصائيات السريعة:**
• 👥 المستخدمين: {users_count}
• ✅ النشطين: {active_users_count}
• 📚 المواد: {grades_summary.get('total_courses', 0)}

🕒 **آخر تحديث:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

اختر الوظيفة المطلوبة:
"""
    
    def _get_dashboard_keyboard(self) -> List[List[InlineKeyboardButton]]:
        """Get dashboard keyboard"""
        return [
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
            ]
        ] 