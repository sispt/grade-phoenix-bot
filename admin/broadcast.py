"""
🔔 Broadcast System (Corrected Version)
"""
import logging
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
from config import CONFIG

logger = logging.getLogger(__name__)

BROADCAST_MESSAGE = range(1)

class BroadcastSystem:
    """Handles sending messages to all users."""

    def __init__(self, bot):
        self.bot = bot
        # Now it correctly accesses the bot's user_storage
        self.user_storage = self.bot.user_storage

    def get_conversation_handler(self):
        return ConversationHandler(
            entry_points=[CommandHandler("broadcast", self.start_broadcast)],
            states={
                BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.send_broadcast)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_broadcast)],
        )

    async def start_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != CONFIG["ADMIN_ID"]:
            await update.message.reply_text("🚫 ليس لديك صلاحية لاستخدام هذه الميزة.")
            return ConversationHandler.END
        
        await update.message.reply_text("أرسل الرسالة التي تريد بثها للجميع. للإلغاء، استخدم /cancel.")
        return BROADCAST_MESSAGE

    async def send_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != CONFIG["ADMIN_ID"]:
            await update.message.reply_text("🚫 ليس لديك صلاحية لاستخدام هذه الميزة.")
            return ConversationHandler.END
        
        message_text = update.message.text
        active_users = self.user_storage.get_active_users() # This line will now work
        sent_count = 0
        
        for user in active_users:
            try:
                await self.bot.app.bot.send_message(chat_id=user["telegram_id"], text=message_text)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast to {user['telegram_id']}: {e}")

        await update.message.reply_text(f"✅ تم إرسال الرسالة بنجاح إلى {sent_count} من أصل {len(active_users)} مستخدم.")
        return ConversationHandler.END

    async def cancel_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("تم إلغاء عملية البث.")
        return ConversationHandler.END