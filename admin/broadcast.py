"""
🔔 Broadcast System (Final Version)
"""

import logging
from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

logger = logging.getLogger(__name__)
BROADCAST_MESSAGE = range(1)


class BroadcastSystem:
    def __init__(self, bot):
        self.bot = bot
        self.user_storage = bot.user_storage

    def get_conversation_handler(self):
        return ConversationHandler(
            entry_points=[CommandHandler("broadcast", self.start_broadcast)],
            states={
                BROADCAST_MESSAGE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.send_broadcast)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_broadcast)],
        )

    async def start_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = getattr(update, "callback_query", None)
        if query:
            await query.edit_message_text("أرسل الرسالة للبث للجميع. للإلغاء: /cancel.")
        else:
            await update.message.reply_text(
                "أرسل الرسالة للبث للجميع. للإلغاء: /cancel."
            )
        return BROADCAST_MESSAGE

    async def send_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        all_users = self.user_storage.get_all_users()
        sent_count = 0
        for user in all_users:
            try:
                await self.bot.app.bot.send_message(
                    chat_id=user["telegram_id"], text=update.message.text
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Broadcast failed for {user['telegram_id']}: {e}")
        await update.message.reply_text(
            f"✅ تم الإرسال إلى {sent_count}/{len(all_users)} مستخدم."
        )
        return ConversationHandler.END

    async def cancel_broadcast(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        await update.message.reply_text("تم إلغاء البث.")
        return ConversationHandler.END
