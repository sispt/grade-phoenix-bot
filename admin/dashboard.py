"""
🎛️ Harmonic Admin Dashboard System (Redesigned)
"""
import logging
from typing import List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import CONFIG
from datetime import datetime

logger = logging.getLogger(__name__)

class AdminDashboard:
    def __init__(self, bot):
        self.bot = bot
        self.user_storage = bot.user_storage

    async def show_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != CONFIG["ADMIN_ID"]: return
        dashboard_text = self._get_dashboard_text()
        keyboard = self._get_dashboard_keyboard()
        await update.message.reply_text(dashboard_text, reply_markup=InlineKeyboardMarkup(keyboard))

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        action = query.data
        await query.answer()
        if action == "users_overview":
            await query.edit_message_text(text=self._get_users_overview_text(), reply_markup=self._get_dashboard_keyboard())
        elif action == "view_users":
            await query.edit_message_text(text=self._get_users_list_text(), reply_markup=self._get_dashboard_keyboard())
        elif action == "analysis":
            await query.edit_message_text(text=self._get_analysis_text(), reply_markup=self._get_dashboard_keyboard())
        elif action == "close_dashboard":
            await query.edit_message_text(text="تم إغلاق لوحة التحكم.")
        else:
            await query.edit_message_text(f"Action '{action}' selected.", reply_markup=self._get_dashboard_keyboard())

    def _get_dashboard_text(self) -> str:
        return (
            "🎛️ **لوحة التحكم الإدارية**\n\n"
            "اختر وظيفة من الأزرار أدناه."
        )

    def _get_dashboard_keyboard(self) -> List[List[InlineKeyboardButton]]:
        return [
            [InlineKeyboardButton("👥 نظرة عامة للمستخدمين", callback_data="users_overview")],
            [InlineKeyboardButton("📋 عرض المستخدمين وبياناتهم", callback_data="view_users")],
            [InlineKeyboardButton("📊 التحليل والإحصائيات", callback_data="analysis")],
            [InlineKeyboardButton("🚫 إغلاق اللوحة", callback_data="close_dashboard")],
        ]

    def _get_users_overview_text(self) -> str:
        total = self.user_storage.get_users_count()
        active = self.user_storage.get_active_users_count()
        inactive = total - active
        return (
            f"👥 **نظرة عامة للمستخدمين**\n\n"
            f"- إجمالي المستخدمين: {total}\n"
            f"- النشطين: {active}\n"
            f"- غير النشطين: {inactive}\n"
        )

    def _get_users_list_text(self) -> str:
        users = self.user_storage.get_all_users()
        if not users:
            return "لا يوجد مستخدمون مسجلون."
        text = "📋 **قائمة المستخدمين:**\n\n"
        for i, user in enumerate(users[:20], 1):  # Show up to 20 users for now
            text += (
                f"{i}. {user.get('username', 'N/A')} (ID: {user.get('telegram_id', '-')})\n"
                f"   • الاسم الكامل: {user.get('fullname', '-')}, البريد: {user.get('email', '-')}\n"
                f"   • تاريخ التسجيل: {user.get('registration_date', '-')}\n"
                f"   • آخر دخول: {user.get('last_login', '-')}\n"
                f"   • نشط: {'✅' if user.get('is_active', True) else '❌'}\n\n"
            )
        if len(users) > 20:
            text += f"...ويوجد المزيد ({len(users)} مستخدم)."
        return text

    def _get_analysis_text(self) -> str:
        users = self.user_storage.get_all_users()
        total = len(users)
        active = len([u for u in users if u.get('is_active', True)])
        last_login_user = max(users, key=lambda u: u.get('last_login', ''), default=None)
        text = "📊 **التحليل والإحصائيات:**\n\n"
        text += f"- إجمالي المستخدمين: {total}\n"
        text += f"- المستخدمون النشطون: {active}\n"
        if last_login_user:
            text += f"- آخر مستخدم نشط: {last_login_user.get('username', '-')} (آخر دخول: {last_login_user.get('last_login', '-')})\n"
        return text