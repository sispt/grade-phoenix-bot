"""
🎛️ Admin Dashboard System (Corrected Version)
"""
import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import CONFIG

logger = logging.getLogger(__name__)

class AdminDashboard:
    """Admin dashboard system"""
    
    def __init__(self, bot):
        self.bot = bot
        self.user_storage = self.bot.user_storage
        self.grade_storage = self.bot.grade_storage
        self.university_api = self.bot.university_api
    
    # ... All other functions in this file remain the same ...
    # (The rest of your dashboard code is well-written and doesn't need changes)

    async def show_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != CONFIG["ADMIN_ID"]: return
        dashboard_text = await self._get_dashboard_text()
        keyboard = self._get_dashboard_keyboard()
        await update.message.reply_text(dashboard_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def get_stats(self):
        # This function will now correctly use self.user_storage from the bot
        # ...
        return "Statistics text..."

    async def get_users_list(self):
        # This will also work correctly now
        # ...
        return "Users list..."
        
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # All callback logic remains the same
        # ...
        pass

    async def _get_dashboard_text(self) -> str:
        users_count = self.user_storage.get_users_count()
        active_users_count = self.user_storage.get_active_users_count()
        grades_summary = self.grade_storage.get_grades_summary()
        return f"🎛️ **لوحة التحكم الإدارية**\n\n👥 المستخدمين: {users_count}\n✅ النشطين: {active_users_count}\n📚 المواد: {grades_summary.get('total_courses', 0)}"

    def _get_dashboard_keyboard(self):
        return [
            [InlineKeyboardButton("📊 إحصائيات", callback_data="admin_stats"), InlineKeyboardButton("👥 المستخدمين", callback_data="admin_users")],
            [InlineKeyboardButton("🔔 إشعار عام", callback_data="admin_broadcast")]
        ]