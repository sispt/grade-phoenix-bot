# This is the final, correct, and clean version of bot/core.py

"""
🎓 Telegram Bot Core - Main Bot Implementation
"""
import asyncio
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    TypeHandler,
)

# Absolute imports
from config import CONFIG
from storage.models import DatabaseManager
from storage.postgresql_users import PostgreSQLUserStorage
from storage.postgresql_grades import PostgreSQLGradeStorage
from storage.users import UserStorage
from storage.grades import GradeStorage
from university.api import UniversityAPI
from admin.dashboard import AdminDashboard
from admin.broadcast import BroadcastSystem
from utils.keyboards import get_main_keyboard, get_main_keyboard_with_relogin, get_admin_keyboard, get_cancel_keyboard
from utils.messages import get_welcome_message, get_help_message

logger = logging.getLogger(__name__)

# Conversation states
ASK_USERNAME, ASK_PASSWORD = range(2)

class TelegramBot:
    """Main Telegram Bot Class"""
    
    def __init__(self):
        self.app = None
        self.db_manager = None
        self.user_storage = None
        self.grade_storage = None
        self.university_api = UniversityAPI()
        self.admin_dashboard = AdminDashboard()
        self.broadcast_system = BroadcastSystem()
        self.grade_check_task = None
        self.running = False
        self._initialize_storage()
        
    def _initialize_storage(self):
        """Initialize storage system based on configuration"""
        try:
            if CONFIG.get("USE_POSTGRESQL", False):
                logger.info("🗄️ Initializing PostgreSQL storage...")
                self.db_manager = DatabaseManager(CONFIG["DATABASE_URL"])
                if self.db_manager.test_connection():
                    self.user_storage = PostgreSQLUserStorage(self.db_manager)
                    self.grade_storage = PostgreSQLGradeStorage(self.db_manager)
                    logger.info("✅ PostgreSQL storage initialized successfully")
                else:
                    logger.error("❌ PostgreSQL connection failed, falling back to file storage")
                    self._initialize_file_storage()
            else:
                logger.info("📁 Initializing file-based storage...")
                self._initialize_file_storage()
        except Exception as e:
            logger.error(f"❌ Storage initialization failed: {e}", exc_info=True)
            self._initialize_file_storage()
    
    def _initialize_file_storage(self):
        """Initialize file-based storage as fallback"""
        self.user_storage = UserStorage()
        self.grade_storage = GradeStorage()
        logger.info("✅ File-based storage initialized successfully")
    
    async def start(self):
        """Start the bot"""
        import os
        self.app = Application.builder().token(CONFIG["TELEGRAM_TOKEN"]).build()
        await self._update_bot_info()
        self._add_handlers()
        if CONFIG["ENABLE_NOTIFICATIONS"]:
            self.grade_check_task = asyncio.create_task(self._grade_checking_loop())
        
        await self.app.initialize()
        await self.app.start()
        
        port = int(os.environ.get("PORT", 8443))
        webhook_url = os.getenv("WEBHOOK_URL", f"https://{os.getenv('RAILWAY_STATIC_URL', 'your-app-name.up.railway.app')}/{CONFIG['TELEGRAM_TOKEN']}")
        
        logger.info(f"DEBUG: Setting up webhook on port {port} with URL: {webhook_url}")
        
        try:
            await self.app.updater.start_webhook(listen="0.0.0.0", port=port, url_path=CONFIG["TELEGRAM_TOKEN"], webhook_url=webhook_url)
            logger.info("✅ Webhook started successfully")
        except Exception as webhook_error:
            logger.error(f"❌ Webhook setup failed: {webhook_error}. Falling back to polling mode.")
            await self.app.updater.start_polling()
            logger.info("✅ Polling started successfully")
        
        self.running = True
    
    async def _update_bot_info(self):
        """Update bot name and description"""
        try:
            await self.app.bot.set_my_name(CONFIG["BOT_NAME"])
            await self.app.bot.set_my_description(CONFIG["BOT_DESCRIPTION"])
            await self.app.bot.set_my_short_description("بوت إشعارات الدرجات الجامعية - جامعة الشام")
        except Exception as e:
            logger.warning(f"⚠️ Failed to update bot info: {e}")

    async def stop(self):
        """Stop the bot gracefully"""
        self.running = False
        if self.grade_check_task: self.grade_check_task.cancel()
        if self.app: await self.app.shutdown()
        logger.info("🛑 Bot stopped.")
    
    def _add_handlers(self):
        """Add all bot handlers"""
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("register", self._register_start), MessageHandler(filters.Regex("^🚀 تسجيل الدخول$"), self._register_start)],
            states={
                ASK_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._register_username)],
                ASK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._register_password)],
            },
            fallbacks=[CommandHandler("cancel", self._cancel_registration)],
        )
        self.app.add_handler(conv_handler)
        self.app.add_handler(CommandHandler("start", self._start_command))
        self.app.add_handler(CommandHandler("grades", self._grades_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
    
    async def _send_message_with_keyboard(self, update, message, keyboard_type="main"):
        keyboards = {"main": get_main_keyboard, "relogin": get_main_keyboard_with_relogin, "cancel": get_cancel_keyboard}
        keyboard = keyboards.get(keyboard_type, get_main_keyboard)()
        await update.message.reply_text(message, reply_markup=keyboard)

    async def _edit_message_no_keyboard(self, message_obj, new_text):
        try:
            await message_obj.edit_text(new_text)
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._send_message_with_keyboard(update, get_welcome_message())
    
    async def _register_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        await self._send_message_with_keyboard(update, "🚀 **تسجيل الدخول**\n\n📝 **أدخل اسم المستخدم الجامعي:**", "cancel")
        return ASK_USERNAME
    
    async def _register_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = update.message.text.strip()
        if not (3 <= len(username) <= 20 and username.replace('-', '').replace('_', '').isalnum()):
            await self._send_message_with_keyboard(update, "اسم المستخدم غير صالح. حاول مرة أخرى:", "cancel")
            return ASK_USERNAME
        context.user_data["username"] = username
        await self._send_message_with_keyboard(update, f"تم حفظ اسم المستخدم: {username}\n\nأدخل كلمة المرور:", "cancel")
        return ASK_PASSWORD

    async def _register_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        password = update.message.text.strip()
        if not password:
            await update.message.reply_text("❌ كلمة المرور غير صالحة، حاول مرة أخرى:")
            return ASK_PASSWORD

        username = context.user_data.get("username")
        telegram_id = update.effective_user.id
        loading_message = await update.message.reply_text("🔄 جاري تسجيل الدخول...")

        try:
            token = await self.university_api.login(username, password)
            if not token:
                await self._edit_message_no_keyboard(loading_message, "فشل تسجيل الدخول. تحقق من بياناتك.")
                return ConversationHandler.END

            await self._edit_message_no_keyboard(loading_message, "📊 جاري جلب بياناتك...")
            user_data = await self.university_api.get_user_data(token)
            if not user_data:
                await self._edit_message_no_keyboard(loading_message, "❌ **فشل جلب بيانات الطالب**")
                return ConversationHandler.END

            self.user_storage.save_user(telegram_id, username, password, token, user_data)
            self.grade_storage.save_grades(telegram_id, user_data.get("grades", []))
            
            await self._edit_message_no_keyboard(loading_message, f"✅ تم تسجيل الدخول بنجاح.\nمرحباً {username}.")
            await self._send_message_with_keyboard(update, "تم التسجيل. استخدم القائمة الرئيسية.")
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"DEBUG: Network error during login: {e}", exc_info=True)
            await self._edit_message_no_keyboard(loading_message, "خطأ في الاتصال. حاول لاحقاً.")
            return ConversationHandler.END

    async def _cancel_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("تم إلغاء العملية.", reply_markup=get_main_keyboard())
        return ConversationHandler.END
    
    async def _grades_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /grades command with corrected dictionary keys."""
        telegram_id = update.effective_user.id
        if not self.user_storage.is_user_registered(telegram_id):
            await update.message.reply_text("سجل دخولك أولاً.", reply_markup=get_main_keyboard())
            return

        loading_message = await update.message.reply_text("جاري فحص الدرجات...")
        try:
            session = self.user_storage.get_user_session(telegram_id)
            if not session or not session.get("token"):
                await self._edit_message_no_keyboard(loading_message, "انتهت الجلسة. سجل دخولك مجدداً.")
                await self._send_message_with_keyboard(update, "اضغط '🚀 تسجيل الدخول' لتجديد الجلسة", "relogin")
                return

            token, username = session.get("token"), session.get("username")
            
            if not await self.university_api.test_token(token):
                await self._edit_message_no_keyboard(loading_message, "الجلسة منتهية، جاري تجديدها...")
                new_token = await self.university_api.login(username, session.get("password"))
                if not new_token:
                    await self._edit_message_no_keyboard(loading_message, "فشل تجديد الجلسة. سجل دخولك مجدداً.")
                    return
                token = new_token
                self.user_storage.update_user_token(telegram_id, token)

            await self._edit_message_no_keyboard(loading_message, "جاري جلب الدرجات...")
            user_data = await self.university_api.get_user_data(token)
            
            if not user_data or not user_data.get("grades"):
                await self._edit_message_no_keyboard(loading_message, "لا توجد درجات متاحة حالياً.")
                return

            grades = user_data.get("grades", [])
            self.grade_storage.save_grades(telegram_id, grades)

            grades_text = "📊 **درجاتك الحالية:**\n\n"
            for i, grade in enumerate(grades, 1):
                course_name = grade.get("name", "غير محدد")
                course_code = grade.get("code", "")
                coursework = grade.get("coursework", "لم يتم النشر")
                final_exam = grade.get("final_exam", "لم يتم النشر")
                total = grade.get("total", "لم يتم النشر")
                
                grades_text += f"**{i}. {course_name}** ({course_code})\n • الأعمال: {coursework}\n • النظري: {final_exam}\n • النهائي: {total}\n\n"

            if len(grades_text) > 4096:
                for part in [grades_text[i:i+4096] for i in range(0, len(grades_text), 4096)]:
                    await update.message.reply_text(part)
            else:
                await self._edit_message_no_keyboard(loading_message, grades_text)

        except Exception as e:
            logger.error(f"DEBUG: Error in grades command: {e}", exc_info=True)
            await self._edit_message_no_keyboard(loading_message, "حدث خطأ أثناء جلب الدرجات. حاول لاحقاً.")
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages and button clicks"""
        text = update.message.text
        if text == "📊 فحص الدرجات":
            await self._grades_command(update, context)
        else:
            await update.message.reply_text("❓ لم أفهم طلبك. استخدم الأزرار.", reply_markup=get_main_keyboard())

    async def _check_user_grades(self, user):
        """Check grades for a specific user using corrected dictionary keys."""
        try:
            telegram_id, username, token, password = user.get("telegram_id"), user.get("username"), user.get("token"), user.get("password")
            if not token: return
            if not await self.university_api.test_token(token):
                if not password: return
                token = await self.university_api.login(username, password)
                if not token: return
                self.user_storage.update_user_token(telegram_id, token)

            user_data = await self.university_api.get_user_data(token)
            if not user_data or not user_data.get("grades"): return

            new_grades, old_grades = user_data.get("grades", []), self.grade_storage.get_grades(telegram_id)
            if old_grades != new_grades:
                old_grades_dict = {g.get('name'): g for g in old_grades}
                changes = [g for g in new_grades if g.get('name') not in old_grades_dict or old_grades_dict[g.get('name')] != g]
                if changes:
                    message = "🎓 **تم تحديث درجاتك:**\n\n"
                    for grade in changes:
                        name, code = grade.get('name', 'N/A'), grade.get('code', 'N/A')
                        cw, fe, total = grade.get('coursework', 'N/A'), grade.get('final_exam', 'N/A'), grade.get('total', 'N/A')
                        message += f"📚 **{name}** ({code})\n • الأعمال: {cw}\n • النظري: {fe}\n • النهائي: {total}\n\n"
                    await self.app.bot.send_message(chat_id=telegram_id, text=message)
                self.grade_storage.save_grades(telegram_id, new_grades)
        except Exception as e:
            logger.error(f"❌ DEBUG: Error checking grades for user {user.get('username')}: {e}", exc_info=True)

    async def _grade_checking_loop(self):
        """Main loop for checking grades"""
        while self.running:
            try:
                users = self.user_storage.get_all_users()
                await asyncio.gather(*(self._check_user_grades(user) for user in users))
            except Exception as e:
                logger.error(f"❌ Error in grade checking loop: {e}", exc_info=True)
            await asyncio.sleep(CONFIG["GRADE_CHECK_INTERVAL"] * 60)