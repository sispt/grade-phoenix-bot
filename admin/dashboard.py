"""
🎛️ Admin Dashboard System (Final Version)
"""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import CONFIG

logger = logging.getLogger(__name__)

class AdminDashboard:
    """Admin dashboard: shows stats and handles admin actions."""
    def __init__(self, bot):
        self.bot = bot
        self.user_storage = bot.user_storage
        self.grade_storage = bot.grade_storage

    async def show_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Displays the admin dashboard with current user statistics."""
        if update.effective_user.id != CONFIG["ADMIN_ID"]: return
        stats_text = await self._get_dashboard_text()
        keyboard = self._get_dashboard_keyboard()
        await update.message.reply_text(stats_text, reply_markup=InlineKeyboardMarkup(keyboard))

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles button callbacks in the admin panel."""
        query = update.callback_query
        action = query.data
        
        if action == "admin_stats":
            stats_text = await self._get_dashboard_text()
            await query.edit_message_text(text=stats_text, reply_markup=self._get_dashboard_keyboard())
        elif action == "admin_server_status":
            await query.edit_message_text(text="✅ حالة الخادم: يعمل بشكل طبيعي.", reply_markup=self._get_dashboard_keyboard())
        # Add more admin actions here as elif blocks
        else:
            await query.edit_message_text("تم تنفيذ الإجراء.")

    async def _get_dashboard_text(self) -> str:
        """Builds the statistics text for the admin dashboard."""
        # Assuming user_storage has a method to get these counts.
        # If not, this needs to be implemented in your storage classes.
        try:
            users_count = self.user_storage.get_users_count()
            active_users_count = self.user_storage.get_active_users_count()
        except:
            users_count, active_users_count = "N/A", "N/A"
        
        return f"🎛️ **لوحة التحكم**\n\n- إجمالي المستخدمين: {users_count}\n- المستخدمون النشطون: {active_users_count}"

    def _get_dashboard_keyboard(self) -> List[List[InlineKeyboardButton]]:
        return [
            [InlineKeyboardButton("📊 تحديث الإحصائيات", callback_data="admin_stats")],
            [InlineKeyboardButton("⚙️ حالة الخادم", callback_data="admin_server_status")]
        ]