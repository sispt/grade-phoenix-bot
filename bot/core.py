# This is the final, correct, and clean version of bot/core.py, based on your last version.

"""
🎓 Telegram Bot Core - Main Bot Implementation
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
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
        self.running = True
        self.app = Application.builder().token(CONFIG["TELEGRAM_TOKEN"]).build()
        await self._update_bot_info()
        self._add_handlers()
        self.grade_check_task = asyncio.create_task(self._grade_checking_loop())
        await self.app.initialize()
        await self.app.start()
        port = int(os.environ.get("PORT", 8443))
        webhook_url = os.getenv("WEBHOOK_URL", f"https://{os.getenv('RAILWAY_STATIC_URL', 'your-app-name.up.railway.app')}/{CONFIG['TELEGRAM_TOKEN']}")
        await self.app.updater.start_webhook(listen="0.0.0.0", port=port, url_path=CONFIG["TELEGRAM_TOKEN"], webhook_url=webhook_url)
        logger.info(f"✅ Bot started on webhook: {webhook_url}")

    async def _update_bot_info(self):
        try:
            # Only set name/description if needed (avoid rate limit)
            current_name = await self.app.bot.get_my_name()
            if current_name.name != CONFIG["BOT_NAME"]:
                try:
                    await self.app.bot.set_my_name(CONFIG["BOT_NAME"])
                except Exception as e:
                    logger.warning(f"⚠️ Failed to set bot name: {e}")
            current_desc = await self.app.bot.get_my_description()
            if current_desc.description != CONFIG["BOT_DESCRIPTION"]:
                try:
                    await self.app.bot.set_my_description(CONFIG["BOT_DESCRIPTION"])
                except Exception as e:
                    logger.warning(f"⚠️ Failed to set bot description: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to update bot info: {e}")

    async def stop(self):
        self.running = False
        if self.grade_check_task:
            self.grade_check_task.cancel()
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
        self.app.add_handler(CommandHandler("notify_grades", self._admin_notify_grades))
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))

    async def _send_message_with_keyboard(self, update, message, keyboard_type="main"):
        keyboards = {"main": get_main_keyboard, "admin": get_admin_keyboard, "cancel": get_cancel_keyboard, "relogin": get_main_keyboard_with_relogin, "unregistered": get_unregistered_keyboard}
        await update.message.reply_text(message, reply_markup=keyboards.get(keyboard_type, get_main_keyboard)())
    
    async def _edit_message_no_keyboard(self, message_obj, new_text):
        try: await message_obj.edit_text(new_text)
        except Exception: pass 

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.user_storage.get_user(update.effective_user.id)
        fullname = user.get('fullname') if user else None
        await self._send_message_with_keyboard(update, get_welcome_message(fullname), "main" if user else "unregistered")

    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "دليل استخدام البوت:\n\n"
            "1. إذا لم تكن مسجلاً، اضغط على '🚀 تسجيل الدخول' وأدخل اسم المستخدم وكلمة المرور الجامعية.\n"
            "2. بعد التسجيل، استخدم الأزرار لفحص الدرجات أو تعديل الإعدادات.\n"
            "3. إذا واجهت أي مشكلة، استخدم زر الدعم أو تواصل مع المطور: " + str(CONFIG.get("ADMIN_USERNAME", "@admin")) + "\n\n"
            "الأوامر المتاحة:\n"
            "/start - بدء الاستخدام\n"
            "/help - المساعدة\n"
            "/grades - فحص الدرجات\n"
            "/profile - معلوماتي\n"
            "/settings - الإعدادات\n"
            "/support - الدعم الفني\n"
        )

    async def _grades_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            telegram_id = update.effective_user.id
            user = self.user_storage.get_user(telegram_id)
            if not user:
                await update.message.reply_text("❗️ يجب التسجيل أولاً.")
                return
            token = user.get("token")
            if not token:
                await update.message.reply_text("❗️ يجب إعادة تسجيل الدخول.")
                return
            # Simulate Release v2.5.0: fetch grades from API or storage
            user_data = await self.university_api.get_user_data(token)
            grades = user_data.get("grades", [])
            if not grades:
                await update.message.reply_text("لا توجد درجات متاحة حالياً.")
                return
            msg = "📚 **درجاتك الأكاديمية:**\n\n"
            for g in grades:
                msg += f"• {g.get('name', '-')} ({g.get('code', '-')})\n  الأعمال: {g.get('coursework', '-')} | النظري: {g.get('final_exam', '-')} | النهائي: {g.get('total', '-')}\n\n"
            await update.message.reply_text(msg, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text("حدث خطأ أثناء جلب الدرجات.")
            logger.error(f"Error in _grades_command: {e}", exc_info=True)

    async def _profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            telegram_id = update.effective_user.id
            user = self.user_storage.get_user(telegram_id)
            if not user:
                await update.message.reply_text("❗️ يجب التسجيل أولاً.")
                return
            msg = (
                f"👤 **معلوماتك الجامعية:**\n"
                f"• الاسم الكامل: {user.get('fullname', '-')}\n"
                f"• اسم المستخدم الجامعي: {user.get('username', '-')}\n"
            )
            await update.message.reply_text(msg, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text("حدث خطأ أثناء جلب المعلومات.")
            logger.error(f"Error in _profile_command: {e}", exc_info=True)

    async def _settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            await update.message.reply_text("⚙️ ليس لديك صلاحية لتعديل الإعدادات في الوقت الحالي.")
        except Exception as e:
            await update.message.reply_text("عذراً، حدث خطأ أثناء عرض الإعدادات.")
            logger.error(f"Error in _settings_command: {e}", exc_info=True)

    async def _support_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            await update.message.reply_text("📞 للدعم الفني تواصل مع المطور: " + str(CONFIG.get("ADMIN_USERNAME", "@admin")))
        except Exception as e:
            await update.message.reply_text("عذراً، حدث خطأ أثناء عرض الدعم.")
            logger.error(f"Error in _support_command: {e}", exc_info=True)

    async def _admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # The admin command should send the *inline* keyboard via the dashboard.
        if update.effective_user.id == CONFIG["ADMIN_ID"]:
            await self.admin_dashboard.show_dashboard(update, context)
        else:
            await update.message.reply_text("🚫 ليس لديك صلاحية لهذه العملية.")

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        # Admin user search mode
        if update.effective_user.id == CONFIG["ADMIN_ID"] and context.user_data.get('awaiting_user_search'):
            handled = await self.admin_dashboard.handle_user_search_message(update, context)
            if handled:
                return
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
            await update.message.reply_text(
                "❓ لم أفهم طلبك. استخدم الأزرار أو اكتب /help للمساعدة.",
                reply_markup=keyboard_to_show
            )

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != CONFIG["ADMIN_ID"]: return
        query = update.callback_query
        await query.answer()
        # This correctly delegates all admin button clicks to the dashboard handler
        await self.admin_dashboard.handle_callback(update, context)

    async def _admin_notify_grades(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != CONFIG["ADMIN_ID"]:
            await update.message.reply_text("🚫 ليس لديك صلاحية لهذه العملية.")
            return
        await update.message.reply_text("🔄 جاري فحص الدرجات لجميع المستخدمين...")
        count = await self._notify_all_users_grades()
        await update.message.reply_text(f"✅ تم فحص الدرجات وإشعار {count} مستخدم (إذا كان هناك تغيير).")

    async def _grade_checking_loop(self):
        await asyncio.sleep(10)  # Give the bot a moment to start
        while self.running:
            try:
                logger.info("🔔 Running scheduled grade check for all users...")
                await self._notify_all_users_grades()
            except Exception as e:
                logger.error(f"❌ Error in scheduled grade check: {e}", exc_info=True)
            interval = CONFIG.get('GRADE_CHECK_INTERVAL', 10) * 60  # minutes to seconds
            await asyncio.sleep(interval)

    async def _notify_all_users_grades(self):
        users = self.user_storage.get_all_users()
        notified_count = 0
        semaphore = asyncio.Semaphore(CONFIG.get('MAX_CONCURRENT_REQUESTS', 5))
        tasks = []
        results = []

        async def check_user(user):
            async with semaphore:
                try:
                    return await self._check_and_notify_user_grades(user)
                except Exception as e:
                    logger.error(f"❌ Error in parallel grade check for user {user.get('username', 'Unknown')}: {e}", exc_info=True)
                    return False

        for user in users:
            tasks.append(asyncio.create_task(check_user(user)))
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            notified_count = sum(1 for r in results if r is True)
        return notified_count

    async def _check_and_notify_user_grades(self, user):
        try:
            telegram_id = user.get("telegram_id")
            username = user.get("username")
            token = user.get("token")
            password = user.get("password")
            if not token:
                return False
            # Re-authenticate if needed
            if not await self.university_api.test_token(token):
                if not password:
                    return False
                logger.info(f"🔄 Token expired for {username}. Re-authenticating...")
                token = await self.university_api.login(username, password)
                if not token:
                    logger.warning(f"❌ Re-authentication failed for {username}.")
                    return False
                self.user_storage.update_user_token(telegram_id, token)
            user_data = await self.university_api.get_user_data(token)
            if not user_data or "grades" not in user_data:
                logger.info(f"No grade data available for {username} in this check.")
                return False
            new_grades = user_data.get("grades", [])
            old_grades = self.grade_storage.get_grades(telegram_id)
            changed_courses = self._compare_grades(old_grades, new_grades)
            if changed_courses:
                logger.warning(f"GRADE CHECK: Found {len(changed_courses)} grade changes for user {username}. Sending notification.")
                display_name = user.get('fullname') or user.get('username', 'المستخدم')
                message = f"🎓 **{display_name}، تم تحديث درجاتك:**\n\n"
                # Build a map for old grades for quick lookup
                old_map = {g.get('code') or g.get('name'): g for g in old_grades if g.get('code') or g.get('name')}
                for grade in changed_courses:
                    name = grade.get('name', 'N/A')
                    code = grade.get('code', '-')
                    coursework = grade.get('coursework', 'لم يتم النشر')
                    final_exam = grade.get('final_exam', 'لم يتم النشر')
                    total = grade.get('total', 'لم يتم النشر')
                    key = code if code != '-' else name
                    old = old_map.get(key, {})
                    def show_change(field):
                        old_val = old.get(field, '—')
                        new_val = grade.get(field, '—')
                        if old_val != new_val and old_val != '—':
                            return f"{old_val} → {new_val}"
                        return f"{new_val}"
                    message += f"📚 **{name}** ({code})\n"
                    message += f" • الأعمال: {show_change('coursework')}\n"
                    message += f" • النظري: {show_change('final_exam')}\n"
                    message += f" • النهائي: {show_change('total')}\n\n"
                # Add update time in UTC+3
                now_utc3 = datetime.now(timezone.utc) + timedelta(hours=3)
                message += f"🕒 وقت التحديث: {now_utc3.strftime('%Y-%m-%d %H:%M')} (UTC+3)"
                try:
                    await self.app.bot.send_message(chat_id=telegram_id, text=message, parse_mode='Markdown')
                    logger.warning(f"GRADE CHECK: Grade update notification sent to user {username} (ID: {telegram_id}).")
                except Exception as e:
                    logger.error(f"❌ Error sending grade update notification: {e}", exc_info=True)
                self.grade_storage.save_grades(telegram_id, new_grades)
                return True
            else:
                # Always update the grades in DB, even if not changed
                self.grade_storage.save_grades(telegram_id, new_grades)
                return False
        except Exception as e:
            logger.error(f"❌ Exception in _check_and_notify_user_grades for user {user.get('username', 'Unknown')}: {e}", exc_info=True)
            return False

    def _compare_grades(self, old_grades: List[Dict], new_grades: List[Dict]) -> List[Dict]:
        """
        Return only courses where important fields (total, coursework, final_exam) changed.
        """
        def extract_relevant(grade):
            return {
                'code': grade.get('code') or grade.get('name'),
                'total': grade.get('total'),
                'coursework': grade.get('coursework'),
                'final_exam': grade.get('final_exam'),
            }
        old_map = {g.get('code') or g.get('name'): extract_relevant(g) for g in old_grades if g.get('code') or g.get('name')}
        changed = []
        for new_grade in new_grades:
            key = new_grade.get('code') or new_grade.get('name')
            if not key:
                continue
            relevant_new = extract_relevant(new_grade)
            relevant_old = old_map.get(key)
            if relevant_old is None or relevant_new != relevant_old:
                changed.append(new_grade)
        return changed

    async def _register_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "يرجى إدخال اسم المستخدم الجامعي الخاص بك. إذا احتجت للمساعدة، اضغط على '❓ المساعدة'."
        )
        return ASK_USERNAME

    async def _register_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['username'] = update.message.text.strip()
        await update.message.reply_text("يرجى إدخال كلمة المرور:")
        return ASK_PASSWORD

    async def _register_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = context.user_data.get('username')
        password = update.message.text.strip()
        telegram_id = update.effective_user.id
        # Here you would call your UniversityAPI to verify credentials and get token
        # For now, just simulate success
        user_data = {"username": username, "fullname": username, "email": "-"}
        self.user_storage.save_user(telegram_id, username, password, token="dummy_token", user_data=user_data)
        await update.message.reply_text(get_welcome_message(user_data.get('fullname')))
        return ConversationHandler.END

    async def _cancel_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("تم إلغاء التسجيل.")
        return ConversationHandler.END