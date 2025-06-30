"""
🎛️ Admin Dashboard System (Final Version)
"""
import logging
from typing import List # Corrected import
from datetime import datetime # Needed for timestamp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import CONFIG

logger = logging.getLogger(__name__)

class AdminDashboard:
    def __init__(self, bot):
        self.bot = bot
        self.user_storage = self.bot.user_storage
        self.grade_storage = self.bot.grade_storage
        # self.university_api = self.bot.university_api # Not strictly needed here

    async def show_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != CONFIG["ADMIN_ID"]: return
        dashboard_text = await self._get_dashboard_text()
        keyboard = self._get_dashboard_keyboard()
        await update.message.reply_text(dashboard_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        action = query.data
        
        await query.answer() # Acknowledge the callback query

        if action == "admin_stats":
            stats_text = await self._get_dashboard_stats_text()
            await query.edit_message_text(text=stats_text, reply_markup=self._get_dashboard_keyboard())
        elif action == "admin_server_status":
            # This is your placeholder for server status.
            await query.edit_message_text(text="✅ حالة الخادم: يعمل بشكل طبيعي.", reply_markup=self._get_dashboard_keyboard())
        elif action == "admin_users_list":
            users_text = await self._get_users_list_text()
            await query.edit_message_text(text=users_text, reply_markup=self._get_dashboard_keyboard())
        elif action == "admin_broadcast":
            await self.bot.broadcast_system.start_broadcast(query, context)
        # Add more admin actions as elif blocks
        else:
            await query.edit_message_text("تم تنفيذ الإجراء (لا يوجد تعريف مفصل).")

    async def _get_dashboard_text(self) -> str:
        # Get quick stats for the main dashboard view
        users_count = self.user_storage.get_users_count() # Assumes this method exists
        active_users_count = self.user_storage.get_active_users_count() # Assumes this method exists
        
        return f"🎛️ **لوحة التحكم الإدارية**\n\n👥 إجمالي المستخدمين: {users_count}\n✅ المستخدمون النشطون: {active_users_count}"

    async def _get_dashboard_stats_text(self) -> str:
        # More detailed stats from user_storage
        users = self.user_storage.get_all_users()
        active_users = self.user_storage.get_active_users()
        # Ensure get_grades_summary exists and works in your storage.
        # If not, you'll need to add it or calculate here.
        grades_summary = self.grade_storage.get_grades_summary() # Placeholder for now
        
        return f"""📈 **إحصائيات البوت:**

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
        if not users: return "📭 **لا يوجد مستخدمين مسجلين حالياً**"
        
        message = "👥 **قائمة المستخدمين**:\n\n"
        # Only show a few users as a summary
        for i, user in enumerate(users[:5], 1):
            status = "✅" if user.get("is_active", True) else "❌"
            message += f"{i}. {status} {user.get('fullname', user.get('username', 'N/A'))} (ID: {user.get('telegram_id')})\n"
        if len(users) > 5: message += f"... و {len(users) - 5} مستخدمين آخرين"
        return message

    def _get_dashboard_keyboard(self) -> List[List[InlineKeyboardButton]]:
        return [
            [
                InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats"),
                InlineKeyboardButton("👥 قائمة المستخدمين", callback_data="admin_users_list"),
            ],
            [
                InlineKeyboardButton("🔔 إشعار عام", callback_data="admin_broadcast"),
                InlineKeyboardButton("⚙️ حالة الخادم", callback_data="admin_server_status"),
            ]
        ]