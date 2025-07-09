"""
🎓 Telegram Bot Core - Main Bot Implementation
"""
import asyncio
from datetime import datetime, timedelta, timezone

from sqlalchemy import update
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters,
    ContextTypes, ConversationHandler
)
from typing import Dict, List
import re
import os
import json

from config import CONFIG
from storage.models import DatabaseManager
from storage.user_storage_v2 import UserStorageV2
from storage.grade_storage_v2 import GradeStorageV2
from admin.dashboard import AdminDashboard
from admin.broadcast import BroadcastSystem
from utils.keyboards import (
    get_main_keyboard, get_main_keyboard_with_admin, get_admin_keyboard, get_cancel_keyboard, 
    get_unregistered_keyboard, remove_keyboard, get_error_recovery_keyboard, get_registration_keyboard,
    get_enhanced_admin_dashboard_keyboard, get_user_management_keyboard, get_broadcast_confirmation_keyboard,
    get_system_actions_keyboard, get_settings_main_keyboard, get_session_settings_keyboard,
    get_privacy_settings_keyboard, get_contact_support_inline_keyboard
)
from utils.messages import get_welcome_message, get_help_message, get_simple_welcome_message, get_security_welcome_message, get_credentials_security_info_message
from security.enhancements import security_manager, is_valid_length
from security.headers import security_headers, security_policy
from utils.analytics import GradeAnalytics
from utils.settings import UserSettings
from university.api_client_v2 import UniversityAPIV2
from utils.logger import get_bot_logger

# Get bot logger
logger = get_bot_logger()
# Add new states for session choice and password confirmation
ASK_USERNAME, ASK_PASSWORD, ASK_SESSION_TYPE, ASK_PASSWORD_CONFIRM = range(4)
ASK_GPA_COURSE_COUNT, ASK_GPA_PERCENTAGE, ASK_GPA_ECTS = range(10, 13)
# Add new states for settings/session management
ASK_SETTINGS_MAIN, ASK_SESSION_MANAGEMENT = 20, 21
# Add new state for older terms selection
ASK_OLDER_TERM_NUMBER = 30

