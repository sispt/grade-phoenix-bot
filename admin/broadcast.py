"""
🔔 Broadcast System
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes
)

from config import CONFIG
from storage.users import UserStorage
from utils.keyboards import get_cancel_keyboard

logger = logging.getLogger(__name__)

# Conversation states
COMPOSE_MESSAGE, PREVIEW_MESSAGE, CONFIRM_SEND = range(3)

class BroadcastSystem:
    """Broadcast message system"""
    
    def __init__(self):
        self.user_storage = UserStorage()
    
    def get_conversation_handler(self) -> ConversationHandler:
        """Get broadcast conversation handler"""
        return ConversationHandler(
            entry_points=[
                CommandHandler("broadcast", self._start_broadcast),
                CallbackQueryHandler(self._start_broadcast_callback, pattern="^admin_broadcast$")
            ],
            states={
                COMPOSE_MESSAGE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._compose_message),
                    CommandHandler("cancel", self._cancel_broadcast)
                ],
                PREVIEW_MESSAGE: [
                    CallbackQueryHandler(self._preview_message),
                    CommandHandler("cancel", self._cancel_broadcast)
                ],
                CONFIRM_SEND: [
                    CallbackQueryHandler(self._confirm_send),
                    CommandHandler("cancel", self._cancel_broadcast)
                ]
            },
            fallbacks=[CommandHandler("cancel", self._cancel_broadcast)],
            name="broadcast_conversation"
        )
    
    async def _start_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start broadcast conversation"""
        if update.effective_user.id != CONFIG["ADMIN_ID"]:
            return ConversationHandler.END
        
        await update.message.reply_text(
            "🔔 **نظام الإشعارات العامة**\n\n"
            "اكتب الرسالة التي تريد إرسالها لجميع المستخدمين:\n\n"
            "💡 **نصائح:**\n"
            "• يمكنك استخدام التنسيق العادي\n"
            "• الرسالة ستُرسل لجميع المستخدمين المسجلين\n"
            "• يمكنك إلغاء العملية في أي وقت\n\n"
            "اكتب رسالتك الآن:",
            reply_markup=get_cancel_keyboard()
        )
        
        return COMPOSE_MESSAGE
    
    async def _start_broadcast_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start broadcast from callback"""
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id != CONFIG["ADMIN_ID"]:
            return ConversationHandler.END
        
        await query.edit_message_text(
            "🔔 **نظام الإشعارات العامة**\n\n"
            "اكتب الرسالة التي تريد إرسالها لجميع المستخدمين:\n\n"
            "💡 **نصائح:**\n"
            "• يمكنك استخدام التنسيق العادي\n"
            "• الرسالة ستُرسل لجميع المستخدمين المسجلين\n"
            "• يمكنك إلغاء العملية في أي وقت\n\n"
            "اكتب رسالتك الآن:"
        )
        
        return COMPOSE_MESSAGE
    
    async def _compose_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle message composition"""
        message_text = update.message.text
        
        if message_text == "❌ إلغاء":
            return await self._cancel_broadcast(update, context)
        
        # Store message in context
        context.user_data["broadcast_message"] = message_text
        
        # Get users count
        users = self.user_storage.get_active_users()
        users_count = len(users)
        
        # Create preview
        preview_text = f"""
📋 **معاينة الرسالة:**

{message_text}

📊 **معلومات الإرسال:**
• 👥 عدد المستلمين: {users_count} مستخدم
• 📅 تاريخ الإرسال: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• 🔔 نوع الرسالة: إشعار عام

هل تريد إرسال هذه الرسالة؟
"""
        
        keyboard = [
            [
                InlineKeyboardButton("✅ إرسال", callback_data="send_broadcast"),
                InlineKeyboardButton("✏️ تعديل", callback_data="edit_broadcast")
            ],
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_broadcast")]
        ]
        
        await update.message.reply_text(
            preview_text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return PREVIEW_MESSAGE
    
    async def _preview_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle preview actions"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "send_broadcast":
            return await self._confirm_send(update, context)
        elif query.data == "edit_broadcast":
            await query.edit_message_text(
                "✏️ **تعديل الرسالة**\n\n"
                "اكتب الرسالة الجديدة:",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ إلغاء", callback_data="cancel_broadcast")
                ]])
            )
            return COMPOSE_MESSAGE
        elif query.data == "cancel_broadcast":
            return await self._cancel_broadcast(update, context)
    
    async def _confirm_send(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm and send broadcast"""
        query = update.callback_query
        await query.answer()
        
        message_text = context.user_data.get("broadcast_message", "")
        if not message_text:
            await query.edit_message_text("❌ لا توجد رسالة للإرسال")
            return ConversationHandler.END
        
        # Get active users
        users = self.user_storage.get_active_users()
        users_count = len(users)
        
        if users_count == 0:
            await query.edit_message_text(
                "❌ **لا يوجد مستخدمين نشطين**\n\n"
                "لا يمكن إرسال الرسالة لعدم وجود مستخدمين مسجلين."
            )
            return ConversationHandler.END
        
        # Add copyright footer
        full_message = f"""
{message_text}

---
🔔 **بوت الإشعارات الجامعية**
👨‍💻 المطور: عبدالرحمن عبدالقادر
📧 البريد الإلكتروني: tox098123@gmail.com
"""
        
        # Send to all users
        success_count = 0
        failed_count = 0
        
        await query.edit_message_text(
            f"📤 **جاري الإرسال...**\n\n"
            f"إرسال الرسالة لـ {users_count} مستخدم..."
        )
        
        for user in users:
            try:
                telegram_id = user.get("telegram_id")
                await update.get_bot().send_message(
                    chat_id=telegram_id,
                    text=full_message
                )
                success_count += 1
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Failed to send broadcast to user {user.get('telegram_id')}: {e}")
                failed_count += 1
        
        # Final report
        report_text = f"""
✅ **تم إرسال الإشعار العام بنجاح!**

📊 **تقرير الإرسال:**
• ✅ تم الإرسال بنجاح: {success_count} مستخدم
• ❌ فشل في الإرسال: {failed_count} مستخدم
• 📅 تاريخ الإرسال: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📋 **الرسالة المرسلة:**
{message_text[:200]}{'...' if len(message_text) > 200 else ''}
"""
        
        await query.edit_message_text(
            report_text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="admin_dashboard")
            ]])
        )
        
        # Log broadcast
        logger.info(f"Broadcast sent: {success_count} success, {failed_count} failed")
        
        return ConversationHandler.END
    
    async def _cancel_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel broadcast"""
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.edit_message_text(
                "❌ **تم إلغاء الإشعار العام**\n\n"
                "لم يتم إرسال أي رسالة.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="admin_dashboard")
                ]])
            )
        else:
            await update.message.reply_text(
                "❌ **تم إلغاء الإشعار العام**\n\n"
                "لم يتم إرسال أي رسالة.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="admin_dashboard")
                ]])
            )
        
        # Clear context
        context.user_data.clear()
        
        return ConversationHandler.END 