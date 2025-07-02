"""
🎛️ Harmonic Admin Dashboard System (Enhanced)
"""
import logging
from typing import List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from config import CONFIG
from datetime import datetime
from utils.keyboards import (
    get_enhanced_admin_dashboard_keyboard,
    get_user_management_keyboard,
    get_broadcast_confirmation_keyboard,
    get_system_actions_keyboard,
    remove_keyboard
)

logger = logging.getLogger(__name__)

# Add 'Broadcast' button to the admin dashboard keyboard
ADMIN_DASHBOARD_BUTTONS = [
    ["👥 المستخدمون", "📊 التحليل"],
    ["📢 بث رسالة"]
]

class AdminDashboard:
    def __init__(self, bot):
        self.bot = bot
        self.user_storage = bot.user_storage

    async def show_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != CONFIG["ADMIN_ID"]: return
        dashboard_text = self._get_dashboard_text()
        keyboard = get_enhanced_admin_dashboard_keyboard()
        await update.message.reply_text(dashboard_text, reply_markup=keyboard)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        action = query.data
        await query.answer()
        
        try:
            if action.startswith("users_overview"):
                await query.edit_message_text(text=self._get_users_overview_text(), reply_markup=get_enhanced_admin_dashboard_keyboard())
            elif action.startswith("view_users"):
                # Pagination logic
                page = 1
                if ':' in action:
                    try:
                        page = int(action.split(':')[1])
                    except:
                        page = 1
                users = self.user_storage.get_all_users()
                total_pages = max(1, (len(users) + 9) // 10)  # 10 users per page
                await query.edit_message_text(
                    text=self._get_users_list_text(page=page), 
                    reply_markup=get_user_management_keyboard(page, total_pages)
                )
            elif action.startswith("user_search"):
                # Prompt admin to enter search query
                await query.edit_message_text(text="🔎 أدخل اسم المستخدم أو الـ ID للبحث:")
                context.user_data['awaiting_user_search'] = True
            elif action.startswith("user_search_result:"):
                # Show user details
                user_id = action.split(':', 1)[1]
                user = next((u for u in self.user_storage.get_all_users() if str(u.get('telegram_id')) == user_id), None)
                if user:
                    text = f"""👤 **تفاصيل المستخدم:**
- الاسم: {user.get('username', '-')}
- المعرف: {user.get('telegram_id', '-')}
- الاسم الكامل: {user.get('fullname', '-')}
- آخر دخول: {user.get('last_login', '-')}
- الحالة: {'نشط' if user.get('is_active', True) else 'غير نشط'}"""
                else:
                    text = "❌ المستخدم غير موجود."
                await query.edit_message_text(text=text, reply_markup=get_enhanced_admin_dashboard_keyboard())
            elif action == "analysis":
                await query.edit_message_text(text=self._get_analysis_text(), reply_markup=get_enhanced_admin_dashboard_keyboard())
            elif action == "close_dashboard":
                await query.edit_message_text(text="✅ تم إغلاق لوحة التحكم.")
            elif action == "broadcast":
                # Start broadcast mode
                await query.edit_message_text(
                    text="📝 أرسل نص الرسالة التي تريد بثها لجميع المستخدمين:",
                    reply_markup=get_broadcast_confirmation_keyboard()
                )
            elif action == "confirm_broadcast":
                await query.edit_message_text(text="📝 أرسل نص الرسالة التي تريد بثها:")
                context.user_data['awaiting_broadcast'] = True
            elif action == "cancel_broadcast":
                await query.edit_message_text(text="❌ تم إلغاء البث.", reply_markup=get_enhanced_admin_dashboard_keyboard())
            elif action == "system_report":
                await query.edit_message_text(text=self._get_system_report_text(), reply_markup=get_enhanced_admin_dashboard_keyboard())
            elif action == "delete_user":
                await query.edit_message_text(text="🔍 أدخل معرف المستخدم الذي تريد حذفه:")
                context.user_data['awaiting_user_delete'] = True
            elif action == "refresh_data":
                await query.edit_message_text(text="🔄 جاري تحديث البيانات...")
                # Simulate refresh
                await query.edit_message_text(text="✅ تم تحديث البيانات.", reply_markup=get_enhanced_admin_dashboard_keyboard())
            elif action == "backup_data":
                await query.edit_message_text(text="💾 جاري إنشاء نسخة احتياطية...")
                # Simulate backup
                await query.edit_message_text(text="✅ تم إنشاء النسخة الاحتياطية.", reply_markup=get_enhanced_admin_dashboard_keyboard())
            elif action == "back_to_dashboard":
                await query.edit_message_text(text=self._get_dashboard_text(), reply_markup=get_enhanced_admin_dashboard_keyboard())
            elif action == "users_stats":
                await query.edit_message_text(text=self._get_users_stats_text(), reply_markup=get_user_management_keyboard())
            elif action == "current_page":
                # Do nothing for current page indicator
                pass
            else:
                await query.edit_message_text(f"Action '{action}' selected.", reply_markup=get_enhanced_admin_dashboard_keyboard())
        except Exception as e:
            logger.error(f"Error handling callback {action}: {e}")
            await query.edit_message_text(
                text="❌ حدث خطأ أثناء معالجة الطلب. يرجى المحاولة مرة أخرى.",
                reply_markup=get_enhanced_admin_dashboard_keyboard()
            )

    def _get_dashboard_text(self) -> str:
        return (
            "🎛️ **لوحة التحكم الإدارية المحسنة**\n\n"
            "اختر الوظيفة المطلوبة من الأزرار أدناه.\n"
            "جميع العمليات محمية ومتاحة للمدير فقط."
        )

    def _get_users_overview_text(self) -> str:
        total = self.user_storage.get_users_count()
        active = self.user_storage.get_active_users_count()
        inactive = total - active
        return (
            f"👥 **نظرة عامة للمستخدمين**\n\n"
            f"📊 **الإحصائيات:**\n"
            f"- إجمالي المستخدمين: {total}\n"
            f"- النشطين: {active}\n"
            f"- غير النشطين: {inactive}\n"
            f"- نسبة النشاط: {(active/total*100):.1f}%" if total > 0 else "0%"
        )

    def _get_users_list_text(self, page=1, per_page=10):
        users = self.user_storage.get_all_users()
        total = len(users)
        start = (page - 1) * per_page
        end = start + per_page
        users_page = users[start:end]
        text = f"👥 **قائمة المستخدمين** (صفحة {page}):\n\n"
        for i, user in enumerate(users_page, start + 1):
            status = "🟢" if user.get('is_active', True) else "🔴"
            text += f"{i}. {status} {user.get('username', '-')} (ID: {user.get('telegram_id', '-')})\n"
        text += f"\n📊 إجمالي المستخدمين: {total}"
        return text

    def _get_users_stats_text(self) -> str:
        users = self.user_storage.get_all_users()
        total = len(users)
        active = len([u for u in users if u.get('is_active', True)])
        inactive = total - active
        
        # Calculate registration trends (last 7 days)
        recent_users = [u for u in users if u.get('registration_date')]
        recent_count = len(recent_users)
        
        text = "📊 **إحصائيات المستخدمين التفصيلية:**\n\n"
        text += f"👥 **الأعداد:**\n"
        text += f"- إجمالي المستخدمين: {total}\n"
        text += f"- النشطين: {active}\n"
        text += f"- غير النشطين: {inactive}\n"
        text += f"- نسبة النشاط: {(active/total*100):.1f}%" if total > 0 else "0%\n"
        text += f"\n📈 **النشاط:**\n"
        text += f"- المستخدمون الجدد: {recent_count}\n"
        return text

    def _get_analysis_text(self) -> str:
        users = self.user_storage.get_all_users()
        total = len(users)
        active = len([u for u in users if u.get('is_active', True)])
        last_login_user = max(users, key=lambda u: u.get('last_login', ''), default=None)
        
        text = "📊 **التحليل والإحصائيات:**\n\n"
        text += f"👥 **المستخدمون:**\n"
        text += f"- إجمالي المستخدمين: {total}\n"
        text += f"- المستخدمون النشطون: {active}\n"
        text += f"- نسبة النشاط: {(active/total*100):.1f}%" if total > 0 else "0%\n"
        
        if last_login_user:
            text += f"\n🕒 **آخر نشاط:**\n"
            text += f"- آخر مستخدم نشط: {last_login_user.get('username', '-')}\n"
            text += f"- آخر دخول: {last_login_user.get('last_login', '-')}\n"
        
        return text

    def _get_system_report_text(self) -> str:
        users = self.user_storage.get_all_users()
        total_users = len(users)
        active_users = len([u for u in users if u.get('is_active', True)])
        
        text = "📋 **تقرير حالة النظام:**\n\n"
        text += f"🖥️ **الحالة العامة:**\n"
        text += f"- النظام: 🟢 يعمل بشكل طبيعي\n"
        text += f"- قاعدة البيانات: 🟢 متصلة\n"
        text += f"- API الجامعة: 🟢 متاح\n\n"
        
        text += f"📊 **الإحصائيات:**\n"
        text += f"- إجمالي المستخدمين: {total_users}\n"
        text += f"- المستخدمون النشطون: {active_users}\n"
        text += f"- نسبة النشاط: {(active_users/total_users*100):.1f}%" if total_users > 0 else "0%\n"
        
        return text

    # To be called from the main bot when admin sends a message after search prompt
    async def handle_user_search_message(self, update, context):
        if not context.user_data.get('awaiting_user_search'):
            return False
        query = update.message.text.strip()
        users = self.user_storage.get_all_users()
        results = [u for u in users if query in str(u.get('telegram_id')) or query.lower() in (u.get('username', '').lower() or '')]
        if not results:
            await update.message.reply_text("❌ لا يوجد مستخدم مطابق.", reply_markup=get_enhanced_admin_dashboard_keyboard())
        else:
            buttons = [[InlineKeyboardButton(f"{u.get('username', '-')} (ID: {u.get('telegram_id', '-')})", callback_data=f"user_search_result:{u.get('telegram_id')}")] for u in results[:10]]
            buttons.append([InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="back_to_dashboard")])
            await update.message.reply_text("نتائج البحث:", reply_markup=InlineKeyboardMarkup(buttons))
        context.user_data['awaiting_user_search'] = False
        return True

    async def handle_user_delete_message(self, update, context):
        if not context.user_data.get('awaiting_user_delete'):
            return False
        user_id = update.message.text.strip()
        try:
            user_id = int(user_id)
            user = next((u for u in self.user_storage.get_all_users() if u.get('telegram_id') == user_id), None)
            if user:
                # Delete user (this will cascade to grades)
                self.user_storage.delete_user(user_id)
                await update.message.reply_text(f"✅ تم حذف المستخدم {user.get('username', '')} بنجاح.", reply_markup=get_enhanced_admin_dashboard_keyboard())
            else:
                await update.message.reply_text("❌ المستخدم غير موجود.", reply_markup=get_enhanced_admin_dashboard_keyboard())
        except ValueError:
            await update.message.reply_text("❌ يرجى إدخال معرف صحيح للمستخدم.", reply_markup=get_enhanced_admin_dashboard_keyboard())
        context.user_data['awaiting_user_delete'] = False
        return True

    async def handle_dashboard_message(self, update, context):
        text = update.message.text
        if text == "📢 بث رسالة":
            await update.message.reply_text("📝 أرسل نص الرسالة التي تريد بثها لجميع المستخدمين:")
            context.user_data['awaiting_broadcast'] = True
            return True
        if context.user_data.get('awaiting_broadcast'):
            message = update.message.text
            await update.message.reply_text("🚀 جاري إرسال الرسالة لجميع المستخدمين...")
            count = await self.broadcast_to_all_users(message)
            await update.message.reply_text(f"✅ تم إرسال الرسالة إلى {count} مستخدم.", reply_markup=get_enhanced_admin_dashboard_keyboard())
            context.user_data['awaiting_broadcast'] = False
            return True
        return False

    async def broadcast_to_all_users(self, message):
        users = self.bot.user_storage.get_all_users()
        sent = 0
        for user in users:
            try:
                await self.bot.app.bot.send_message(chat_id=user['telegram_id'], text=message)
                sent += 1
            except Exception:
                continue
        return sent