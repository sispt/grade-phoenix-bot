# This is the final, complete, and fully functional version of bot/core.py

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
from utils.keyboards import get_main_keyboard, get_admin_keyboard, get_cancel_keyboard, get_main_keyboard_with_relogin, get_unregistered_keyboard # New import
from utils.messages import get_welcome_message, get_help_message

logger = logging.getLogger(__name__)
ASK_USERNAME, ASK_PASSWORD = range(2)

class TelegramBot:
    """Main Telegram Bot Class"""
    
    def __init__(self):
        self.app = None
        self.db_manager = None
        self.user_storage = None 
        self.grade_storage = None 
        self.university_api = UniversityAPI()
        
        self._initialize_storage() 
        
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
            logger.error(f"❌ Error during PostgreSQL storage initialization: {e}", exc_info=True)
        
        if not pg_initialized:
            logger.info("📁 Initializing file-based storage as fallback.")
            try:
                self.user_storage = UserStorage()
                self.grade_storage = GradeStorage()
                logger.info("✅ File-based storage initialized successfully.")
            except Exception as e:
                logger.error(f"❌ Critical: File storage initialization also failed: {e}", exc_info=True)
                raise RuntimeError("Failed to initialize any data storage. Bot cannot operate.")

    async def start(self):
        import os
        self.app = Application.builder().token(CONFIG["TELEGRAM_TOKEN"]).build()
        await self._update_bot_info()
        self._add_handlers()
        if CONFIG["ENABLE_NOTIFICATIONS"]:
            logger.warning("GRADE CHECK LOOP SHOULD START NOW")
            self.grade_check_task = asyncio.create_task(self._grade_checking_loop())
        await self.app.initialize()
        await self.app.start()
        port = int(os.environ.get("PORT", 8443))
        webhook_url = os.getenv("WEBHOOK_URL", f"https://{os.getenv('RAILWAY_STATIC_URL', 'your-app-name.up.railway.app')}/{CONFIG['TELEGRAM_TOKEN']}")
        await self.app.updater.start_webhook(listen="0.0.0.0", port=port, url_path=CONFIG["TELEGRAM_TOKEN"], webhook_url=webhook_url)
        self.running = True
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
        logger.info("DEBUG: Adding all bot handlers...")
        reg_handler = ConversationHandler(
            entry_points=[CommandHandler("register", self._register_start), MessageHandler(filters.Regex("^🚀 تسجيل الدخول$"), self._register_start)],
            states={ASK_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._register_username)], ASK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._register_password)], },
            fallbacks=[CommandHandler("cancel", self._cancel_registration)],
        )
        self.app.add_handler(reg_handler)
        self.app.add_handler(self.broadcast_system.get_conversation_handler())
        self.app.add_handler(CommandHandler("start", self._start_command))
        self.app.add_handler(CommandHandler("help", self._help_command))
        self.app.add_handler(CommandHandler("grades", self._grades_command))
        self.app.add_handler(CommandHandler("profile", self._profile_command))
        self.app.add_handler(CommandHandler("settings", self._settings_command))
        self.app.add_handler(CommandHandler("support", self._support_command))
        self.app.add_handler(CommandHandler("admin", self._admin_command))
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))

    async def _send_message_with_keyboard(self, update, message, keyboard_type="main"):
        keyboards = {"main": get_main_keyboard, "admin": get_admin_keyboard, "cancel": get_cancel_keyboard, "relogin": get_main_keyboard_with_relogin, "unregistered": get_unregistered_keyboard} # Added unregistered
        await update.message.reply_text(message, reply_markup=keyboards.get(keyboard_type, get_main_keyboard)())
    
    async def _edit_message_no_keyboard(self, message_obj, new_text):
        try: await message_obj.edit_text(new_text)
        except Exception: pass 

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Check if user is registered to show appropriate keyboard
        telegram_id = update.effective_user.id
        if self.user_storage.is_user_registered(telegram_id):
            await self._send_message_with_keyboard(update, get_welcome_message(), "main")
        else:
            await self._send_message_with_keyboard(update, get_welcome_message(), "unregistered") # Show login button
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._send_message_with_keyboard(update, get_help_message())

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
                await update.message.reply_text("اضغط '🚀 تسجيل الدخول' للمحاولة مرة أخرى", reply_markup=get_unregistered_keyboard()) # Correct keyboard for retry
                return ConversationHandler.END
            
            await self._edit_message_no_keyboard(loading_message, "📊 جاري جلب بياناتك...")
            user_data = await self.university_api.get_user_data(token)
            if not user_data:
                await loading_message.edit_text("❌ **فشل جلب بيانات الطالب**")
                await update.message.reply_text("اضغط '🚀 تسجيل الدخول' للمحاولة مرة أخرى", reply_markup=get_unregistered_keyboard()) # Correct keyboard for retry
                return ConversationHandler.END

            self.user_storage.save_user(telegram_id, username, password, token, user_data)
            self.grade_storage.save_grades(telegram_id, user_data.get("grades", []))
            await loading_message.edit_text(f"✅ تم تسجيل الدخول بنجاح.\nمرحباً {user_data.get('fullname')}.")
            
            # This ensures the main keyboard appears after successful registration
            await update.message.reply_text("تم التسجيل. استخدم القائمة الرئيسية.", reply_markup=get_main_keyboard())
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"Login error: {e}", exc_info=True)
            await loading_message.edit_text("خطأ في الاتصال. حاول لاحقاً.")
            await update.message.reply_text("اضغط '🚀 تسجيل الدخول' للمحاولة مرة أخرى", reply_markup=get_unregistered_keyboard()) # Correct keyboard for retry
            return ConversationHandler.END

    async def _cancel_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # After cancelling, user should see unregistered keyboard if not registered, or main if they were.
        telegram_id = update.effective_user.id
        if self.user_storage.is_user_registered(telegram_id):
            await update.message.reply_text("تم إلغاء العملية.", reply_markup=get_main_keyboard())
        else:
            await update.message.reply_text("تم إلغاء العملية.", reply_markup=get_unregistered_keyboard())
        return ConversationHandler.END
    
    async def _grades_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        if not self.user_storage.is_user_registered(telegram_id):
            await update.message.reply_text("سجل دخولك أولاً.", reply_markup=get_unregistered_keyboard()) # Use unregistered keyboard if not logged in
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
                    await self._send_message_with_keyboard(update, "اضغط '🚀 تسجيل الدخول' لتجديد الجلسة", "relogin")
                    return
                token = new_token
                self.user_storage.update_user_token(telegram_id, token)

            await self._edit_message_no_keyboard(loading_message, "جاري جلب الدرجات...")
            user_data = await self.university_api.get_user_data(token)
            
            if not user_data or not user_data.get("grades"):
                await self._edit_message_no_keyboard(loading_message, "لا توجد درجات متاحة حالياً.")
                # After failure, return to main keyboard
                await update.message.reply_text("اضغط '📊 فحص الدرجات' للمحاولة مرة أخرى", reply_markup=get_main_keyboard())
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
            
            # Always return to main keyboard after success
            await update.message.reply_text("اضغط '📊 فحص الدرجات' لتحديث الدرجات", reply_markup=get_main_keyboard())

        except Exception as e:
            logger.error(f"DEBUG: Error in grades command: {e}", exc_info=True)
            await self._edit_message_no_keyboard(loading_message, "حدث خطأ أثناء جلب الدرجات. حاول لاحقاً.")
            # Always return to main keyboard after error
            await update.message.reply_text("اضغط '📊 فحص الدرجات' للمحاولة مرة أخرى", reply_markup=get_main_keyboard())
    
    async def _profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.user_storage.get_user(update.effective_user.id)
        if not user: return await update.message.reply_text("❌ لم يتم تسجيلك بعد.", reply_markup=get_unregistered_keyboard()) # Unregistered
        grades_count = len(self.grade_storage.get_grades(update.effective_user.id))
        await update.message.reply_text(f"👤 **معلوماتك الشخصية:**\n🆔 `{user.get('telegram_id')}`\n👨‍🎓 `{user.get('username', 'N/A')}`\n📧 `{user.get('email', 'N/A')}`\n📊 `{grades_count}` مواد", reply_markup=get_main_keyboard())

    async def _settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"⚙️ **الإعدادات الحالية:**\n- الإشعارات: {'🔔 مفعلة' if CONFIG['ENABLE_NOTIFICATIONS'] else '🔕 معطلة'}\n- فترة الفحص: كل {CONFIG['GRADE_CHECK_INTERVAL']} دقائق.", reply_markup=get_main_keyboard())

    async def _support_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"📞 للدعم الفني، تواصل مع المطور: {CONFIG['ADMIN_USERNAME']}", reply_markup=get_main_keyboard())

    async def _admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id == CONFIG["ADMIN_ID"]:
            await self.admin_dashboard.show_dashboard(update, context)
        else:
            await self._send_message_with_keyboard(update, "🚫 ليس لديك صلاحية لهذه العملية.")

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
            # User facing actions
            "📊 فحص الدرجات": self._grades_command,
            "❓ المساعدة": self._help_command,
            "👤 معلوماتي": self._profile_command,
            "⚙️ الإعدادات": self._settings_command,
            "📞 الدعم": self._support_command,
            # Registration Entry Point
            "🚀 تسجيل الدخول": self._register_start, # New: Direct entry for unregistered users
            # Admin Panel Entry Point
            "🎛️ لوحة التحكم": self._admin_command,
        }
        action = actions.get(text)
        if action: await action(update, context)
        else: await update.message.reply_text("❓ لم أفهم طلبك. استخدم الأزرار.", reply_markup=get_main_keyboard())

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != CONFIG["ADMIN_ID"]: return
        query = update.callback_query
        await query.answer()
        await self.admin_dashboard.handle_callback(update, context)
        
    async def _grade_checking_loop(self):
        logger.warning("GRADE CHECK LOOP IS RUNNING")
        while self.running:
            try:
                logger.warning("GRADE CHECK: Starting grade check cycle...")
                users = self.user_storage.get_all_users()
                logger.warning(f"GRADE CHECK: USERS TO CHECK: {users}")
                await asyncio.gather(*(self._check_user_grades(user) for user in users))
                logger.warning(f"GRADE CHECK: Completed. Next check in {CONFIG['GRADE_CHECK_INTERVAL']} minutes")
            except asyncio.CancelledError:
                logger.warning("GRADE CHECK: Grade checking task cancelled")
                break
            except Exception as e:
                logger.error(f"GRADE CHECK: Error in grade checking loop: {e}", exc_info=True)
                await asyncio.sleep(60) # Wait 1 minute before next attempt after an error
            await asyncio.sleep(CONFIG["GRADE_CHECK_INTERVAL"] * 60)
            
    async def _check_user_grades(self, user):
        logger.warning(f"GRADE CHECK: CHECKING GRADES FOR USER: {user}")
        try:
            telegram_id, username, token, password = user.get("telegram_id"), user.get("username"), user.get("token"), user.get("password")
            if not token:
                logger.warning(f"GRADE CHECK: User {username} has no token, skipping.")
                return
            if not await self.university_api.test_token(token):
                if not password:
                    logger.warning(f"GRADE CHECK: User {username} has no password for re-auth, skipping.")
                    return
                logger.warning(f"GRADE CHECK: Token expired for {username}. Re-authenticating...")
                token = await self.university_api.login(username, password)
                if not token:
                    logger.warning(f"GRADE CHECK: Re-authentication failed for {username}.")
                    return
                self.user_storage.update_user_token(telegram_id, token)
                logger.warning(f"GRADE CHECK: Re-authentication successful for {username}. Token updated.")
            user_data = await self.university_api.get_user_data(token)
            if not user_data or "grades" not in user_data:
                logger.warning(f"GRADE CHECK: No user data or grades for {username}.")
                return
            new_grades = user_data.get("grades", [])
            old_grades = self.grade_storage.get_grades(telegram_id)
            changed_courses = self._compare_grades(old_grades, new_grades)
            logger.warning(f"GRADE CHECK: {username} - Changed courses: {changed_courses}")
            if changed_courses:
                logger.warning(f"GRADE CHECK: Found {len(changed_courses)} grade changes for user {username}. Sending notification.")
                message = "🎓 **تم تحديث درجاتك:**\n\n"
                for grade in changed_courses:
                    name = grade.get('name', 'N/A')
                    code = grade.get('code', '')
                    coursework = grade.get('coursework', 'لم يتم النشر')
                    final_exam = grade.get('final_exam', 'لم يتم النشر')
                    total = grade.get('total', 'لم يتم النشر')
                    message += f"📚 **{name}** ({code})\n • الأعمال: {coursework}\n • النظري: {final_exam}\n • النهائي: {total}\n\n"
                try:
                    await self.app.bot.send_message(chat_id=telegram_id, text=message, parse_mode='Markdown')
                    logger.warning(f"GRADE CHECK: Grade update notification sent to user {username} (ID: {telegram_id}).")
                except Exception as e:
                    logger.error(f"GRADE CHECK: Failed to send notification to {username} (ID: {telegram_id}): {e}", exc_info=True)
                self.grade_storage.save_grades(telegram_id, new_grades)
                logger.warning(f"GRADE CHECK: Updated grades saved for user {username}.")
            else:
                logger.warning(f"GRADE CHECK: No grade changes for user {username}.")
        except Exception as e:
            logger.error(f"GRADE CHECK: Error checking grades for user {user.get('username', 'Unknown')}: {e}", exc_info=True)

    def _compare_grades(self, old_grades: List[Dict], new_grades: List[Dict]) -> List[Dict]:
        old_grades_map = {g.get('code') or g.get('name'): g for g in old_grades if g.get('code') or g.get('name')}
        changes = []
        for new_grade in new_grades:
            key = new_grade.get('code') or new_grade.get('name')
            if not key: continue
            if key not in old_grades_map or old_grades_map[key] != new_grade:
                changes.append(new_grade)
        return changes