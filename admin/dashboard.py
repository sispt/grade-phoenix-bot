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
        if action.startswith("users_overview"):
            await query.edit_message_text(text=self._get_users_overview_text(), reply_markup=self._get_dashboard_keyboard())
        elif action.startswith("view_users"):
            # Pagination logic
            page = 1
            if ':' in action:
                try:
                    page = int(action.split(':')[1])
                except:
                    page = 1
            await query.edit_message_text(text=self._get_users_list_text(page=page), reply_markup=self._get_users_list_keyboard(page=page))
        elif action.startswith("user_search"):
            # Prompt admin to enter search query
            await query.edit_message_text(text="🔎 أدخل اسم المستخدم أو الـ ID للبحث:")
            context.user_data['awaiting_user_search'] = True
        elif action.startswith("user_search_result:"):
            # Show user details
            user_id = action.split(':', 1)[1]
            user = next((u for u in self.user_storage.get_all_users() if str(u.get('telegram_id')) == user_id), None)
            if user:
                text = f"👤 المستخدم: {user.get('username', '-')}
ID: {user.get('telegram_id', '-')}
الاسم الكامل: {user.get('fullname', '-')}
آخر دخول: {user.get('last_login', '-')}
"
            else:
                text = "❌ المستخدم غير موجود."
            await query.edit_message_text(text=text, reply_markup=self._get_dashboard_keyboard())
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

    def _get_users_list_text(self, page=1, per_page=10):
        users = self.user_storage.get_all_users()
        total = len(users)
        start = (page - 1) * per_page
        end = start + per_page
        users_page = users[start:end]
        text = f"👥 قائمة المستخدمين (صفحة {page}):\n\n"
        for user in users_page:
            text += f"- {user.get('username', '-')} (ID: {user.get('telegram_id', '-')})\n"
        text += f"\nإجمالي المستخدمين: {total}"
        return text

    def _get_users_list_keyboard(self, page=1, per_page=10):
        users = self.user_storage.get_all_users()
        total_pages = max(1, (len(users) + per_page - 1) // per_page)
        buttons = []
        nav = []
        if page > 1:
            nav.append(InlineKeyboardButton("⬅️ السابق", callback_data=f"view_users:{page-1}"))
        if page < total_pages:
            nav.append(InlineKeyboardButton("التالي ➡️", callback_data=f"view_users:{page+1}"))
        if nav:
            buttons.append(nav)
        # Add search button
        buttons.append([InlineKeyboardButton("🔎 بحث عن مستخدم", callback_data="user_search")])
        # Add close button
        buttons.append([InlineKeyboardButton("❌ إغلاق", callback_data="close_dashboard")])
        return InlineKeyboardMarkup(buttons)

    # To be called from the main bot when admin sends a message after search prompt
    async def handle_user_search_message(self, update, context):
        if not context.user_data.get('awaiting_user_search'):
            return False
        query = update.message.text.strip()
        users = self.user_storage.get_all_users()
        results = [u for u in users if query in str(u.get('telegram_id')) or query.lower() in (u.get('username', '').lower() or '')]
        if not results:
            await update.message.reply_text("❌ لا يوجد مستخدم مطابق.", reply_markup=self._get_dashboard_keyboard())
        else:
            buttons = [[InlineKeyboardButton(f"{u.get('username', '-')} (ID: {u.get('telegram_id', '-')})", callback_data=f"user_search_result:{u.get('telegram_id')}")] for u in results[:10]]
            buttons.append([InlineKeyboardButton("❌ إغلاق", callback_data="close_dashboard")])
            await update.message.reply_text("نتائج البحث:", reply_markup=InlineKeyboardMarkup(buttons))
        context.user_data['awaiting_user_search'] = False
        return True

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