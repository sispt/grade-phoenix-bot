"""
🎛️ Admin Dashboard System (Final Version)
"""
import logging
from typing import List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import CONFIG

logger = logging.getLogger(__name__)

class AdminDashboard:
    def __init__(self, bot):
        self.bot = bot
        self.user_storage = bot.user_storage

    async def show_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != CONFIG["ADMIN_ID"]: return
        dashboard_text = await self._get_dashboard_text()
        keyboard = self._get_dashboard_keyboard()
        # This sends an inline keyboard which requires callbacks to work
        await update.message.reply_text(dashboard_text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        action = query.data
        
        await query.answer()

        if action == "admin_stats":
            stats_text = await self._get_dashboard_stats_text()
            await query.edit_message_text(text=stats_text, reply_markup=self._get_dashboard_keyboard())
        elif action == "admin_broadcast":
            await self.bot.broadcast_system.start_broadcast(update, context)
        else:
            await query.edit_message_text(f"Action '{action}' selected.", reply_markup=self._get_dashboard_keyboard())

    async def _get_dashboard_text(self) -> str:
        users_count = self.user_storage.get_users_count()
        return f"🎛️ **لوحة التحكم**\n\n- إجمالي المستخدمين: {users_count}"

    def _get_dashboard_keyboard(self) -> List[List[InlineKeyboardButton]]:
        return [
            [InlineKeyboardButton("📊 عرض الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton("🔔 إشعار عام", callback_data="admin_broadcast")],
        ]
        
    async def _get_dashboard_stats_text(self) -> str:
        # Placeholder for more detailed stats
        return f"Total Users: {self.user_storage.get_users_count()}"