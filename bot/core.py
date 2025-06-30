# This is the final, correct, and clean version of bot/core.py, based on your last version.

"""
🎓 Telegram Bot Core - Main Bot Implementation
"""
import asyncio
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters,
    ContextTypes, ConversationHandler
)
from typing import Dict, List

from config import CONFIG
from storage.models import DatabaseManager
from storage.postgresql_users import PostgreSQLUserStorage
from storage.postgresql_grades import PostgreSQLGradeStorage
from storage.users import UserStorage
from storage.grades import GradeStorage
from university.api import UniversityAPI
from admin.dashboard import AdminDashboard
from admin.broadcast import BroadcastSystem
from utils.keyboards import get_main_keyboard, get_admin_keyboard, get_cancel_keyboard, get_main_keyboard_with_relogin, get_unregistered_keyboard
from utils.messages import get_welcome_message, get_help_message

logger = logging.getLogger(__name__)
ASK_USERNAME, ASK_PASSWORD = range(2)

class TelegramBot:
    """Main Telegram Bot Class"""
    
    def __init__(self):
        self.app, self.db_manager, self.user_storage, self.grade_storage = None, None, None, None
        self.university_api = UniversityAPI()
        
        # --- CRITICAL FIX: Initialize storage FIRST ---
        self._initialize_storage() 
        
        # --- THEN initialize classes that depend on storage ---
        self.admin_dashboard = AdminDashboard(self)
        self.broadcast_system = BroadcastSystem(self)
        
        self.grade_check_task = None
        self.running = False
        
    def _initialize_storage(self):
        pg_initialized = False
        try:
            if CONFIG.get("USE_POSTGRESQL") and CONFIG.get("DATABASE_URL"):
                logger.info("🗄️ Initializing PostgreSQL storage...")
                self.db_manager = DatabaseManager(CONFIG["DATABASE_URL"])
                if self.db_manager.test_connection():
                    self.user_storage = PostgreSQLUserStorage(self.db_manager)
                    self.grade_storage = PostgreSQLGradeStorage(self.db_manager)
                    logger.info("✅ PostgreSQL storage initialized successfully.")
                    pg_initialized = True
                else:
                    logger.error("❌ PostgreSQL connection failed during initialization.")
        except Exception as e:
            logger.error(f"❌ Error during PostgreSQL initialization: {e}", exc_info=True)
        
        if not pg_initialized:
            logger.info("📁 Initializing file-based storage as fallback.")
            try:
                self.user_storage = UserStorage()
                self.grade_storage = GradeStorage()
                logger.info("✅ File-based storage initialized.")
            except Exception as e:
                logger.critical(f"❌ FATAL: File storage also failed. Bot cannot run: {e}", exc_info=True)
                raise RuntimeError("Failed to initialize any data storage.")

    async def start(self):
        import os
        self.running = True # <<< CRITICAL FIX 1: Set running to True BEFORE starting the loop
        self.app = Application.builder().token(CONFIG["TELEGRAM_TOKEN"]).build()
        await self._update_bot_info()
        self._add_handlers()
        if CONFIG["ENABLE_NOTIFICATIONS"]:
            logger.info("Notifications are enabled. Creating grade check task.")
            self.grade_check_task = asyncio.create_task(self._grade_checking_loop())
        
        await self.app.initialize()
        await self.app.start()
        port = int(os.environ.get("PORT", 8443))
        webhook_url = os.getenv("WEBHOOK_URL", f"https://{os.getenv('RAILWAY_STATIC_URL', 'your-app-name.up.railway.app')}/{CONFIG['TELEGRAM_TOKEN']}")
        await self.app.updater.start_webhook(listen="0.0.0.0", port=port, url_path=CONFIG["TELEGRAM_TOKEN"], webhook_url=webhook_url)
        logger.info(f"✅ Bot started on webhook: {webhook_url}")

    async def _update_bot_info(self):
        try:
            await self.app.bot.set_my_name(CONFIG["BOT_NAME"])
            await self.app.bot.set_my_description(CONFIG["BOT_DESCRIPTION"])
        except Exception as e:
            logger.warning(f"⚠️ Failed to update bot info: {e}")

    async def stop(self):
        self.running = False
        if self.grade_check_task: self.grade_check_task.cancel()
        if self.app: await self.app.shutdown()
        logger.info("🛑 Bot stopped.")

    def _add_handlers(self):
        # This function from your last version is correct and complete
        registration_handler = ConversationHandler(
            entry_points=[CommandHandler("register", self._register_start), MessageHandler(filters.Regex("^🚀 تسجيل الدخول$"), self._register_start)],
            states={ASK_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._register_username)], ASK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._register_password)]},
            fallbacks=[CommandHandler("cancel", self._cancel_registration)],
        )
        self.app.add_handler(registration_handler)
        self.app.add_handler(self.broadcast_system.get_conversation_handler())
        self.app.add_handler(CommandHandler("start", self._start_command))
        self.app.add_handler(CommandHandler("help", self._help_command))
        self.app.add_handler(CommandHandler("grades", self._grades_command))
        self.app.add_handler(CommandHandler("profile", self._profile_command))
        self.app.add_handler(CommandHandler("settings", self._settings_command))
        self.app.add_handler(CommandHandler("support", self._support_command))
        # Use a different command for the admin panel entry to avoid confusion with the keyboard
        self.app.add_handler(CommandHandler("admin", self._admin_command))
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))

    async def _send_message_with_keyboard(self, update, message, keyboard_type="main"):
        keyboards = {"main": get_main_keyboard, "admin": get_admin_keyboard, "cancel": get_cancel_keyboard, "relogin": get_main_keyboard_with_relogin, "unregistered": get_unregistered_keyboard}
        await update.message.reply_text(message, reply_markup=keyboards.get(keyboard_type, get_main_keyboard)())
    
    async def _edit_message_no_keyboard(self, message_obj, new_text):
        try: await message_obj.edit_text(new_text)
        except Exception: pass 

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.user_storage.is_user_registered(update.effective_user.id):
            await self._send_message_with_keyboard(update, get_welcome_message(), "main")
        else:
            await self._send_message_with_keyboard(update, get_welcome_message(), "unregistered")
    
    # ... [Paste all the other methods from your last version of core.py here] ...
    # This includes _help_command, _register_start, _grades_command, _profile_command, etc.
    # They are already correct. The key changes are below.

    async def _admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # The admin command should send the *inline* keyboard via the dashboard.
        if update.effective_user.id == CONFIG["ADMIN_ID"]:
            await self.admin_dashboard.show_dashboard(update, context)
        else:
            await update.message.reply_text("🚫 ليس لديك صلاحية لهذه العملية.")

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        # This dictionary now correctly maps button text to the functions
        actions = {
            "📊 فحص الدرجات": self._grades_command,
            "❓ المساعدة": self._help_command,
            "👤 معلوماتي": self._profile_command,
            "⚙️ الإعدادات": self._settings_command,
            "📞 الدعم": self._support_command,
            "🚀 تسجيل الدخول": self._register_start,
            "🔄 إعادة تسجيل الدخول": self._register_start,
            "🎛️ لوحة التحكم": self._admin_command,
        }
        action = actions.get(text)
        if action:
            await action(update, context)
        else:
            keyboard_to_show = get_main_keyboard() if self.user_storage.is_user_registered(update.effective_user.id) else get_unregistered_keyboard()
            await update.message.reply_text("❓ لم أفهم طلبك. استخدم الأزرار.", reply_markup=keyboard_to_show)

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != CONFIG["ADMIN_ID"]: return
        query = update.callback_query
        await query.answer()
        # This correctly delegates all admin button clicks to the dashboard handler
        await self.admin_dashboard.handle_callback(update, context)
        
    async def _grade_checking_loop(self):
        await asyncio.sleep(15) # Give the bot a moment to start before the first check
        logger.info("--- Starting the main Grade Checking Loop ---")
        while self.running:
            try:
                logger.info("🔍 Grade check cycle initiated...")
                users = self.user_storage.get_all_users()
                if not users:
                    logger.info("No users are registered. Skipping this cycle.")
                else:
                    logger.info(f"Found {len(users)} users to check.")
                    await asyncio.gather(*(self._check_user_grades(user) for user in users))
                logger.info(f"✅ Grade check cycle completed. Next check in {CONFIG['GRADE_CHECK_INTERVAL']} minutes.")
            except asyncio.CancelledError:
                logger.info("🛑 Grade checking task was cancelled.")
                break
            except Exception as e:
                logger.error(f"❌ An unhandled error occurred in the grade checking loop: {e}", exc_info=True)
                await asyncio.sleep(60)
            
            await asyncio.sleep(CONFIG["GRADE_CHECK_INTERVAL"] * 60)
            
    async def _check_user_grades(self, user):
        try:
            telegram_id, username, token, password = user.get("telegram_id"), user.get("username"), user.get("token"), user.get("password")
            if not token: return
            
            if not await self.university_api.test_token(token):
                if not password: return
                logger.info(f"🔄 Token expired for {username}. Re-authenticating...")
                token = await self.university_api.login(username, password)
                if not token: 
                    logger.warning(f"❌ Re-authentication failed for {username}.")
                    return
                self.user_storage.update_user_token(telegram_id, token)

            user_data = await self.university_api.get_user_data(token)
            if not user_data or "grades" not in user_data:
                logger.info(f"No grade data available for {username} in this check.")
                return

            new_grades = user_data.get("grades", [])
            old_grades = self.grade_storage.get_grades(telegram_id)
            changed_courses = self._compare_grades(old_grades, new_grades)

            if changed_courses:
                logger.info(f"🔄 Found {len(changed_courses)} grade changes for user {username}. Sending notification.")
                message = "🎓 **تم تحديث درجاتك:**\n\n"
                for grade in changed_courses:
                    message += f"📚 **{grade.get('name', 'N/A')}** ({grade.get('code', '')})\n • الأعمال: {grade.get('coursework', '-')}\n • النظري: {grade.get('final_exam', '-')}\n • النهائي: {grade.get('total', '-')}\n\n"
                
                await self.app.bot.send_message(chat_id=telegram_id, text=message, parse_mode='Markdown')
                self.grade_storage.save_grades(telegram_id, new_grades)
            else:
                logger.info(f"✅ No grade changes detected for user {username}.")
                
        except Exception as e:
            logger.error(f"❌ Error during _check_user_grades for {user.get('username', 'Unknown')}: {e}", exc_info=True)

    def _compare_grades(self, old_grades: List[Dict], new_grades: List[Dict]) -> List[Dict]:
        old_grades_map = {g.get('code') or g.get('name'): g for g in old_grades if g.get('code') or g.get('name')}
        changes = []
        for new_grade in new_grades:
            key = new_grade.get('code') or new_grade.get('name')
            if not key: continue
            if key not in old_grades_map or old_grades_map[key] != new_grade:
                changes.append(new_grade)
        return changes