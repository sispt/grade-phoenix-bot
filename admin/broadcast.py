"""
🔔 Broadcast System (Final & Complete Version)
"""
import logging
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes

logger = logging.getLogger(__name__)
BROADCAST_MESSAGE = range(1)

class BroadcastSystem:
    """Handles sending messages to all users."""

    def __init__(self, bot): # Corrected to accept bot instance
        self.bot = bot
        # Access user_storage directly from the bot object
        self.user_storage = self.bot.user_storage

    def get_conversation_handler(self):
        return ConversationHandler(
            entry_points=[CommandHandler("broadcast", self.start_broadcast)],
            states={BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.send_broadcast)]},
            fallbacks=[CommandHandler("cancel", self.cancel_broadcast)],
        )

    async def start_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Determine if the command came from a message or an inline callback
        if update.callback_query:
            # If from callback, edit the message that contained the inline button
            await update.callback_query.edit_message_text("أرسل الرسالة للبث للجميع. للإلغاء: /cancel.")
        else:
            # If from a direct command, send a new message
            await update.message.reply_text("أرسل الرسالة للبث للجميع. للإلغاء: /cancel.")
        return BROADCAST_MESSAGE

    async def send_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message_text = update.message.text
        all_users = self.user_storage.get_all_users() # This method should exist and return all users
        sent_count = 0
        
        for user in all_users:
            try:
                # Use self.bot.app.bot for sending messages within extensions
                await self.bot.app.bot.send_message(chat_id=user["telegram_id"], text=message_text)
                sent_count += 1
            except Exception as e:
                logger.error(f"❌ Failed to send broadcast to {user.get('telegram_id', 'N/A')}: {e}", exc_info=True)
        
        await update.message.reply_text(f"✅ تم إرسال الرسالة بنجاح إلى {sent_count} من أصل {len(all_users)} مستخدم.")
        return ConversationHandler.END

    async def cancel_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("تم إلغاء عملية البث.")
        return ConversationHandler.END