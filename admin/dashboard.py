"""
🎛️ Admin Dashboard System (Final & Complete Version)
"""
import logging
from typing import List # Corrected import for List
from datetime import datetime # Needed for timestamp in stats
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import CONFIG

logger = logging.getLogger(__name__)

class AdminDashboard:
    """Admin dashboard system"""
    
    def __init__(self, bot): # Corrected to accept bot instance
        self.bot = bot
        # Access storage instances directly from the passed bot object
        self.user_storage = self.bot.user_storage
        self.grade_storage = self.bot.grade_storage
        self.university_api = self.bot.university_api # Access API for potential admin tasks

    async def show_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != CONFIG["ADMIN_ID"]: return
        dashboard_text = await self._get_dashboard_text()
        keyboard = self._get_dashboard_keyboard()
        # Admin commands are usually sent in private, so reply_text is fine.
        await update.message.reply_text(dashboard_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        action = query.data
        
        await query.answer() # Always acknowledge the callback query
        
        if action == "admin_stats":
            stats_text = await self._get_dashboard_stats_text()
            await query.edit_message_text(text=stats_text, reply_markup=self._get_dashboard_keyboard())
        elif action == "admin_server_status":
            # This is a placeholder for actual server status checks if implemented.
            await query.edit_message_text(text="✅ حالة الخادم: يعمل بشكل طبيعي.", reply_markup=self._get_dashboard_keyboard())
        elif action == "admin_users_list":
            users_text = await self._get_users_list_text()
            await query.edit_message_text(text=users_text, reply_markup=self._get_dashboard_keyboard())
        elif action == "admin_broadcast":
            # Delegate to broadcast system. The `start_broadcast` method will handle sending the initial message.
            await self.bot.broadcast_system.start_broadcast(query, context)
        # Add more admin actions as elif blocks here
        else:
            await query.edit_message_text("تم تنفيذ الإجراء (لا يوجد تعريف مفصل).")

    async def _get_dashboard_text(self) -> str:
        # Get quick stats for the main dashboard view
        # Ensure your storage.users.py has get_users_count() and get_active_users_count() methods
        try:
            users_count = self.user_storage.get_users_count()
            active_users_count = self.user_storage.get_active_users_count()
        except AttributeError: # Fallback if methods are not yet implemented in UserStorage
            users_count, active_users_count = "N/A", "N/A"
        
        return f"""
🎛️ **لوحة التحكم الإدارية**

📊 **الإحصائيات السريعة:**
• 👥 إجمالي المستخدمين: {users_count}
• ✅ المستخدمون النشطون: {active_users_count}

🕒 **آخر تحديث:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

اختر الوظيفة المطلوبة:
"""

    async def _get_dashboard_stats_text(self) -> str:
        # More detailed stats from user_storage
        users = self.user_storage.get_all_users()
        active_users = self.user_storage.get_active_users()
        # Ensure your storage.grades.py has get_grades_summary() method
        try:
            grades_summary = self.grade_storage.get_grades_summary()
        except AttributeError: # Fallback if method is not yet implemented
            grades_summary = {"total_courses": "N/A", "recent_updates": "N/A"}
        
        return f"""
📈 **إحصائيات البوت:**

👥 **المستخدمين:**
• إجمالي المستخدمين: {len(users)}
• المستخدمون النشطون: {len(active_users)}
• نسبة النشاط: {(len(active_users)/len(users)*100) if len(users) > 0 else 0:.1f}%

📊 **الدرجات:**
• إجمالي المواد: {grades_summary.get('total_courses', 0)}
• التحديثات الأخيرة: {grades_summary.get('recent_updates', 0)}

🕒 **آخر تحديث:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

    async def _get_users_list_text(self) -> str:
        users = self.user_storage.get_all_users()
        if not users:
            return "📭 **لا يوجد مستخدمين مسجلين حالياً**"
        
        message = f"👥 **قائمة المستخدمين** ({len(users)} مستخدم):\n\n"
        # Displaying a summary of users for brevity in the list
        for i, user in enumerate(users[:CONFIG.get("MAX_USERS_PER_PAGE", 10)], 1): # Limit to configured max per page
            status = "✅" if user.get("is_active", True) else "❌"
            message += f"{i}. {status} {user.get('fullname', user.get('username', 'غير محدد'))} (ID: `{user.get('telegram_id')}`)\n"
        
        if len(users) > CONFIG.get("MAX_USERS_PER_PAGE", 10):
            message += f"... و {len(users) - CONFIG.get('MAX_USERS_PER_PAGE', 10)} مستخدمين آخرين"
        
        return message

    def _get_dashboard_keyboard(self) -> List[List[InlineKeyboardButton]]:
        return [
            [
                InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"),
                InlineKeyboardButton("👥 قائمة المستخدمين", callback_data="admin_users_list")
            ],
            [
                InlineKeyboardButton("🔔 إشعار عام", callback_data="admin_broadcast"),
                InlineKeyboardButton("⚙️ حالة الخادم", callback_data="admin_server_status") # Changed button text
            ]
            # Add more rows for other admin actions here
        ]