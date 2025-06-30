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
)
from typing import Dict, List

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
        # Pass the bot instance to the admin classes
        self.admin_dashboard = AdminDashboard(self)
        self.broadcast_system = BroadcastSystem(self)
        self.grade_check_task = None
        self.running = False
        self._initialize_storage()
        
    def _initialize_storage(self):
        try:
            if CONFIG.get("USE_POSTGRESQL", False) and CONFIG.get("DATABASE_URL"):
                logger.info("🗄️ Initializing PostgreSQL storage...")
                self.db_manager = DatabaseManager(CONFIG["DATABASE_URL"])
                if self.db_manager.test_connection():
                    self.user_storage = PostgreSQLUserStorage(self.db_manager)
                    self.grade_storage = PostgreSQLGradeStorage(self.db_manager)
                    logger.info("✅ PostgreSQL storage initialized successfully")
                    return
                else:
                    logger.error("❌ PostgreSQL connection failed, falling back to file storage")
            
            logger.info("📁 Initializing file-based storage...")
            self._initialize_file_storage()

        except Exception as e:
            logger.error(f"❌ Storage initialization failed: {e}", exc_info=True)
            self._initialize_file_storage()
    
    def _initialize_file_storage(self):
        self.user_storage = UserStorage()
        self.grade_storage = GradeStorage()
        logger.info("✅ File-based storage initialized successfully")
    
    async def start(self):
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
        try:
            await self.app.bot.set_my_name(CONFIG["BOT_NAME"])
            await self.app.bot.set_my_description(CONFIG["BOT_DESCRIPTION"])
            await self.app.bot.set_my_short_description("بوت الإشعارات الجامعية - جامعة الشام")
        except Exception as e:
            logger.warning(f"⚠️ Failed to update bot info: {e}")

    async def stop(self):
        self.running = False
        if self.grade_check_task: self.grade_check_task.cancel()
        if self.app: await self.app.shutdown()
        logger.info("🛑 Bot stopped.")
    
    def _add_handlers(self):
        logger.info("DEBUG: Adding all bot handlers...")

        registration_handler = ConversationHandler(
            entry_points=[CommandHandler("register", self._register_start), MessageHandler(filters.Regex("^🚀 تسجيل الدخول$"), self._register_start)],
            states={ ASK_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._register_username)], ASK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._register_password)], },
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
        self.app.add_handler(CommandHandler("stats", self._stats_command))
        self.app.add_handler(CommandHandler("list_users", self._list_users_command))
        self.app.add_handler(CommandHandler("restart", self._restart_command))
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        logger.info("✅ All handlers added successfully!")

    async def _send_message_with_keyboard(self, update, message, keyboard_type="main"):
        keyboards = {"main": get_main_keyboard, "relogin": get_main_keyboard_with_relogin, "cancel": get_cancel_keyboard, "admin": get_admin_keyboard}
        keyboard = keyboards.get(keyboard_type, get_main_keyboard)()
        await update.message.reply_text(message, reply_markup=keyboard)

    async def _edit_message_no_keyboard(self, message_obj, new_text):
        try:
            await message_obj.edit_text(new_text)
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = get_welcome_message() + f"\n\nالإصدار: {CONFIG['BOT_VERSION']}"
        await self._send_message_with_keyboard(update, msg)
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = get_help_message() + f"\n\nالإصدار: {CONFIG['BOT_VERSION']}"
        await self._send_message_with_keyboard(update, msg)

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

        username, telegram_id = context.user_data.get("username"), update.effective_user.id
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

            token, username, password = session.get("token"), session.get("username"), session.get("password")
            
            if not await self.university_api.test_token(token):
                await self._edit_message_no_keyboard(loading_message, "الجلسة منتهية، جاري تجديدها...")
                new_token = await self.university_api.login(username, password)
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
                grades_text += f"**{i}. {grade.get('name', '')}** ({grade.get('code', '')})\n • الأعمال: {grade.get('coursework', '-')}\n • النظري: {grade.get('final_exam', '-')}\n • النهائي: {grade.get('total', '-')}\n\n"

            if len(grades_text) > 4096:
                for part in [grades_text[i:i+4096] for i in range(0, len(grades_text), 4096)]:
                    await update.message.reply_text(part)
            else:
                await self._edit_message_no_keyboard(loading_message, grades_text)

        except Exception as e:
            logger.error(f"DEBUG: Error in grades command: {e}", exc_info=True)
            await self._edit_message_no_keyboard(loading_message, "حدث خطأ أثناء جلب الدرجات. حاول لاحقاً.")
    
    async def _profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        user = self.user_storage.get_user(telegram_id)
        if not user:
            await update.message.reply_text("❌ لم يتم تسجيلك بعد.", reply_markup=get_main_keyboard())
            return
        grades = self.grade_storage.get_grades(telegram_id)
        message = f"👤 **معلوماتك الشخصية:**\n🆔 `{telegram_id}`\n👨‍🎓 `{user.get('username', 'N/A')}`\n📧 `{user.get('email', 'N/A')}`\n📊 `{len(grades)}` مواد"
        await update.message.reply_text(message)

    async def _settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("⚙️ قسم الإعدادات قيد التطوير.")
        
    async def _support_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"📞 للدعم، تواصل مع المطور: {CONFIG['ADMIN_USERNAME']}")

    async def _stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != CONFIG["ADMIN_ID"]: return
        await self.admin_dashboard.show_dashboard(update, context)

    async def _list_users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != CONFIG["ADMIN_ID"]: return
        await self.admin_dashboard.list_users_command(update, context)

    async def _restart_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != CONFIG["ADMIN_ID"]: return
        await update.message.reply_text("🔄 جارٍ إعادة تشغيل البوت...")
        logger.info("Soft restart command received from admin.")
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        actions = {
            "📊 فحص الدرجات": self._grades_command,
            "❓ المساعدة": self._help_command,
            "👤 معلوماتي": self._profile_command,
            "⚙️ الإعدادات": self._settings_command,
            "📞 الدعم": self._support_command,
            "🎛️ لوحة التحكم": self._stats_command, # Admin button
        }
        action = actions.get(text)
        if action:
            await action(update, context)
        else:
            await update.message.reply_text("❓ لم أفهم طلبك. استخدم الأزرار.", reply_markup=get_main_keyboard())

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        if query.from_user.id != CONFIG["ADMIN_ID"]: return
        await self.admin_dashboard.handle_callback(update, context)

    async def _grade_checking_loop(self):
        while self.running:
            try:
                users = self.user_storage.get_all_users()
                await asyncio.gather(*(self._check_user_grades(user) for user in users))
            except Exception as e:
                logger.error(f"❌ Error in grade checking loop: {e}", exc_info=True)
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
            if not user_data or "grades" not in user_data: return

            new_grades = user_data.get("grades", [])
            old_grades = self.grade_storage.get_grades(telegram_id)
            
            changed_courses = self._compare_grades(old_grades, new_grades)

            if changed_courses:
                logger.info(f"🔄 Found {len(changed_courses)} grade changes for user {username}")
                message = "🎓 **تم تحديث درجاتك:**\n\n"
                for grade in changed_courses:
                    message += f"📚 **{grade.get('name', 'N/A')}** ({grade.get('code', 'N/A')})\n • الأعمال: {grade.get('coursework', '-')}\n • النظري: {grade.get('final_exam', '-')}\n • النهائي: {grade.get('total', '-')}\n\n"
                
                await self.app.bot.send_message(chat_id=telegram_id, text=message)
                self.grade_storage.save_grades(telegram_id, new_grades)
            else:
                logger.info(f"✅ No grade changes for user {username}.")
                
        except Exception as e:
            logger.error(f"❌ DEBUG: Error checking grades for user {user.get('username')}: {e}", exc_info=True)

    def _compare_grades(self, old_grades: List[Dict], new_grades: List[Dict]) -> List[Dict]:
        old_grades_map = {g.get('code', g.get('name')): g for g in old_grades}
        changes = []
        for new_grade in new_grades:
            key = new_grade.get('code', new_grade.get('name'))
            if key not in old_grades_map or old_grades_map[key] != new_grade:
                changes.append(new_grade)
        return changes