class TelegramBot:
    """Main Telegram Bot Class"""
    
    def __init__(self):
        self.app, self.db_manager, self.user_storage, self.grade_storage = None, None, None, None
        self.university_api = UniversityAPIV2()
        # Initialize storage before other components
        self._initialize_storage() 
        # Initialize components that depend on storage
        self.grade_analytics = GradeAnalytics(self.user_storage)
        self.user_settings = UserSettings(self.user_storage)
        self.admin_dashboard = AdminDashboard(self)
        self.broadcast_system = BroadcastSystem(self)
        self.grade_check_task = None
        self.running = False
        self._user_locks = {}  # username_unique: asyncio.Lock

    def _initialize_storage(self):
        pg_initialized = False
        # Initialize new clean storage systems
        try:
            logger.info("🗄️ Initializing new clean storage systems...")
            self.user_storage = UserStorageV2(CONFIG["MYSQL_URL"])
            self.grade_storage = GradeStorageV2(CONFIG["MYSQL_URL"])
            logger.info("✅ New storage systems initialized successfully.")
        except Exception as e:
            logger.critical(f"❌ FATAL: Storage initialization failed. Bot cannot run: {e}", exc_info=True)
            raise RuntimeError("Failed to initialize storage systems.")

    def _get_user_lock(self, username_unique):
        if username_unique not in self._user_locks:
            self._user_locks[username_unique] = asyncio.Lock()
        return self._user_locks[username_unique]

    async def start(self):
        self.running = True
        self.app = Application.builder().token(CONFIG["TELEGRAM_TOKEN"]).build()
        await self._update_bot_info()
        self._add_handlers()
        await self.app.initialize()
        await self.app.start()
        port = int(os.environ.get("PORT", 8000))
        
        # Try to get Railway URL from environment
        railway_app_name = os.getenv("RAILWAY_APP_NAME")
        
        # Use WEBHOOK_URL if it's a full URL
        webhook_url_env = os.getenv("WEBHOOK_URL")
        if webhook_url_env and webhook_url_env.startswith("https://"):
            # Use the provided webhook URL
            webhook_url = webhook_url_env
            railway_url = webhook_url_env.replace(f"/{CONFIG['TELEGRAM_TOKEN']}", "")
        else:
            # Build webhook URL from Railway domain
            railway_url = (
                webhook_url_env or 
                os.getenv("RAILWAY_STATIC_URL") or 
                os.getenv("RAILWAY_PUBLIC_DOMAIN") or
                os.getenv("RAILWAY_DOMAIN") or
                (f"{railway_app_name}.up.railway.app" if railway_app_name else None) or
                "your-app-name.up.railway.app"  # fallback if nothing else is set
            )
            
            # Final webhook URL
            webhook_url = f"https://{railway_url}/{CONFIG['TELEGRAM_TOKEN']}"
        
        logger.info(f"🌐 Webhook URL: {webhook_url}")
        logger.info(f"🔧 Railway URL source: {railway_url}")
        
        await self.app.updater.start_webhook(listen="0.0.0.0", port=port, url_path=CONFIG["TELEGRAM_TOKEN"], webhook_url=webhook_url)
        logger.info(f"✅ Bot started on webhook: {webhook_url}")

        # Start background tasks only if not running under cron
        if os.getenv("RUN_GRADE_CHECK") != "1":
            self.grade_check_task = asyncio.create_task(self._grade_checking_loop())
            self.daily_quote_task = asyncio.create_task(self.scheduled_daily_quote_broadcast())

    async def _update_bot_info(self):
        try:
            # Only update bot name/description if needed
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
        if hasattr(self, 'daily_quote_task') and self.daily_quote_task:
            self.daily_quote_task.cancel()
        if self.app:
            await self.app.stop()
            await self.app.shutdown()
        logger.info("🛑 Bot stopped.")

    def _add_handlers(self):
        # Register all bot handlers
        registration_handler = ConversationHandler(
            entry_points=[
                CommandHandler("register", self._register_start),
                MessageHandler(filters.Regex("^🚀 تسجيل الدخول للجامعة$"), self._register_start)
            ],
            states={
                ASK_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._register_username)],
                ASK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._register_password)],
                ASK_SESSION_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._register_session_type)],
                ASK_PASSWORD_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._register_password_confirm)],
            },
            fallbacks=[CommandHandler("cancel", self._cancel_registration), MessageHandler(filters.Regex("^❌ إلغاء$"), self._cancel_registration)],
        )
        self.app.add_handler(registration_handler)
        self.app.add_handler(self.broadcast_system.get_conversation_handler())
        self.app.add_handler(CommandHandler("start", self._start_command))
        self.app.add_handler(CommandHandler("help", self._help_command))
        self.app.add_handler(CommandHandler("grades", self._grades_command))
        self.app.add_handler(CommandHandler("old_grades", self._old_grades_command))
        self.app.add_handler(CommandHandler("profile", self._profile_command))
        self.app.add_handler(CommandHandler("settings", self._settings_command))
        self.app.add_handler(CommandHandler("support", self._support_command))
        # Security-related commands
        self.app.add_handler(CommandHandler("security_info", self._security_info_command))
        self.app.add_handler(CommandHandler("security_audit", self._security_audit_command))
        self.app.add_handler(CommandHandler("privacy_policy", self._privacy_policy_command))
        self.app.add_handler(CommandHandler("security_stats", self._security_stats_command))
        self.app.add_handler(CommandHandler("security_headers", self._security_headers_command))
        # Admin panel command
        self.app.add_handler(CommandHandler("admin", self._admin_command))
        self.app.add_handler(CommandHandler("notify_grades", self._admin_notify_grades))
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))
        gpa_calc_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^🧮 حساب المعدل المخصص$"), self._gpa_calc_start)],
            states={
                ASK_GPA_COURSE_COUNT: [
                    MessageHandler(filters.Regex("^❌ إلغاء$"), self._cancel_gpa_calc),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._gpa_ask_course_count)
                ],
                ASK_GPA_PERCENTAGE: [
                    MessageHandler(filters.Regex("^❌ إلغاء$"), self._cancel_gpa_calc),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._gpa_ask_percentage)
                ],
                ASK_GPA_ECTS: [
                    MessageHandler(filters.Regex("^❌ إلغاء$"), self._cancel_gpa_calc),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._gpa_ask_ects)
                ],
            },
            fallbacks=[
                CommandHandler("cancel", self._cancel_gpa_calc),
                MessageHandler(filters.Regex("^❌ إلغاء$"), self._cancel_gpa_calc)
            ],
            allow_reentry=True,
        )
        self.app.add_handler(gpa_calc_handler)
        # Move older_terms_handler above the generic handler
        older_terms_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex("^📅 جميع الفصول$"), self._older_terms_command)],
            states={
                ASK_OLDER_TERM_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._ask_older_term_number)],
            },
            fallbacks=[MessageHandler(filters.Regex("^❌ إلغاء$"), self._cancel_registration)],
        )
        self.app.add_handler(older_terms_handler)
        # The generic handler must come after all ConversationHandlers
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        self.app.add_handler(CallbackQueryHandler(self._settings_callback_handler, pattern="^(back_to_main|cancel_action)$"))
        settings_handler = ConversationHandler(
            entry_points=[CommandHandler("settings", self._settings_command)],
            states={
                ASK_SETTINGS_MAIN: [MessageHandler(filters.Regex("^🔑 إدارة الجلسة/كلمة المرور$"), self._session_management_start)],
                ASK_SESSION_MANAGEMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_session_management)],
            },
            fallbacks=[MessageHandler(filters.Regex("^🔙 العودة$"), self._return_to_main)],
        )
        self.app.add_handler(settings_handler)

    async def _send_message_with_keyboard(self, update, message, keyboard_type="main"):
        keyboards = {
            "main": get_main_keyboard, 
            "admin": get_admin_keyboard, 
            "cancel": get_cancel_keyboard, 
            "unregistered": get_unregistered_keyboard,
            "error_recovery": get_error_recovery_keyboard
        }
        await update.message.reply_text(message, reply_markup=keyboards.get(keyboard_type, get_main_keyboard)())
    
    async def _send_message_without_keyboard(self, update, message):
        """Send message and remove any existing keyboard."""
        await update.message.reply_text(message, reply_markup=remove_keyboard())
    
    async def _edit_message_no_keyboard(self, message_obj, new_text):
        try: await message_obj.edit_text(new_text)
        except Exception: pass 

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.user_storage.get_user(update.effective_user.id)
        fullname = user.get('fullname') if user else None
        
        # Show user-friendly welcome message
        if user:
            # Registered user - show simple welcome with security info
            welcome_message = get_security_welcome_message()
            await self._send_message_with_keyboard(update, welcome_message, "main")
        else:
            # New user - show simple explanation
            welcome_message = get_simple_welcome_message()
            await self._send_message_with_keyboard(update, welcome_message, "unregistered")

    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        is_admin = user_id == CONFIG["ADMIN_ID"]
        help_text = (
            "🎓 دليل استخدام البوت\n\n"
            "كيفية الاستخدام:\n"
            "1. اضغط '🚀 تسجيل الدخول' وأدخل بياناتك الجامعية\n"
            "2. استخدم الأزرار لفحص الدرجات والإعدادات\n"
            "3. استعمل الأزرار للمساعدة أو الدعم الفني\n\n"
            "الأوامر الأساسية:\n"
            "/start - بدء الاستخدام\n"
            "/help - المساعدة\n"
            "/grades - التحقق من درجات الفصل الحالي\n"
            "/old_grades - التحقق من درجات الفصل السابق\n"
            "/profile - معلوماتي\n"
            "/settings - الإعدادات\n"
            "/support - الدعم الفني\n\n"
            "أوامر الأمان:\n"
            "/security_info - معلومات الأمان\n"
            "/security_audit - تقرير التدقيق الأمني\n"
            "/security_headers - معلومات معايير الأمان (للمطور فقط)\n"
            "/privacy_policy - سياسة الخصوصية\n"
        )
        if is_admin:
            help_text += "\nأوامر المدير:\n/security_stats - إحصائيات الأمان\n/admin - لوحة التحكم\n"
        help_text += f"\n👨‍💻 المطور: {CONFIG.get('ADMIN_USERNAME', '@admin')}"
        try:
            await update.message.reply_text(help_text)
        except Exception as e:
            logger.error(f"Error sending help message: {e}")

    async def _security_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            from admin.dashboard import AdminDashboard
            security_info = AdminDashboard.get_user_security_info()
            await update.message.reply_text(security_info, reply_markup=get_main_keyboard())
        except Exception as e:
            await update.message.reply_text("عذراً، حدث خطأ أثناء عرض معلومات الأمان.", reply_markup=get_main_keyboard())
            logger.error(f"Error in _security_info_command: {e}", exc_info=True)

    async def _security_audit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            audit_message = (
                "📋 تقرير التدقيق الأمني:\n\n"
                "• جميع العمليات في البوت تخضع لمراجعة دورية لضمان الأمان.\n"
                "• لا يتم تخزين كلمات المرور أو مشاركتها مع أي جهة.\n"
                "• نستخدم أحدث معايير الأمان لحماية بياناتك.\n\n"
                "إذا كان لديك أي سؤال عن الأمان، تواصل مع الدعم الفني."
            )
            await update.message.reply_text(audit_message, reply_markup=get_main_keyboard())
        except Exception as e:
            await update.message.reply_text("عذراً، حدث خطأ أثناء عرض تقرير التدقيق.", reply_markup=get_main_keyboard())
            logger.error(f"Error in _security_audit_command: {e}", exc_info=True)

    async def _privacy_policy_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            privacy_message = (
                "🔒 سياسة الخصوصية:\n\n"
                "• بياناتك الجامعية تُستخدم فقط لجلب الدرجات ولا يتم تخزين كلمة المرور نهائياً.\n"
                "• جميع المعلومات مشفرة وآمنة ولا يتم مشاركتها مع أي جهة خارجية.\n"
                "• يمكنك حذف بياناتك في أي وقت من خلال الدعم الفني.\n"
                "• هدفنا هو حماية خصوصيتك وتقديم أفضل تجربة ممكنة.\n\n"
                "لأي استفسار عن الخصوصية، تواصل مع الدعم الفني."
            )
            await update.message.reply_text(privacy_message, reply_markup=get_main_keyboard())
        except Exception as e:
            await update.message.reply_text("عذراً، حدث خطأ أثناء عرض سياسة الخصوصية.", reply_markup=get_main_keyboard())
            logger.error(f"Error in _privacy_policy_command: {e}", exc_info=True)

    async def _security_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if update.effective_user.id != CONFIG["ADMIN_ID"]:
                await update.message.reply_text("🚫 هذا الأمر متاح للمدير فقط.", reply_markup=get_main_keyboard())
                return
            stats = security_manager.get_security_stats()
            
            # Support both old and new stats structures
            total_events = stats.get('total_events_24h', 0)
            failed_logins = stats.get('failed_logins', 0)
            blocked_attempts = stats.get('blocked_attempts', 0)
            active_sessions = stats.get('active_sessions', 0)
            high_risk_events = stats.get('high_risk_events', 0)
            
            # Extract nested stats if present
            if 'rate_limiter' in stats:
                blocked_attempts = stats.get('rate_limiter', {}).get('blocked_users', 0)
            if 'session_manager' in stats:
                active_sessions = stats.get('session_manager', {}).get('active_sessions', 0)
            
            stats_message = (
                "🔐 إحصائيات الأمان (24 ساعة)\n\n"
                f"📊 إجمالي الأحداث: {total_events}\n"
                f"❌ محاولات تسجيل فاشلة: {failed_logins}\n"
                f"🚫 محاولات محظورة: {blocked_attempts}\n"
                f"👥 الجلسات النشطة: {active_sessions}\n"
                f"⚠️ أحداث عالية الخطورة: {high_risk_events}\n\n"
                "💡 هذه الإحصائيات تساعد في مراقبة الأمان"
            )
            await update.message.reply_text(stats_message, reply_markup=get_main_keyboard())
        except Exception as e:
            await update.message.reply_text("عذراً، حدث خطأ أثناء جلب إحصائيات الأمان.", reply_markup=get_main_keyboard())
            logger.error(f"Error in _security_stats_command: {e}", exc_info=True)

    async def _security_headers_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            headers_message = (
                "🛡️ معلومات الأمان:\n\n"
                "• البوت يستخدم تقنيات حماية متقدمة لضمان سرية بياناتك.\n"
                "• جميع الاتصالات مشفرة وآمنة.\n"
                "• لا داعي للقلق بشأن الخصوصية أو الأمان.\n\n"
                "لأي استفسار، تواصل مع الدعم الفني."
            )
            await update.message.reply_text(headers_message, reply_markup=get_main_keyboard())
        except Exception as e:
            await update.message.reply_text("عذراً، حدث خطأ أثناء جلب معلومات الأمان.", reply_markup=get_main_keyboard())
            logger.error(f"Error in _security_headers_command: {e}", exc_info=True)

    async def _grades_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            logger.info(f"🔍 _grades_command called for user {update.effective_user.id}")
            context.user_data['last_action'] = 'grades'
            telegram_id = update.effective_user.id
            user = self.user_storage.get_user(telegram_id)
            logger.info(f"📊 User lookup result: {user is not None}")
            if not user:
                logger.warning(f"❌ User {telegram_id} not found in storage")
                await update.message.reply_text("❗️ يجب التسجيل أولاً.", reply_markup=get_unregistered_keyboard())
                return
            token = user.get("session_token")
            logger.info(f"🔑 Token found: {token is not None}")
            if not token:
                logger.warning(f"❌ No token for user {telegram_id}")
                await update.message.reply_text("❗️ يجب إعادة تسجيل الدخول.", reply_markup=get_unregistered_keyboard())
                return
            
            # Test token validity first
            logger.info(f"🔍 Testing token validity for user {telegram_id}")
            if not await self.university_api.test_token(token):
                logger.warning(f"❌ Invalid token for user {telegram_id}")
                
                # Token is invalid, force logout
                logger.warning(f"❌ Invalid token for user {user.get('username', 'Unknown')}, forcing logout")
                await self._force_logout_user(telegram_id, update)
                return
            
            logger.info(f"🌐 Calling get_user_data for user {telegram_id}")
            user_data = await self.university_api.get_user_data(token)
            logger.info(f"📊 User data result: {user_data is not None}")
            
            # Check if user_data is None (API error) or has no grades
            if not user_data:
                logger.warning(f"❌ API error for user {telegram_id}, forcing logout")
                await self._force_logout_user(telegram_id, update)
                return
            
            grades = user_data.get("grades", [])
            logger.info(f"📈 Grades count: {len(grades) if grades else 0}")
            
            if not grades:
                logger.warning(f"⚠️ No grades found for user {telegram_id}")
                await update.message.reply_text("لا يوجد درجات متاحة بعد.", reply_markup=get_main_keyboard())
                return

            # Always save grades to the grade table after fetching
            self.grade_storage.store_grades(user.get('username'), grades)

            # Format grades with quote
            logger.info(f"📝 Formatting grades for user {telegram_id}")
            message = await self.grade_analytics.format_current_grades_with_quote(telegram_id, grades)
            logger.info(f"✅ Sending formatted message to user {telegram_id}")
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_keyboard())
        except Exception as e:
            logger.error(f"[ALERT] Error in _grades_command: {e}", exc_info=True)
            admin_id = CONFIG.get("ADMIN_ID")
            admin_username = CONFIG.get("ADMIN_USERNAME", "@admin")
            if admin_id:
                try:
                    await self.app.bot.send_message(chat_id=admin_id, text=f"[DB/UX ERROR] User: {update.effective_user.id}\nAction: grades\nError: {e}")
                except Exception:
                    pass
            is_registered = self.user_storage.is_user_registered(update.effective_user.id)
            keyboard = get_main_keyboard() if is_registered else get_unregistered_keyboard()
            await update.message.reply_text(f"❌ حدث خطأ أثناء جلب الدرجات. إذا استمرت المشكلة، لا تتردد في التواصل مع المطور {admin_username}.", reply_markup=keyboard)

    async def _old_grades_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            context.user_data['last_action'] = 'old_grades'
            telegram_id = update.effective_user.id
            user = self.user_storage.get_user(telegram_id)
            if not user:
                await update.message.reply_text("❗️ يجب التسجيل أولاً.", reply_markup=get_unregistered_keyboard())
                return
            token = user.get("session_token")
            if not token:
                await update.message.reply_text("❗️ يجب إعادة تسجيل الدخول.", reply_markup=get_unregistered_keyboard())
                return
            
            # Test token validity first
            logger.info(f"🔍 Testing token validity for user {telegram_id} (old grades)")
            if not await self.university_api.test_token(token):
                logger.warning(f"❌ Invalid token for user {telegram_id}")
                
                # Token is invalid, force logout
                logger.warning(f"❌ Invalid token for user {user.get('username', 'Unknown')}, forcing logout")
                await self._force_logout_user(telegram_id, update)
                return
            
            old_grades = await self.university_api.get_old_grades(token)
            if old_grades is None:
                logger.warning(f"❌ API error for user {telegram_id} (old grades), forcing logout")
                await self._force_logout_user(telegram_id, update)
                return
            if not old_grades:
                await update.message.reply_text("📚 لا توجد درجات سابقة متاحة للفصل الدراسي السابق.", reply_markup=get_main_keyboard())
                return
            formatted_message = await self.grade_analytics.format_old_grades_with_analysis(telegram_id, old_grades)
            # Split long messages if needed
            if len(formatted_message) > 4096:
                # Send message in chunks if too long
                for i in range(0, len(formatted_message), 4096):
                    await update.message.reply_text(formatted_message[i:i+4096], reply_markup=get_main_keyboard())
            else:
                await update.message.reply_text(formatted_message, reply_markup=get_main_keyboard())
        except Exception as e:
            logger.error(f"[ALERT] Error in _old_grades_command: {e}", exc_info=True)
            admin_id = CONFIG.get("ADMIN_ID")
            admin_username = CONFIG.get("ADMIN_USERNAME", "@admin")
            if admin_id:
                try:
                    await self.app.bot.send_message(chat_id=admin_id, text=f"[DB/UX ERROR] User: {update.effective_user.id}\nAction: old_grades\nError: {e}")
                except Exception:
                    pass
            context.user_data.pop('last_action', None)
            is_registered = self.user_storage.is_user_registered(update.effective_user.id)
            keyboard = get_main_keyboard() if is_registered else get_unregistered_keyboard()
            await update.message.reply_text(f"❌ حدث خطأ غير متوقع أثناء جلب الدرجات السابقة. إذا استمرت المشكلة، لا تتردد في التواصل مع المطور {admin_username}.", reply_markup=keyboard)

    async def _profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            telegram_id = update.effective_user.id
            user = self.user_storage.get_user(telegram_id)
            if not user:
                await update.message.reply_text("❗️ يجب التسجيل أولاً.", reply_markup=get_unregistered_keyboard())
                return
            msg = (
                f"👤 **معلوماتك الجامعية:**\n"
                f"• الاسم الكامل: {user.get('fullname', '-')}\n"
                f"• اسم المستخدم الجامعي: {user.get('username', '-')}\n"
            )
            try:
                await update.message.reply_text(msg, reply_markup=get_main_keyboard())
            except Exception as e:
                logger.error(f"Error sending profile message: {e}")
                await update.message.reply_text(msg, reply_markup=get_main_keyboard())
        except Exception as e:
            await update.message.reply_text("حدث خطأ أثناء جلب المعلومات.", reply_markup=get_unregistered_keyboard())
            logger.error(f"Error in _profile_command: {e}", exc_info=True)

    async def _settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "⚙️ إعدادات الحساب\n\n"
            "يمكنك التحكم في بياناتك والوصول إلى خيارات الخصوصية.\n"
            "كل شيء في هذا البوت شفاف ويمكنك دائماً معرفة كيف يتم التعامل مع بياناتك.\n\n"
            "- يمكنك زيارة الكود البرمجي على GitHub.",
            reply_markup=get_session_settings_keyboard()
        )
        return ASK_SETTINGS_MAIN

    def _get_contact_support_keyboard(self):
        """Returns an inline keyboard with a Contact Support button."""
        admin_username = CONFIG.get("ADMIN_USERNAME", "@admin")
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("📞 تواصل مع الدعم الفني", url=f"https://t.me/{admin_username.lstrip('@')}")]
        ])

    async def _support_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            admin_username = CONFIG.get("ADMIN_USERNAME", "@admin")
            await update.message.reply_text(
                f"📞 للدعم الفني: {admin_username}\nاضغط الزر أدناه للتواصل مباشرة.",
                reply_markup=self._get_contact_support_keyboard()
            )
        except Exception as e:
            await update.message.reply_text("عذراً، حدث خطأ أثناء عرض الدعم.", reply_markup=get_main_keyboard())
            logger.error(f"Error in _support_command: {e}", exc_info=True)

    async def _admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Show admin dashboard for admin users
        if update.effective_user.id == CONFIG["ADMIN_ID"]:
            await self.admin_dashboard.show_dashboard(update, context)
        else:
            await update.message.reply_text("🚫 ليس لديك صلاحية لهذه العملية.", reply_markup=get_main_keyboard())

    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        user_id = update.effective_user.id
        is_registered = self.user_storage.is_user_registered(user_id)
        if text == "❌ إلغاء":
            keyboard = get_main_keyboard() if is_registered else get_unregistered_keyboard()
            await update.message.reply_text(
                "✅ تم إلغاء العملية. يمكنك البدء من جديد أو اختيار إجراء آخر.",
                reply_markup=keyboard
            )
            context.user_data.clear()
            return
        try:
            # Admin: user search
            if user_id == CONFIG["ADMIN_ID"] and context.user_data.get('awaiting_user_search'):
                handled = await self.admin_dashboard.handle_user_search_message(update, context)
                if handled:
                    context.user_data.pop('awaiting_user_search', None)
                    return
            # Admin: user delete
            if user_id == CONFIG["ADMIN_ID"] and context.user_data.get('awaiting_user_delete'):
                handled = await self.admin_dashboard.handle_user_delete_message(update, context)
                if handled:
                    context.user_data.pop('awaiting_user_delete', None)
                    return
            # Admin: broadcast
            if user_id == CONFIG["ADMIN_ID"] and context.user_data.get('awaiting_broadcast'):
                handled = await self.admin_dashboard.handle_dashboard_message(update, context)
                if handled:
                    context.user_data.pop('awaiting_broadcast', None)
                    return
            # Admin: force grade check
            if context.user_data.get("awaiting_force_grade_check"):
                handled = await self.admin_dashboard.handle_force_grade_check_message(update, context)
                if handled:
                    return
            # Handle error recovery buttons
            # If the user presses a session type button outside registration, show the welcome message and keyboard
            if text in [
                "🔒 جلسة مؤقتة (لا يتم تخزين كلمة المرور)",
                "🔑 جلسة دائمة (تخزين كلمة المرور مشفر)"
            ]:
                user = self.user_storage.get_user(user_id)
                if user:
                    from utils.messages import get_welcome_message
                    welcome_message = get_welcome_message(user.get('fullname'))
                    await update.message.reply_text(welcome_message, reply_markup=get_main_keyboard())
                else:
                    from utils.messages import get_simple_welcome_message
                    await update.message.reply_text(get_simple_welcome_message(), reply_markup=get_unregistered_keyboard())
                return
            # Map button text to actions
            actions = {
                # Grade actions
                "📊 درجات الفصل الحالي": self._grades_command,
                "📚 درجات الفصل السابق": self._old_grades_command,
                # User actions
                "👤 معلوماتي الشخصية": self._profile_command,
                "⚙️ الإعدادات والتخصيص": self._settings_command,
                # Support/help
                "📞 الدعم الفني": self._support_command,
                "❓ المساعدة والدليل": self._help_command,
                # Registration
                "🚀 تسجيل الدخول للجامعة": self._register_start,
                # Admin
                "🎛️ لوحة التحكم الإدارية": self._admin_command,
                "🔙 العودة للوحة الرئيسية": self._return_to_main,
                # Legacy button support
                "📊 التحقق من درجات الفصل الحالي": self._grades_command,
                "📚 التحقق من درجات الفصل السابق": self._old_grades_command,
                "👤 معلوماتي": self._profile_command,
                "⚙️ الإعدادات": self._settings_command,
                "📞 الدعم": self._support_command,
                "❓ المساعدة": self._help_command,
                "🚀 تسجيل الدخول": self._register_start,
                "🎛️ لوحة التحكم": self._admin_command,
                "🔙 العودة": self._return_to_main,
                # Info about bot
                "❓ كيف يعمل البوت؟": self._how_it_works_command,
                # Logout
                "🚪 تسجيل الخروج": self._logout_command,
                # Refresh keyboard
                "🔄 تحديث الأزرار": self._refresh_keyboard,
                "🧮 حساب المعدل المخصص": self._gpa_calc_start,
                "📅 جميع الفصول": self._older_terms_command,
                "📥 تحميل معلوماتي": self._download_my_info_command,
            }
            action = actions.get(text)
            if action:
                await action(update, context)
                return
            else:
                is_registered = self.user_storage.is_user_registered(user_id)
                keyboard = get_main_keyboard() if is_registered else get_unregistered_keyboard()
                await update.message.reply_text(
                    "هذه الميزة قيد التطوير. سيتم توفيرها قريباً.\n\n📞 للمساعدة: اضغط '📞 الدعم الفني' أو الزر أدناه.",
                    reply_markup=keyboard
                )
        except Exception as e:
            logger.error(f"[ALERT] Error in _handle_message: {e}", exc_info=True)
            admin_id = CONFIG.get("ADMIN_ID")
            admin_username = CONFIG.get("ADMIN_USERNAME", "@admin")
            if admin_id:
                try:
                    await self.app.bot.send_message(chat_id=admin_id, text=f"[UX ERROR] User: {user_id}\nAction: {text}\nError: {e}")
                except Exception:
                    pass
            context.user_data.clear()
            is_registered = self.user_storage.is_user_registered(user_id)
            keyboard = get_main_keyboard() if is_registered else get_unregistered_keyboard()
            await update.message.reply_text(
                f"❌ حدث خطأ غير متوقع\n\n**الحلول:**\n• جرب مرة أخرى بعد قليل\n• إذا استمرت المشكلة، لا تتردد في التواصل مع المطور {admin_username}\n• تأكد من اتصالك بالإنترنت\n\n📞 للمساعدة: اضغط '📞 الدعم الفني' أو الزر أدناه.",
                reply_markup=keyboard
            )

    async def _handle_error_recovery(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle error recovery actions from the error recovery keyboard."""
        text = update.message.text
        user_id = update.effective_user.id
        
        if text == "🔄 إعادة المحاولة":
            # Retry last action if possible
            last_action = context.user_data.get('last_action')
            if last_action:
                try:
                    if last_action == "grades":
                        await self._grades_command(update, context)
                    elif last_action == "old_grades":
                        await self._old_grades_command(update, context)
                    elif last_action == "profile":
                        await self._profile_command(update, context)
                    elif last_action == "settings":
                        await self._settings_command(update, context)
                    else:
                        await self._start_command(update, context)
                except Exception as e:
                    logger.error(f"Error in retry action: {e}")
                    await update.message.reply_text(
                        "❌ فشلت إعادة المحاولة. يرجى المحاولة مرة أخرى لاحقاً.",
                        reply_markup=get_error_recovery_keyboard()
                    )
            else:
                await self._start_command(update, context)
        
        elif text == "🏠 العودة للرئيسية":
            await self._start_command(update, context)
        
        elif text == "📞 الدعم":
            await self._support_command(update, context)
        
        elif text == "❓ المساعدة":
            await self._help_command(update, context)

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        # Handle admin callbacks
        if update.effective_user.id == CONFIG["ADMIN_ID"]:
            await self.admin_dashboard.handle_callback(update, context)
            return
            
        # Handle regular user callbacks
        user_id = update.effective_user.id
        user = self.user_storage.get_user_by_telegram_id(user_id)
        
        if query.data == "delete_user_data":
            if not user:
                await query.edit_message_text("❗️ يجب التسجيل أولاً.")
                return
            # Show confirmation for data deletion
            await query.edit_message_text(
                "🗑️ **حذف البيانات الشخصية**\n\n"
                "⚠️ **تحذير**: هذا الإجراء سيحذف:\n"
                "• جميع بياناتك المخزنة\n"
                "• كلمة المرور المشفرة\n"
                "• إعداداتك الشخصية\n"
                "• سجل الدرجات\n\n"
                "❌ **لا يمكن التراجع عن هذا الإجراء**\n\n"
                "هل أنت متأكد من حذف جميع بياناتك؟",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ نعم، احذف جميع بياناتي", callback_data="confirm_delete_data")],
                    [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_delete_data")]
                ])
            )
            return
            
        elif query.data == "confirm_delete_data":
            if not user:
                await query.edit_message_text("❗️ يجب التسجيل أولاً.")
                return
            # Delete user data
            try:
                # Delete user from storage
                self.user_storage.delete_user(user["username"])
                # Delete grades
                self.grade_storage.delete_user_grades(user["username"])
                await query.edit_message_text(
                    "✅ تم حذف جميع بياناتك بنجاح.\n\n"
                    "تم تسجيل خروجك تلقائياً. يمكنك التسجيل مرة أخرى إذا أردت.",
                    reply_markup=get_unregistered_keyboard()
                )
            except Exception as e:
                await query.edit_message_text(
                    f"❌ حدث خطأ أثناء حذف البيانات: {str(e)}\n\n"
                    "يرجى المحاولة مرة أخرى أو التواصل مع الدعم الفني."
                )
            return
            
        elif query.data == "cancel_delete_data":
            # Return to privacy settings
            await query.edit_message_text(
                "تم إلغاء حذف البيانات.",
                reply_markup=get_privacy_settings_keyboard()
            )
            return
        
        elif query.data == "back_to_settings":
            # Return to main settings
            from utils.keyboards import get_settings_main_keyboard
            keyboard = get_settings_main_keyboard(translation_enabled=user.get("do_trans", False) if user else False)
            await query.edit_message_text(
                "تمت العودة إلى الإعدادات الرئيسية.",
                reply_markup=keyboard
            )
            return
            
        # Delegate other callbacks to settings handler
        await self._settings_callback_handler(update, context)

    async def _admin_notify_grades(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != CONFIG["ADMIN_ID"]:
            await update.message.reply_text("🚫 ليس لديك صلاحية لهذه العملية.", reply_markup=get_main_keyboard())
            return
        await update.message.reply_text("🔄 جاري فحص الدرجات لجميع المستخدمين...")
        count = await self._notify_all_users_grades()
        await update.message.reply_text(f"✅ تم فحص الدرجات وإشعار {count} مستخدم (إذا كان هناك تغيير).", reply_markup=get_main_keyboard())

    async def _grade_checking_loop(self):
        logger.info("🚦 Entered _grade_checking_loop (unconditional)")
        try:
            await asyncio.sleep(10)
            logger.info("🚦 Slept 10 seconds, entering infinite loop")
            while True:
                logger.info("🔔 Running scheduled grade check for all users (unconditional)...")
                await self._notify_all_users_grades()
                interval = int(CONFIG.get('GRADE_CHECK_INTERVAL', 10)) * 60
                logger.info(f"🚦 Sleeping for {interval} seconds before next check (unconditional)")
                await asyncio.sleep(interval)
        except Exception as e:
            logger.error(f"❌ Exception in _grade_checking_loop: {e}", exc_info=True)

    async def _notify_all_users_grades(self):
        users = self.user_storage.get_all_users()
        logger.info(f"🔍 Force grade check: Found {len(users)} users in database")
        
        if not users:
            logger.warning("⚠️ No users found in database for grade check")
            return 0
            
        notified_count = 0
        semaphore = asyncio.Semaphore(CONFIG.get('MAX_CONCURRENT_REQUESTS', 5))
        tasks = []
        results = []

        async def check_user(user):
            async with semaphore:
                try:
                    logger.debug(f"🔍 Checking grades for user: {user.get('username', 'Unknown')} (ID: {user.get('telegram_id', 'Unknown')})")
                    return await self._check_and_notify_user_grades(user)
                except Exception as e:
                    logger.error(f"❌ Error in parallel grade check for user {user.get('username', 'Unknown')}: {e}", exc_info=True)
                    return False

        for user in users:
            tasks.append(asyncio.create_task(check_user(user)))
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            notified_count = sum(1 for r in results if r is True)
        
        logger.info(f"📊 Force grade check completed: {notified_count}/{len(users)} users notified")
        return notified_count

    async def _check_and_notify_user_grades(self, user):
        try:
            telegram_id = user.get("telegram_id")
            username = user.get("username")
            username_unique = user.get("username_unique")
            # Always use a valid username for grade storage
            storage_username = username_unique or username
            if not storage_username:
                logger.error(f"[ALERT] Cannot store grades: missing username for user with telegram_id={telegram_id}")
                return False
            token = user.get("session_token")
            logger.info(f"[CALL] _check_and_notify_user_grades for username={username}, username_unique={username_unique}, telegram_id={telegram_id}")
            logger.info(f"[CHECK] self.grade_storage is type: {type(self.grade_storage)}")
            lock = self._get_user_lock(username_unique)
            # --- Fix: Always initialize notified and is_pg ---
            notified = user.get("session_expired_notified", False)
            is_pg = hasattr(self.user_storage, 'update_token_expired_notified')
            async with lock:
                # Notify only once if token expired
                if not token:
                    logger.debug(f"❌ No token for user {username}")
                    notified = user.get("session_expired_notified", False)
                    if not notified:
                        await self.app.bot.send_message(
                            chat_id=telegram_id,
                            text="⏰ انتهت صلاحية الجلسة\n\nتم تسجيل الخروج تلقائياً لحماية حسابك. يرجى تسجيل الدخول مرة أخرى من خلال زر '🚀 تسجيل الدخول للجامعة'.",
                            reply_markup=get_unregistered_keyboard()
                        )
                        is_pg = hasattr(self.user_storage, 'update_token_expired_notified')
                        if is_pg:
                            self.user_storage.update_token_expired_notified(user["username"], True)
                        else:
                            user["session_expired_notified"] = True
                            if hasattr(self.user_storage, '_save_users'):
                                self.user_storage._save_users()
                    return False
                # Test token validity
                if not await self.university_api.test_token(token):
                    logger.warning(f"❌ Token expired for user {username}")
                    # Try auto-login if password is stored
                    if user.get("password_stored") and user.get("encrypted_password"):
                        try:
                            from utils.crypto import decrypt_password
                            decrypted_password = decrypt_password(user["encrypted_password"])
                            new_token = await self.university_api.login(user["username"], decrypted_password)
                            if new_token:
                                logger.info(f"🔑 Auto-login successful for user {username}, updating token.")
                                # Update token in storage
                                user["token"] = new_token
                                self.user_storage.save_user(
                                    telegram_id,
                                    user["username"],
                                    new_token,
                                    user,
                                    encrypted_password=user["encrypted_password"],
                                    password_stored=True,
                                    password_consent_given=user.get("password_consent_given", True)
                                )
                                # Retry grade check with new token
                                token = new_token

                            else:
                                logger.warning(f"❌ Auto-login failed for user {username}")
                                return False
                        except Exception as e:
                            logger.warning(f"❌ Auto-login failed for user {username}")
                            return False
                    else:
                        # Token is invalid, notify user to login manually
                        if not notified:
                            await self.app.bot.send_message(
                                chat_id=telegram_id,
                                text="⏰ انتهت صلاحية الجلسة\n\nيرجى تسجيل الدخول مرة أخرى من خلال زر '🚀 تسجيل الدخول للجامعة' ثم إدخال بياناتك من جديد. هذا طبيعي ويحدث كل فترة.",
                                reply_markup=get_unregistered_keyboard()
                            )
                            if is_pg:
                                self.user_storage.update_token_expired_notified(user["username"], True)
                            else:
                                user["session_expired_notified"] = True
                                if hasattr(self.user_storage, '_save_users'):
                                    self.user_storage._save_users()
                        return False
                logger.debug(f"✅ Token valid for user {username}")
                # Reset notification flag if token is valid
                if notified:
                    if is_pg:
                        self.user_storage.update_token_expired_notified(user["username"], False)
                    else:
                        # Update file storage
                        user["session_expired_notified"] = False
                        if hasattr(self.user_storage, '_save_users'):
                            self.user_storage._save_users()
                logger.debug(f"🔍 Fetching user data for {username}")
                user_data = await self.university_api.get_user_data(token)
                if not user_data or "grades" not in user_data:
                    logger.info(f"No grade data available for {username} in this check.")
                    return False
                new_grades = user_data.get("grades", [])
                logger.debug(f"📊 Found {len(new_grades)} new grades for user {username}")
                # Use storage_username for grade storage
                old_grades = []
                try:
                    old_grades = self.grade_storage.get_user_grades(storage_username)
                except Exception as db_exc:
                    logger.error(f"[ALERT] Persistent DB error for user {storage_username}: {db_exc}")
                    # Alert admin
                    admin_id = CONFIG.get("ADMIN_ID")
                    if admin_id:
                        try:
                            await self.app.bot.send_message(chat_id=admin_id, text=f"[DB ERROR] Persistent DB error for user {storage_username}: {db_exc}")
                        except Exception:
                            pass
                    return False
                logger.debug(f"📊 Found {len(old_grades) if old_grades else 0} stored grades for user {storage_username}")
                
                # Get user's grade notification sensitivity setting
                user_settings = self.user_settings.get_user_settings(telegram_id)
                sensitivity = user_settings.get("notifications", {}).get("grade_sensitivity", "meaningful")
                logger.debug(f"🔍 User {username_unique} grade sensitivity setting: {sensitivity}")
                
                changed_courses = self._compare_grades(old_grades, new_grades, sensitivity)
                logger.debug(f"🔍 Grade comparison for {storage_username}: {len(changed_courses)} {sensitivity} changes detected")
                # Always save the grades, regardless of notification
                self.grade_storage.store_grades(storage_username, new_grades)
                if not changed_courses:
                    logger.debug(f"✅ No {sensitivity} grade changes for user {storage_username}, not sending notification.")
                    return False
                
                # Create appropriate message based on sensitivity
                if sensitivity == "all":
                    message = f"🎓 تم تحديث درجاتك في المواد التالية:\n\n"
                elif sensitivity == "significant":
                    message = f"🎓 تم تحديث درجاتك بشكل كبير في المواد التالية:\n\n"
                else:  # meaningful
                    message = f"🎓 تم تحديث درجاتك في المواد التالية:\n\n"
                old_map = {g.get('code') or g.get('name'): g for g in old_grades if g.get('code') or g.get('name')}
                
                for grade in changed_courses:
                    name = grade.get('name', 'N/A')
                    code = grade.get('code', '-')
                    key = code if code != '-' else name
                    old = old_map.get(key, {})

                    def show_change(field, label):
                        old_val = old.get(field, '—')
                        new_val = grade.get(field, '—')
                        # Always show old and new, even if old was missing or 'لم يتم النشر'
                        return f"{label}: {old_val} → {new_val}" if old_val != new_val else None

                    changes = [
                        show_change('coursework', 'الأعمال'),
                        show_change('final_exam', 'النظري'),
                        show_change('total', 'النهائي'),
                    ]
                    changes = [c for c in changes if c]

                    if changes:
                        message += f"📚 {name} ({code})\n" + "\n".join(changes) + "\n\n"
                
                # If we reach here, we have meaningful changes to report
                now_utc3 = datetime.now(timezone.utc) + timedelta(hours=3)
                message += f"🕒 وقت التحديث: {now_utc3.strftime('%Y-%m-%d %H:%M')} (UTC+3)"
                await self.app.bot.send_message(chat_id=telegram_id, text=message)
                logger.info(f"✅ Sent grade change notification to user {username_unique}")
                return True
        except Exception as e:
            logger.error(f"❌ Error in _check_and_notify_user_grades for user {user.get('username', 'Unknown')}: {e}", exc_info=True)
            return False

    def _compare_grades(self, old_grades: List[Dict], new_grades: List[Dict], sensitivity: str = "meaningful") -> List[Dict]:
        """
        Return only courses where important fields (total, coursework, final_exam) changed based on sensitivity level.
        
        Sensitivity levels:
        - "all": Notify about any change, including new courses and "لم يتم النشر" changes
        - "meaningful": Only notify about actual grade changes (default)
        - "significant": Only notify about significant grade changes (e.g., letter grade changes)
        """
        def extract_relevant(grade):
            return {
                'code': grade.get('code') or grade.get('name'),
                'total': grade.get('total'),
                'coursework': grade.get('coursework'),
                'final_exam': grade.get('final_exam'),
            }
        
        def is_meaningful_grade(value):
            """Check if a grade value is meaningful (not empty, None, or 'لم يتم النشر')"""
            if not value or value == 'لم يتم النشر' or value == '—' or value == '-':
                return False
            return True
        
        def has_meaningful_change(old_val, new_val):
            """Check if there's a meaningful change between two grade values"""
            old_meaningful = is_meaningful_grade(old_val)
            new_meaningful = is_meaningful_grade(new_val)
            
            # If both are not meaningful, no change
            if not old_meaningful and not new_meaningful:
                return False
            
            # If one is meaningful and the other isn't, that's a change
            if old_meaningful != new_meaningful:
                return True
            
            # If both are meaningful, check if they're different
            if old_meaningful and new_meaningful:
                return old_val != new_val
            
            return False
        
        def has_significant_change(old_val, new_val):
            """Check if there's a significant change between two grade values (e.g., letter grade changes)"""
            if not is_meaningful_grade(old_val) or not is_meaningful_grade(new_val):
                return False
            
            # Try to extract numeric values for comparison
            try:
                old_num = float(old_val) if old_val.replace('.', '').replace('-', '').isdigit() else None
                new_num = float(new_val) if new_val.replace('.', '').replace('-', '').isdigit() else None
                
                if old_num is not None and new_num is not None:
                    # Consider significant if difference is >= 5 points
                    return abs(new_num - old_num) >= 5
                else:
                    # For letter grades, any change is significant
                    return old_val != new_val
            except:
                # If we can't parse as numbers, treat as letter grades
                return old_val != new_val
        
        old_map = {g.get('code') or g.get('name'): extract_relevant(g) for g in old_grades if g.get('code') or g.get('name')}
        changed = []
        
        for new_grade in new_grades:
            key = new_grade.get('code') or new_grade.get('name')
            if not key:
                continue
                
            relevant_new = extract_relevant(new_grade)
            relevant_old = old_map.get(key)
            
            # Handle new courses based on sensitivity
            if relevant_old is None:
                if sensitivity == "all":
                    logger.debug(f"📝 New course '{key}' found, including in changes (sensitivity: all)")
                    changed.append(new_grade)
                else:
                    logger.debug(f"📝 New course '{key}' found, skipping notification (sensitivity: {sensitivity})")
                continue
            
            # Choose comparison function based on sensitivity
            if sensitivity == "all":
                def compare_func(old_val, new_val):
                    return old_val != new_val
            elif sensitivity == "significant":
                compare_func = has_significant_change
            else:  # "meaningful" (default)
                compare_func = has_meaningful_change
            
            # Check for changes in any of the important fields
            total_changed = compare_func(relevant_old.get('total'), relevant_new.get('total'))
            coursework_changed = compare_func(relevant_old.get('coursework'), relevant_new.get('coursework'))
            final_exam_changed = compare_func(relevant_old.get('final_exam'), relevant_new.get('final_exam'))
            
            has_changes = total_changed or coursework_changed or final_exam_changed
            
            if has_changes:
                logger.debug(f"📊 {sensitivity.capitalize()} change detected for course '{key}': total={total_changed}, coursework={coursework_changed}, final_exam={final_exam_changed}")
                changed.append(new_grade)
            else:
                logger.debug(f"✅ No {sensitivity} changes for course '{key}'")
        
        return changed

    async def _register_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        # Rate limiting
        if not security_manager.check_login_attempt(user_id):
            await update.message.reply_text(
                "🚫 تم حظر محاولات تسجيل الدخول مؤقتاً بسبب كثرة المحاولات الفاشلة.\n"
                "يرجى المحاولة مرة أخرى بعد 15 دقيقة.",
                reply_markup=get_unregistered_keyboard()
            )
            return ConversationHandler.END
        
        # Clear previous session and user data
        existing_user = self.user_storage.get_user(user_id)
        if existing_user:
            logger.info(f"User {user_id} is relogging in. Clearing existing session.")
            # Invalidate session
            if hasattr(security_manager, 'session_manager'):
                security_manager.session_manager.invalidate_session(user_id)
            # Clear user data from context
            context.user_data.clear()
            # Remove user token
            if hasattr(self.user_storage, 'clear_user_token'):
                # For PostgreSQL storage
                self.user_storage.clear_user_token(user_id)
            else:
                # For file storage
                existing_user["token"] = None
                existing_user["token_expired_notified"] = False
                if hasattr(self.user_storage, '_save_users'):
                    self.user_storage._save_users()
        
        # Show security info before asking for credentials
        await update.message.reply_text(get_credentials_security_info_message())
        
        await update.message.reply_text(
            "يرجى إدخال الكود الجامعي الخاص بك. إذا احتجت للمساعدة، اضغط على '❓ المساعدة'."
        )
        return ASK_USERNAME

    async def _register_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = update.message.text.strip()
        
        # Validate username length
        if not is_valid_length(username, min_len=7, max_len=20):
            await update.message.reply_text(
                "❌ الكود الجامعي يجب أن يكون بين 7 و 20 حرف.\n\n"
                "❌ University code must be between 7 and 20 characters."
            )
            return ASK_USERNAME
        
        # Validate university code format
        if not re.fullmatch(r"[A-Za-z]{3,}[0-9]{4,}", username):
            await update.message.reply_text(
                "❌ الكود الجامعي يجب أن يكون على الشكل: 3 أحرف أو أكثر ثم 4 أرقام أو أكثر (مثال: ENG2425041).\n\n"
                "❌ University code must be in the form: 3+ letters then 4+ digits (e.g., ENG2425041)."
            )
            return ASK_USERNAME
        
        context.user_data['username'] = username
        await update.message.reply_text("يرجى إدخال كلمة المرور:")
        await update.message.reply_text(
            "🔒 ملاحظة: كلمة المرور لا تُخزن نهائياً وتُستخدم فقط لتسجيل الدخول. بياناتك آمنة بالكامل.\n"
            "نستخدم رمز دخول مؤقت (Token) بدلاً من كلمة المرور لحماية حسابك.\n"
            "_Note: Your password is never stored and is used only for login. Your data is fully secure._\n"
            "We use a temporary login token instead of your password to keep your account safe."
        )
        return ASK_PASSWORD

    async def _register_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = context.user_data.get('username')
        password = update.message.text.strip()
        telegram_id = update.effective_user.id
        # Make sure username is set
        if not username:
            await update.message.reply_text(
                "❌ حدث خطأ في البيانات. يرجى المحاولة مرة أخرى.",
                reply_markup=get_unregistered_keyboard()
            )
            return ConversationHandler.END
        # Validate password
        if not is_valid_length(password, min_len=1, max_len=100):
            await update.message.reply_text(
                "❌ كلمة المرور غير صحيحة.\n\n"
                "❌ Invalid password format."
            )
            return ASK_PASSWORD
        # Check for invalid password characters
        if any(char in password for char in ['<', '>', '"', "'", '&', ';', '|', '`', '$', '(', ')', '{', '}']):
            await update.message.reply_text(
                "❌ كلمة المرور تحتوي على رموز غير مسموحة.\n\n"
                "❌ Password contains invalid characters."
            )
            return ASK_PASSWORD
        # Store password in context for later use
        context.user_data['password'] = password
        # Prompt for session type with detailed explanation
        session_keyboard = ReplyKeyboardMarkup([
            ["🔒 جلسة مؤقتة (لا يتم تخزين كلمة المرور)", "🔑 جلسة دائمة (تخزين كلمة المرور مشفر)"]
        ], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(
            "🔐 **خيارات الجلسة**\n\n"
            "يمكنك اختيار نوع الجلسة التي تناسبك بعد تسجيل الدخول:\n\n"
            "1️⃣ **جلسة مؤقتة**\n"
            "- ستتوقف إشعارات الدرجات الجديدة بعد فترة زمنية قصيرة.\n"
            "- كلمة المرور لن يتم تخزينها أبداً بعد تسجيل الدخول.\n"
            "- عند انتهاء الجلسة أو انتهاء صلاحية رمز الدخول، ستحتاج لإعادة إدخال كلمة المرور يدويًا لتسجيل الدخول مرة أخرى.\n"
            "- سيقوم النظام الجامعي بتسجيل خروجك خﻻل بضعة أيام ولن تستمر بتلقي إشعارات الدرجات "
            "2️⃣ **جلسة دائمة**\n"
            "- سيرسل البوت إشعارات الدرجات الجديدة بشكل مستمر ودائم.\n"
            "- سيتم تخزين كلمة المرور بشكل مشفر وآمن (لا يمكن لأي شخص الاطلاع عليها).\n"
            "- عند انتهاء الجلسة أو انتهاء صلاحية رمز الدخول، سيقوم البوت بتسجيل الدخول تلقائيًا دون الحاجة لإعادة إدخال كلمة المرور.\n"
            "- هذا الخيار مناسب إذا كنت تريد سهولة الاستخدام وعدم الحاجة لإدخال كلمة المرور كل مرة.\n\n"
            "\nيرجى اختيار أحد الخيارات من الأزرار أدناه:",
            reply_markup=session_keyboard
        )
        return ASK_SESSION_TYPE

    async def _register_session_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text.strip()
        if "مؤقتة" in text:
            # Temporary session: do not store password
            context.user_data['session_type'] = 'temporary'
            context.user_data['password_stored'] = False
            context.user_data['password_consent_given'] = False
            return await self._register_login_and_fetch_info(update, context)
        elif "دائمة" in text:
            # Permanent session: ask for password confirmation
            context.user_data['session_type'] = 'permanent'
            await update.message.reply_text(
                "يرجى إدخال كلمة المرور مرة أخرى للتأكيد (لن يتم عرضها لأي شخص):",
                reply_markup=ReplyKeyboardMarkup([["❌ إلغاء"]], resize_keyboard=True, one_time_keyboard=True)
            )
            context.user_data['password_confirm_attempts'] = 0
            return ASK_PASSWORD_CONFIRM
        else:
            await update.message.reply_text(
                "❌ يرجى اختيار أحد الخيارات من الأزرار فقط.",
                reply_markup=ReplyKeyboardMarkup([
                    ["🔒 جلسة مؤقتة (لا يتم تخزين كلمة المرور)", "🔑 جلسة دائمة (تخزين كلمة المرور مشفر)"]
                ], resize_keyboard=True, one_time_keyboard=True)
            )
            return ASK_SESSION_TYPE

    async def _register_password_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        password = context.user_data.get('password')
        confirm = update.message.text.strip()
        attempts = context.user_data.get('password_confirm_attempts', 0) + 1
        context.user_data['password_confirm_attempts'] = attempts
        if confirm != password:
            if attempts >= 3:
                await update.message.reply_text(
                    "❌ تم إدخال كلمة مرور خاطئة 3 مرات. سيتم التحويل إلى جلسة مؤقتة.",
                    reply_markup=ReplyKeyboardMarkup([
                        ["🔒 جلسة مؤقتة (لا يتم تخزين كلمة المرور)"]
                    ], resize_keyboard=True, one_time_keyboard=True)
                )
                context.user_data['session_type'] = 'temporary'
                context.user_data['password_stored'] = False
                context.user_data['password_consent_given'] = False
                return await self._register_login_and_fetch_info(update, context)
            else:
                await update.message.reply_text(
                    f"❌ كلمة المرور غير متطابقة. حاول مرة أخرى. (محاولة {attempts}/3)",
                    reply_markup=ReplyKeyboardMarkup([["❌ إلغاء"]], resize_keyboard=True, one_time_keyboard=True)
                )
                return ASK_PASSWORD_CONFIRM
        # Passwords match, proceed
        context.user_data['password_stored'] = True
        context.user_data['password_consent_given'] = True
        return await self._register_login_and_fetch_info(update, context)

    async def _register_login_and_fetch_info(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = context.user_data.get('username')
        password = context.user_data.get('password')
        session_type = context.user_data.get('session_type', 'temporary')
        telegram_id = update.effective_user.id
        # Try to log in with university API
        await update.message.reply_text("🔄 جاري التحقق من بياناتك...\nChecking your credentials...")
        token = await self.university_api.login(username, password)
        # Record login attempt
        success = token is not None
        security_manager.record_login_attempt(telegram_id, success, username)
        if not token:
            await update.message.reply_text(
                "❌ تعذّر تسجيل الدخول. يرجى التأكد من صحة اسم المستخدم وكلمة المرور الجامعية وإعادة المحاولة.\n\nLogin failed. Please check your university username and password and try again.",
                reply_markup=get_unregistered_keyboard()
            )
            return await self._register_start(update, context)
        # Get user info for welcome message
        user_info = await self.university_api.get_user_info(token)
        if user_info:
            api_fullname = user_info.get('fullname', '')
            api_firstname = user_info.get('firstname', '')
            api_lastname = user_info.get('lastname', '')
            api_username = user_info.get('username', username)
            email = user_info.get('email', '-')
            if api_fullname and api_fullname.strip():
                fullname = api_fullname.strip()
                if api_firstname and api_firstname.strip():
                    firstname = api_firstname.strip()
                    lastname = api_lastname.strip() if api_lastname else ''
                else:
                    name_parts = fullname.split()
                    if len(name_parts) >= 2:
                        firstname = name_parts[0]
                        lastname = ' '.join(name_parts[1:])
                    else:
                        firstname = fullname
                        lastname = ''
            else:
                fullname = f"طالب جامعة الشام ({api_username})"
                firstname = "طالب"
                lastname = "جامعة الشام"
        else:
            fullname = f"طالب جامعة الشام ({username})"
            firstname = "طالب"
            lastname = "جامعة الشام"
            email = '-'
        context.user_data['user_data'] = {
            "username": username,
            "fullname": fullname,
            "firstname": firstname,
            "lastname": lastname,
            "email": email
        }
        context.user_data['token'] = token
        return await self._complete_registration(update, context)

    async def _complete_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        user_data = context.user_data.get('user_data')
        token = context.user_data.get('token')
        password = context.user_data.get('password')
        password_stored = context.user_data.get('password_stored', False)
        password_consent_given = context.user_data.get('password_consent_given', False)
        session_type = context.user_data.get('session_type', 'temporary')
        if not user_data or not token:
            await update.message.reply_text(
                "❌ حدث خطأ في البيانات. يرجى المحاولة مرة أخرى.",
                reply_markup=get_unregistered_keyboard()
            )
            return ConversationHandler.END
        # Encrypt password if permanent session
        encrypted_password = None
        if password_stored and password:
            from utils.crypto import encrypt_password
            try:
                encrypted_password = encrypt_password(password)
                logger.info("✅ Password encrypted successfully")
            except Exception as e:
                logger.error(f"❌ Error encrypting password: {e}")
                logger.info("🔄 Continuing with temporary session due to encryption failure")
                await update.message.reply_text(
                    "⚠️ حدث خطأ أثناء تشفير كلمة المرور. سيتم المتابعة بجلسة مؤقتة.",
                    reply_markup=get_unregistered_keyboard()
                )
                password_stored = False
                password_consent_given = False
        # Save user to database
        try:
            user_dict = {
                "telegram_id": telegram_id,
                "username": user_data['username'],
                "fullname": user_data.get('fullname'),
                "firstname": user_data.get('firstname'),
                "lastname": user_data.get('lastname'),
                "email": user_data.get('email'),
                "session_token": token,
                "token_expires_at": None,  # Set if you have it
                "is_active": True,
                # Optionally add encrypted_password, password_stored, password_consent_given if your User model supports them
            }
            success = self.user_storage.create_user(user_dict)
            if not success:
                # User exists, update their info
                self.user_storage.update_user(user_data['username'], {
                    "session_token": token,
                    "token_expires_at": None,
                    "is_active": True,
                    "fullname": user_data.get('fullname'),
                    "firstname": user_data.get('firstname'),
                    "lastname": user_data.get('lastname'),
                    "email": user_data.get('email'),
                    "encrypted_password": encrypted_password,
                    "password_stored": password_stored,
                    "password_consent_given": password_consent_given
                })
                logger.warning(f"User {user_data['username']} already exists, updated session info.")
                welcome_message = get_welcome_message(user_data['fullname'])
                if session_type == 'permanent' and password_stored:
                    welcome_message += "\n\n🔑 **جلسة دائمة**\nكلمة المرور مخزنة بشكل مشفر. سيتم تسجيل الدخول تلقائياً عند انتهاء الجلسة."
                else:
                    welcome_message += "\n\n🔐 **جلسة مؤقتة**\nكلمة المرور لم تُخزن. ستحتاج لتسجيل الدخول مرة أخرى عند انتهاء الجلسة."
                try:
                    await update.message.reply_text(welcome_message, reply_markup=get_main_keyboard())
                except Exception as e:
                    logger.error(f"Error sending welcome message: {e}")
                    await update.message.reply_text(welcome_message)
                return ConversationHandler.END
            logger.info(f"✅ User saved successfully")
        except Exception as e:
            logger.error(f"❌ Error saving user: {e}", exc_info=True)
            await update.message.reply_text(
                "❌ حدث خطأ أثناء حفظ البيانات. يرجى المحاولة مرة أخرى.",
                reply_markup=get_unregistered_keyboard()
            )
            return ConversationHandler.END
        # Create session
        try:
            security_manager.create_user_session(telegram_id, token, user_data)
            logger.info(f"✅ User session created successfully")
        except Exception as e:
            logger.error(f"❌ Error creating user session: {e}", exc_info=True)
        # Show welcome message
        welcome_message = get_welcome_message(user_data['fullname'])
        if session_type == 'permanent' and password_stored:
            welcome_message += "\n\n🔑 **جلسة دائمة**\nكلمة المرور مخزنة بشكل مشفر. سيتم تسجيل الدخول تلقائياً عند انتهاء الجلسة."
        else:
            welcome_message += "\n\n🔐 **جلسة مؤقتة**\nكلمة المرور لم تُخزن. ستحتاج لتسجيل الدخول مرة أخرى عند انتهاء الجلسة."
        try:
            await update.message.reply_text(welcome_message, reply_markup=get_main_keyboard())
        except Exception as e:
            logger.error(f"Error sending welcome message: {e}")
            await update.message.reply_text(welcome_message)
        return ConversationHandler.END

    async def _return_to_main(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Return to main keyboard from admin interface"""
        keyboard_to_show = get_main_keyboard() if self.user_storage.is_user_registered(update.effective_user.id) else get_unregistered_keyboard()
        await update.message.reply_text(
            "تمت العودة إلى القائمة الرئيسية.",
            reply_markup=keyboard_to_show
        )

    async def _cancel_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        is_registered = self.user_storage.is_user_registered(update.effective_user.id)
        keyboard = get_main_keyboard() if is_registered else get_unregistered_keyboard()
        await update.message.reply_text("تم إلغاء التسجيل.", reply_markup=keyboard)
        return ConversationHandler.END

    async def send_quote_to_all_users(self, message):
        users = self.user_storage.get_all_users()
        sent = 0
        for user in users:
            try:
                await self.app.bot.send_message(chat_id=user['telegram_id'], text=message)
                sent += 1
            except Exception:
                continue
        return sent

    async def scheduled_daily_quote_broadcast(self):
        """Send daily quote to all users at scheduled time"""
        import pytz
        from datetime import datetime, time, timedelta
        tz = pytz.timezone('Asia/Riyadh')
        # Get schedule from environment
        def get_scheduled_time():
            time_str = os.getenv("QUOTE_SCHEDULE", "14:00")
            try:
                hour, minute = map(int, time_str.strip().split(":"))
                if 0 <= hour < 24 and 0 <= minute < 60:
                    return hour, minute
            except Exception:
                pass
            return 14, 0  # default time
        target_hour, target_minute = get_scheduled_time()
        logger.info(f"🕑 Daily quote scheduler started (UTC+3) at {target_hour:02d}:{target_minute:02d}")
        while self.running:
            now = datetime.now(tz)
            next_run = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
            if now >= next_run:
                next_run += timedelta(days=1)
            wait_seconds = (next_run - now).total_seconds()
            logger.info(f"Next daily quote broadcast in {wait_seconds/60:.1f} minutes")
            await asyncio.sleep(wait_seconds)
            if not self.running:
                break
            # Fetch and send the quote
            quote = await self.grade_analytics.get_daily_quote()
            if quote:
                user = self.user_storage.get_user_by_telegram_id(telegram_id)
                do_translate = user.get("do_trans", False) if user else False
                quote_text = await self.grade_analytics.format_quote_dual_language(quote, do_translate=do_translate)
            else:
                message = "💬 رسالة اليوم:\n\nلم تتوفر رسالة اليوم حالياً."
            count = await self.send_quote_to_all_users(message)
            logger.info(f"✅ تم إرسال رسالة اليوم إلى {count} مستخدم.")

    async def _how_it_works_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🤖 هذا البوت يساعدك في متابعة درجاتك الجامعية بسهولة وأمان!\n\n"
            "• يمكنك معرفة درجاتك الحالية والسابقة في أي وقت\n"
            "• تصلك إشعارات فورية عند تحديث الدرجات\n"
            "• كل بياناتك مشفرة وآمنة ولا يتم تخزين كلمة المرور\n"
            "• يمكنك التواصل مع الدعم الفني لأي استفسار\n\n"
            "ابدأ الآن بالضغط على '🚀 تسجيل الدخول للجامعة'!"
        )

    async def _broadcast_quote(self, context: ContextTypes.DEFAULT_TYPE):
        try:
            quote = await self.grade_analytics.get_daily_quote()
            if not quote:
                logger.warning("No quote available for broadcast.")
                return
            # Format quote in two languages
            quote_text = await self.grade_analytics.format_quote_dual_language(quote)
            for user in self.user_storage.get_all_users():
                telegram_id = user.get("telegram_id")
                if telegram_id:
                    try:
                        await context.bot.send_message(chat_id=telegram_id, text=quote_text, parse_mode=ParseMode.MARKDOWN)
                    except Exception as e:
                        logger.warning(f"Failed to send quote to {telegram_id}: {e}")
        except Exception as e:
            logger.error(f"Error in _broadcast_quote: {e}")

    async def _refresh_keyboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Refresh keyboard based on user registration status"""
        try:
            user = self.user_storage.get_user(update.effective_user.id)
            if user:
                await update.message.reply_text(
                    "✅ تم تحديث الأزرار للمستخدمين المسجلين.",
                    reply_markup=get_main_keyboard()
                )
            else:
                await update.message.reply_text(
                    "❌ أنت غير مسجل. يرجى التسجيل أولاً.",
                    reply_markup=get_unregistered_keyboard()
                )
        except Exception as e:
            logger.error(f"[ALERT] Error in _refresh_keyboard: {e}", exc_info=True)
            admin_id = CONFIG.get("ADMIN_ID")
            admin_username = CONFIG.get("ADMIN_USERNAME", "@admin")
            if admin_id:
                try:
                    await self.app.bot.send_message(chat_id=admin_id, text=f"[REFRESH ERROR] User: {getattr(update.effective_user, 'id', None)}\nError: {e}")
                except Exception:
                    pass
            await update.message.reply_text(f"❌ حدث خطأ أثناء تحديث الأزرار. إذا استمرت المشكلة، لا تتردد في التواصل مع المطور {admin_username}.", reply_markup=get_main_keyboard())

    async def _force_logout_user(self, telegram_id: int, update: Update):
        """Force logout user due to invalid token"""
        logger.info(f"🔄 Forcing logout for user {telegram_id} due to invalid token")
        
        # End user session
        if hasattr(security_manager, 'session_manager'):
            security_manager.session_manager.invalidate_session(telegram_id)
        
        # Clear user token
        if hasattr(self.user_storage, 'clear_user_token'):
            # For PostgreSQL storage
            self.user_storage.clear_user_token(telegram_id)
        else:
            # For file storage
            user = self.user_storage.get_user(telegram_id)
            if user:
                user["token"] = None
                user["is_active"] = False
                if hasattr(self.user_storage, '_save_users'):
                    self.user_storage._save_users()
        
        # Notify user
        await update.message.reply_text(
            "⏰ انتهت صلاحية الجلسة\n\nتم تسجيل الخروج تلقائياً لحماية حسابك. يرجى تسجيل الدخول مرة أخرى من خلال زر '🚀 تسجيل الدخول للجامعة'.",
            reply_markup=get_unregistered_keyboard()
        )

    async def _logout_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        # End user session
        if hasattr(security_manager, 'session_manager'):
            security_manager.session_manager.invalidate_session(telegram_id)
        # Remove user token and mark as inactive
        user = self.user_storage.get_user(telegram_id)
        if user:
            if hasattr(self.user_storage, 'clear_user_token'):
                # For PostgreSQL storage
                self.user_storage.clear_user_token(telegram_id)
            else:
                # For file storage
                user["token"] = None
                user["is_active"] = False
                if hasattr(self.user_storage, '_save_users'):
                    self.user_storage._save_users()
        await update.message.reply_text(
            "✅ تم تسجيل الخروج بنجاح. يمكنك تسجيل الدخول مرة أخرى في أي وقت.",
            reply_markup=get_unregistered_keyboard()
        )

    async def _settings_callback_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = update.effective_user.id
        user = self.user_storage.get_user_by_telegram_id(user_id)
        
        if query.data == "toggle_translation":
            if not user:
                await query.edit_message_text("❗️ يجب التسجيل أولاً.")
                return
            # Toggle do_trans
            new_value = not user.get("do_trans", False)
            self.user_storage.update_user(user["username"], {"do_trans": new_value})
            # Refresh keyboard
            from utils.keyboards import get_settings_main_keyboard
            keyboard = get_settings_main_keyboard(translation_enabled=new_value)
            status = "مفعلة" if new_value else "معطلة"
            await query.edit_message_text(
                f"🌐 تم {'تفعيل' if new_value else 'تعطيل'} ترجمة الاقتباسات للعربية.\n\nالحالة الحالية: {status}",
                reply_markup=keyboard
            )
            return
            
        elif query.data == "delete_user_data":
            if not user:
                await query.edit_message_text("❗️ يجب التسجيل أولاً.")
                return
            # Show confirmation for data deletion
            await query.edit_message_text(
                "🗑️ **حذف البيانات الشخصية**\n\n"
                "⚠️ **تحذير**: هذا الإجراء سيحذف:\n"
                "• جميع بياناتك المخزنة\n"
                "• كلمة المرور المشفرة\n"
                "• إعداداتك الشخصية\n"
                "• سجل الدرجات\n\n"
                "❌ **لا يمكن التراجع عن هذا الإجراء**\n\n"
                "هل أنت متأكد من حذف جميع بياناتك؟",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ نعم، احذف جميع بياناتي", callback_data="confirm_delete_data")],
                    [InlineKeyboardButton("❌ إلغاء", callback_data="cancel_delete_data")]
                ])
            )
            return
            
        elif query.data == "confirm_delete_data":
            if not user:
                await query.edit_message_text("❗️ يجب التسجيل أولاً.")
                return
            # Delete user data
            try:
                # Delete user from storage
                self.user_storage.delete_user(user["username"])
                # Delete grades
                self.grade_storage.delete_user_grades(user["username"])
                await query.edit_message_text(
                    "✅ تم حذف جميع بياناتك بنجاح.\n\n"
                    "تم تسجيل خروجك تلقائياً. يمكنك التسجيل مرة أخرى إذا أردت.",
                    reply_markup=get_unregistered_keyboard()
                )
            except Exception as e:
                await query.edit_message_text(
                    f"❌ حدث خطأ أثناء حذف البيانات: {str(e)}\n\n"
                    "يرجى المحاولة مرة أخرى أو التواصل مع الدعم الفني."
                )
            return
            
        elif query.data == "cancel_delete_data":
            # Return to privacy settings
            await query.edit_message_text(
                "تم إلغاء حذف البيانات.",
                reply_markup=get_privacy_settings_keyboard()
            )
            return
            
        elif query.data == "toggle_show_profile":
            if not user:
                await query.edit_message_text("❗️ يجب التسجيل أولاً.")
                return
            # Toggle profile visibility (placeholder for future implementation)
            await query.edit_message_text(
                "👁️ **عرض المعلومات الشخصية**\n\n"
                "هذه الميزة قيد التطوير.\n\n"
                "ستتمكن قريباً من التحكم في عرض معلوماتك الشخصية للآخرين.",
                reply_markup=get_privacy_settings_keyboard()
            )
            return
            
        elif query.data == "toggle_share_stats":
            if not user:
                await query.edit_message_text("❗️ يجب التسجيل أولاً.")
                return
            # Toggle stats sharing (placeholder for future implementation)
            await query.edit_message_text(
                "📊 **مشاركة الإحصائيات**\n\n"
                "هذه الميزة قيد التطوير.\n\n"
                "ستتمكن قريباً من التحكم في مشاركة إحصائياتك مع المطورين لتحسين الخدمة.",
                reply_markup=get_privacy_settings_keyboard()
            )
            return
            
        elif query.data == "data_retention":
            if not user:
                await query.edit_message_text("❗️ يجب التسجيل أولاً.")
                return
            # Data retention settings (placeholder for future implementation)
            await query.edit_message_text(
                "📅 **فترة الاحتفاظ بالبيانات**\n\n"
                "هذه الميزة قيد التطوير.\n\n"
                "ستتمكن قريباً من تحديد المدة التي نحتفظ فيها ببياناتك.",
                reply_markup=get_privacy_settings_keyboard()
            )
            return
            
        elif query.data == "back_to_settings":
            # Return to main settings
            from utils.keyboards import get_settings_main_keyboard
            keyboard = get_settings_main_keyboard(translation_enabled=user.get("do_trans", False) if user else False)
            await query.edit_message_text(
                "تمت العودة إلى الإعدادات الرئيسية.",
                reply_markup=keyboard
            )
            return
            
        elif query.data == "back_to_main":
            await query.edit_message_text(
                "تمت العودة إلى القائمة الرئيسية.\n\n"
                "نحن نقدر ثقتك ونسعى دائماً للشفافية في كل ما يتعلق ببياناتك."
            )
        elif query.data == "cancel_action":
            is_registered = self.user_storage.is_user_registered(update.effective_user.id)
            keyboard = get_main_keyboard() if is_registered else get_unregistered_keyboard()
            await query.edit_message_text(
                "✅ تم إلغاء العملية. يمكنك البدء من جديد أو اختيار إجراء آخر.",
            )
            await update.effective_chat.send_message(
                "تمت إعادتك للقائمة الرئيسية.",
                reply_markup=keyboard
            )

    async def _gpa_calc_fallback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("تم إلغاء العملية. أرسل /start للبدء من جديد.")
        return ConversationHandler.END

    async def _gpa_calc_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['gpa_calc'] = {'courses': [], 'current': 0, 'count': 0}
        await update.message.reply_text(
            "كم عدد المقررات التي تريد حساب المعدل التراكمي لها؟ (أدخل رقماً بين 1 و10)",
            reply_markup=ReplyKeyboardMarkup([["❌ إلغاء"]], resize_keyboard=True, one_time_keyboard=True)
        )
        return ASK_GPA_COURSE_COUNT

    async def _gpa_ask_course_count(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            count = int(update.message.text.strip())
            if not (1 <= count <= 10):
                raise ValueError
            context.user_data['gpa_calc']['count'] = count
            context.user_data['gpa_calc']['current'] = 1
            await update.message.reply_text(
                f"أدخل النسبة المئوية للمقرر رقم 1 (مثال: 85)",
                reply_markup=ReplyKeyboardMarkup([["❌ إلغاء"]], resize_keyboard=True, one_time_keyboard=True)
            )
            return ASK_GPA_PERCENTAGE
        except Exception:
            await update.message.reply_text("❌ أدخل رقماً صحيحاً بين 1 و10.")
            return ASK_GPA_COURSE_COUNT

    async def _gpa_ask_percentage(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            # Try to extract integer from input
            text = update.message.text.strip()
            # Extract first number (integer or float) from the string
            import re
            match = re.search(r"\d+(?:\.\d+)?", text)
            if not match:
                raise ValueError("No digits found")
            percent = int(float(match.group(0)))
            if not (0 <= percent <= 100):
                raise ValueError("Out of range")
            # Check if percentage is below 30 (0 earned points)
            if percent < 30:
                await update.message.reply_text(f"⚠️ النسبة المئوية {percent}% أقل من 30%، ستكون النقاط المكتسبة 0.")
            context.user_data['gpa_calc']['courses'].append({'percentage': percent})
            # Ask for ECTS for this course
            current = context.user_data['gpa_calc']['current']
            await update.message.reply_text(
                f"أدخل عدد نقاط ECTS المخصصة للمقرر رقم {current} (مثال: 4)",
                reply_markup=ReplyKeyboardMarkup([["❌ إلغاء"]], resize_keyboard=True, one_time_keyboard=True)
            )
            return ASK_GPA_ECTS
        except Exception:
            await update.message.reply_text("❌ أدخل نسبة مئوية صحيحة بين 0 و100.")
            return ASK_GPA_PERCENTAGE

    async def _gpa_ask_ects(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            ects = float(update.message.text.strip())
            if not (0.5 <= ects <= 20):
                raise ValueError
            current = context.user_data['gpa_calc']['current']
            context.user_data['gpa_calc']['courses'][-1]['ects'] = ects
            if current >= context.user_data['gpa_calc']['count']:
                # Calculate GPA
                return await self._gpa_calc_show_result(update, context)
            else:
                context.user_data['gpa_calc']['current'] += 1
                await update.message.reply_text(
                    f"أدخل النسبة المئوية للمقرر رقم {context.user_data['gpa_calc']['current']} (دون إشارة %، مثال: 85)",
                    reply_markup=ReplyKeyboardMarkup([["❌ إلغاء"]], resize_keyboard=True, one_time_keyboard=True)
                )
                return ASK_GPA_PERCENTAGE
        except Exception:
            await update.message.reply_text("❌ أدخل عدد نقاط ECTS صحيح (عادة بين 0.5 و20)")
            return ASK_GPA_ECTS

    async def _gpa_calc_show_result(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        from utils.analytics import GradeAnalytics
        analytics = GradeAnalytics(self.user_storage)
        # Build grades list in the same format as analytics expects
        grades = []
        for c in context.user_data['gpa_calc']['courses']:
            grades.append({'total': str(c['percentage']), 'ects': c['ects']})
        gpa = analytics._calculate_gpa(grades)
        if gpa is not None:
            # Format to exactly 3 digits from left to right (e.g., 3.15, 2.5, 4.0)
            # Remove trailing zeros and decimal point
            gpa_str = f"{gpa:.2f}"
            # Remove trailing zeros (including those followed by decimal point)
            while gpa_str.endswith('0') and '.' in gpa_str:
                gpa_str = gpa_str[:-1]
            # Remove trailing decimal point
            if gpa_str.endswith('.'):
                gpa_str = gpa_str[:-1]
            if gpa_str == '':
                gpa_str = '0'
        else:
            gpa_str = "-"
        await update.message.reply_text(f"✅ المعدل التراكمي (GPA) للمقررات المدخلة: {gpa_str}", reply_markup=get_main_keyboard())
        context.user_data.pop('gpa_calc', None)
        return ConversationHandler.END

    async def _cancel_gpa_calc(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel handler for custom GPA calculator flow."""
        context.user_data.pop('gpa_calc', None)
        is_registered = self.user_storage.is_user_registered(update.effective_user.id)
        keyboard = get_main_keyboard() if is_registered else get_unregistered_keyboard()
        await update.message.reply_text(
            "❌ تم إلغاء عملية حساب المعدل. يمكنك البدء من جديد أو اختيار إجراء آخر.",
            reply_markup=keyboard
        )
        return ConversationHandler.END

    async def _session_management_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = self.user_storage.get_user(update.effective_user.id)
        if not user:
            await update.message.reply_text("❗️ يجب التسجيل أولاً.", reply_markup=get_unregistered_keyboard())
            return ConversationHandler.END
        session_type = "دائمة" if user.get("password_stored") else "مؤقتة"
        await update.message.reply_text(
            f"🔑 إدارة الجلسة/كلمة المرور\n\n"
            f"نوع الجلسة الحالي: {session_type}\n"
            "يمكنك هنا تغيير نوع الجلسة أو حذف كلمة المرور المخزنة.\n\n"
            "• للانتقال إلى جلسة مؤقتة (بدون تخزين كلمة المرور)، أرسل: 'تحويل إلى مؤقتة'\n"
            "• للانتقال إلى جلسة دائمة (تخزين كلمة المرور مشفر)، أرسل: 'تحويل إلى دائمة'\n"
            "• لحذف كلمة المرور المخزنة، أرسل: 'حذف كلمة المرور'\n\n"
            "🔙 العودة"
        )
        return ASK_SESSION_MANAGEMENT

    async def _handle_session_management(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text.strip()
        user_id = update.effective_user.id
        user = self.user_storage.get_user(user_id)
        if not user:
            await update.message.reply_text("❗️ يجب التسجيل أولاً.", reply_markup=get_unregistered_keyboard())
            return ConversationHandler.END
        if text == "تحويل إلى مؤقتة":
            self.user_storage.save_user(
                user_id,
                user["username"],
                user["token"],
                user,
                encrypted_password="",
                password_stored=False,
                password_consent_given=False
            )
            await update.message.reply_text("✅ تم التحويل إلى جلسة مؤقتة. لن يتم تخزين كلمة المرور بعد الآن.", reply_markup=get_main_keyboard())
            return ConversationHandler.END
        elif text == "تحويل إلى دائمة":
            await update.message.reply_text("يرجى إعادة إدخال كلمة المرور لتخزينها بشكل مشفر:")
            context.user_data["session_upgrade"] = True
            return ASK_PASSWORD
        elif text == "حذف كلمة المرور":
            self.user_storage.save_user(
                user_id,
                user["username"],
                user["token"],
                user,
                encrypted_password="",
                password_stored=False,
                password_consent_given=False
            )
            await update.message.reply_text("✅ تم حذف كلمة المرور المخزنة.", reply_markup=get_main_keyboard())
            return ConversationHandler.END
        elif text == "🔙 العودة":
            await self._return_to_main(update, context)
            return ConversationHandler.END
        else:
            await update.message.reply_text("❌ يرجى اختيار أو كتابة أحد الخيارات الصحيحة فقط.")
            return ASK_SESSION_MANAGEMENT

    async def _older_terms_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the 'older terms' button: show list of all terms, prompt for number, then fetch grades for selected term."""
        telegram_id = update.effective_user.id
        user = self.user_storage.get_user(telegram_id)
        if not user:
            await update.message.reply_text("❗️ يجب التسجيل أولاً.", reply_markup=get_unregistered_keyboard())
            return
        token = user.get("session_token")
        if not token:
            await update.message.reply_text("❗️ يجب إعادة تسجيل الدخول.", reply_markup=get_unregistered_keyboard())
            return
        # Fetch all terms
        homepage_data = await self.university_api.get_homepage_data(token)
        if not homepage_data:
            await update.message.reply_text("❌ تعذر جلب قائمة الفصول. حاول لاحقاً.", reply_markup=get_main_keyboard())
            return
        terms = self.university_api.extract_terms_from_homepage(homepage_data)
        if not terms or len(terms) < 1:
            await update.message.reply_text("❌ لا توجد فصول متاحة.", reply_markup=get_main_keyboard())
            return
        # Show numbered list (skip first two: current, previous)
        all_terms = terms
        context.user_data['older_terms_list'] = all_terms
        msg = "اختر رقم الفصل الذي تريد عرض درجاته:\n\n"
        for idx, (term_name, _) in enumerate(all_terms, 1):
            msg += f"{idx}. {term_name}\n"
        msg += "\nأدخل رقم الفصل المطلوب (مثال: 1):"
        await update.message.reply_text(msg, reply_markup=remove_keyboard())
        context.user_data['last_action'] = 'older_terms'
        return ASK_OLDER_TERM_NUMBER

    async def _ask_older_term_number(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        user = self.user_storage.get_user(telegram_id)
        if not user:
            await update.message.reply_text("❗️ يجب التسجيل أولاً.", reply_markup=get_unregistered_keyboard())
            return ConversationHandler.END
        token = user.get("session_token")
        if not token:
            await update.message.reply_text("❗️ يجب إعادة تسجيل الدخول.", reply_markup=get_unregistered_keyboard())
            return ConversationHandler.END
        all_terms = context.user_data.get('older_terms_list')
        if not all_terms:
            await update.message.reply_text("❌ لا توجد فصول متاحة.", reply_markup=get_main_keyboard())
            return ConversationHandler.END
        try:
            number = int(update.message.text.strip())
        except Exception:
            await update.message.reply_text("❌ أدخل رقم صحيح للفصل.")
            return ASK_OLDER_TERM_NUMBER
        if not (1 <= number <= len(all_terms)):
            await update.message.reply_text(f"❌ اختر رقم بين 1 و {len(all_terms)}.")
            return ASK_OLDER_TERM_NUMBER
        term_name, term_id = all_terms[number-1]
        # Fetch grades for selected term
        grades = await self.university_api.get_term_grades(token, term_id)
        if not grades:
            await update.message.reply_text(f"❌ لا توجد درجات متاحة للفصل: {term_name}", reply_markup=get_main_keyboard())
            return ConversationHandler.END
        # Add term info to grades
        for grade in grades:
            grade['term_name'] = term_name
            grade['term_id'] = term_id
        # Save grades to storage
        self.grade_storage.store_grades(user.get('username'), grades)
        # Format and send grades for the selected term
        formatted_message = await self.grade_analytics.format_old_grades_with_analysis(telegram_id, grades)
        if len(formatted_message) > 4096:
            for i in range(0, len(formatted_message), 4096):
                await update.message.reply_text(formatted_message[i:i+4096], reply_markup=get_main_keyboard())
        else:
            await update.message.reply_text(formatted_message, reply_markup=get_main_keyboard())
        return ConversationHandler.END

    async def _download_my_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        telegram_id = update.effective_user.id
        user = self.user_storage.get_user(telegram_id)
        if not user:
            await update.message.reply_text("❗️ يجب التسجيل أولاً.", reply_markup=get_unregistered_keyboard())
            return
        # Remove sensitive/session fields if needed
        user_info = dict(user)
        user_info.pop("session_token", None)
        # Convert to JSON
        json_str = json.dumps(user_info, ensure_ascii=False, indent=2)
        # Inform the user about privacy
        await update.message.reply_text(
            "هذه كل البيانات التي يخزنها البوت عنك. لا أحد يطلع عليها إلا عند طلبك ذلك بشكل مباشر، ويتم جلبها فقط عند طلبك."
        )
        # Send as file
        await update.message.reply_document(
            document=bytes(json_str, encoding="utf-8"),
            filename="my_information.json",
            caption="📥 هذه جميع المعلومات المخزنة عنك في قاعدة البيانات."
        )

    async def _silent_update_all_users_grades(self):
        """
        Refresh grades for all users and save them to storage, but do NOT send any notifications.
        Returns the number of users whose grades were refreshed.
        """
        users = self.user_storage.get_all_users()
        logger.info(f"🔕 Silent update: Found {len(users)} users in database")
        if not users:
            logger.warning("⚠️ No users found in database for silent update")
            return 0
        updated_count = 0
        semaphore = asyncio.Semaphore(CONFIG.get('MAX_CONCURRENT_REQUESTS', 5))
        tasks = []
        results = []

        async def refresh_user(user):
            async with semaphore:
                try:
                    telegram_id = user.get("telegram_id")
                    username = user.get("username")
                    username_unique = user.get("username_unique")
                    # Fallback: use username if username_unique is missing
                    storage_username = username_unique or username
                    if not storage_username:
                        logger.error(f"[ALERT] Cannot store grades: missing username and username_unique for user with telegram_id={telegram_id}")
                        return False
                    token = user.get("session_token")
                    lock = self._get_user_lock(storage_username)
                    async with lock:
                        if not token:
                            return False
                        # Test token validity
                        if not await self.university_api.test_token(token):
                            return False
                        user_data = await self.university_api.get_user_data(token)
                        if not user_data or "grades" not in user_data:
                            return False
                        new_grades = user_data.get("grades", [])
                        self.grade_storage.store_grades(storage_username, new_grades)
                        return True
                except Exception as e:
                    logger.error(f"❌ Error in silent grade refresh for user {user.get('username', 'Unknown')}: {e}", exc_info=True)
                    return False

        for user in users:
            tasks.append(asyncio.create_task(refresh_user(user)))
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            updated_count = sum(1 for r in results if r is True)
        logger.info(f"🔕 Silent update completed: {updated_count}/{len(users)} users refreshed")
        return updated_count