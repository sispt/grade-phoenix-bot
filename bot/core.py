"""
🎓 Telegram Bot Core - Main Bot Implementation
"""
import asyncio
from datetime import datetime, timedelta, timezone
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters,
    ContextTypes, ConversationHandler
)
from typing import Dict, List
import re
import os

from config import CONFIG
from storage.models import DatabaseManager
from storage.user_storage_v2 import UserStorageV2
from storage.grade_storage_v2 import GradeStorageV2
from admin.dashboard import AdminDashboard
from admin.broadcast import BroadcastSystem
from utils.keyboards import (
    get_main_keyboard, get_admin_keyboard, get_cancel_keyboard, 
    get_unregistered_keyboard,
    remove_keyboard, get_error_recovery_keyboard, get_settings_main_keyboard
)
from utils.messages import get_welcome_message, get_help_message, get_simple_welcome_message, get_security_welcome_message, get_credentials_security_info_message
from security.enhancements import security_manager, is_valid_length
from security.headers import security_headers, security_policy
from utils.analytics import GradeAnalytics
from university.api_client_v2 import UniversityAPIV2
from utils.logger import get_bot_logger

# Get bot logger
logger = get_bot_logger()
ASK_USERNAME, ASK_PASSWORD = range(2)
ASK_GPA_COURSE_COUNT, ASK_GPA_PERCENTAGE, ASK_GPA_ECTS = range(10, 13)

class TelegramBot:
    """Main Telegram Bot Class"""
    
    def __init__(self):
        self.app, self.db_manager, self.user_storage, self.grade_storage = None, None, None, None
        self.university_api = UniversityAPIV2()
        # Initialize storage before other components
        self._initialize_storage() 
        # Initialize components that depend on storage
        self.grade_analytics = GradeAnalytics(self.user_storage)
        self.admin_dashboard = AdminDashboard(self)
        self.broadcast_system = BroadcastSystem(self)
        self.grade_check_task = None
        self.running = False

    def _initialize_storage(self):
        pg_initialized = False
        # Initialize new clean storage systems
        try:
            logger.info("🗄️ Initializing new clean storage systems...")
            self.user_storage = UserStorageV2(CONFIG["DATABASE_URL"])
            self.grade_storage = GradeStorageV2(CONFIG["DATABASE_URL"])
            logger.info("✅ New storage systems initialized successfully.")
        except Exception as e:
            logger.critical(f"❌ FATAL: Storage initialization failed. Bot cannot run: {e}", exc_info=True)
            raise RuntimeError("Failed to initialize storage systems.")

    async def start(self):
        self.running = True
        self.app = Application.builder().token(CONFIG["TELEGRAM_TOKEN"]).build()
        await self._update_bot_info()
        self._add_handlers()
        self.grade_check_task = asyncio.create_task(self._grade_checking_loop())
        self.daily_quote_task = asyncio.create_task(self.scheduled_daily_quote_broadcast())
        await self.app.initialize()
        await self.app.start()
        port = int(os.environ.get("PORT", 8443))
        
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
        if self.app: await self.app.shutdown()
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
                ASK_GPA_COURSE_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._gpa_ask_course_count)],
                ASK_GPA_PERCENTAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._gpa_ask_percentage)],
                ASK_GPA_ECTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._gpa_ask_ects)],
            },
            fallbacks=[MessageHandler(filters.Regex("^❌ إلغاء$"), self._cancel_registration)],
        )
        self.app.add_handler(gpa_calc_handler)
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        self.app.add_handler(CallbackQueryHandler(self._settings_callback_handler, pattern="^(back_to_main|cancel_action)$"))

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
            "3. للمساعدة تواصل مع المطور\n\n"
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
            # Send help as plain text
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
            token = user.get("token")
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
            
            # Format grades with quote
            logger.info(f"📝 Formatting grades for user {telegram_id}")
            message = await self.grade_analytics.format_current_grades_with_quote(telegram_id, grades)
            logger.info(f"✅ Sending formatted message to user {telegram_id}")
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=get_main_keyboard())
        except Exception as e:
            logger.error(f"❌ Error in _grades_command: {e}", exc_info=True)
            is_registered = self.user_storage.is_user_registered(update.effective_user.id)
            keyboard = get_main_keyboard() if is_registered else get_unregistered_keyboard()
            await update.message.reply_text("❌ حدث خطأ أثناء جلب الدرجات.", reply_markup=keyboard)

    async def _old_grades_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            context.user_data['last_action'] = 'old_grades'
            telegram_id = update.effective_user.id
            user = self.user_storage.get_user(telegram_id)
            if not user:
                await update.message.reply_text("❗️ يجب التسجيل أولاً.", reply_markup=get_unregistered_keyboard())
                return
            token = user.get("token")
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
            logger.error(f"Error in _old_grades_command: {e}", exc_info=True)
            context.user_data.pop('last_action', None)
            is_registered = self.user_storage.is_user_registered(update.effective_user.id)
            keyboard = get_main_keyboard() if is_registered else get_unregistered_keyboard()
            await update.message.reply_text("❌ حدث خطأ غير متوقع أثناء جلب الدرجات السابقة. يرجى المحاولة لاحقاً أو التواصل مع الدعم.", reply_markup=keyboard)

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
            "- يمكنك زيارة الكود البرمجي على GitHub."
        )

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
                f"📞 للدعم الفني تواصل مع المطور: {admin_username}\nاضغط الزر أدناه للتواصل مباشرة.",
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
            if text in ["🔄 إعادة المحاولة", "🏠 العودة للرئيسية"]:
                await self._handle_error_recovery(update, context)
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
            logger.error(f"Error in _handle_message: {e}", exc_info=True)
            context.user_data.clear()
            is_registered = self.user_storage.is_user_registered(user_id)
            keyboard = get_main_keyboard() if is_registered else get_unregistered_keyboard()
            await update.message.reply_text(
                "❌ حدث خطأ غير متوقع\n\n**الحلول:**\n• جرب مرة أخرى بعد قليل\n• إذا استمرت المشكلة، تواصل مع الدعم\n• تأكد من اتصالك بالإنترنت\n\n📞 للمساعدة: اضغط '📞 الدعم الفني' أو الزر أدناه.",
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
        if update.effective_user.id != CONFIG["ADMIN_ID"]: return
        query = update.callback_query
        await query.answer()
        # Delegate admin button clicks
        await self.admin_dashboard.handle_callback(update, context)

    async def _admin_notify_grades(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != CONFIG["ADMIN_ID"]:
            await update.message.reply_text("🚫 ليس لديك صلاحية لهذه العملية.", reply_markup=get_main_keyboard())
            return
        await update.message.reply_text("🔄 جاري فحص الدرجات لجميع المستخدمين...")
        count = await self._notify_all_users_grades()
        await update.message.reply_text(f"✅ تم فحص الدرجات وإشعار {count} مستخدم (إذا كان هناك تغيير).", reply_markup=get_main_keyboard())

    async def _grade_checking_loop(self):
        await asyncio.sleep(10)  # Wait a bit before starting grade check
        while self.running:
            try:
                logger.info("🔔 Running scheduled grade check for all users...")
                await self._notify_all_users_grades()
            except Exception as e:
                logger.error(f"❌ Error in scheduled grade check: {e}", exc_info=True)
            interval = CONFIG.get('GRADE_CHECK_INTERVAL', 10) * 60
            await asyncio.sleep(interval)

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
            token = user.get("token")
            
            logger.debug(f"🔍 Starting grade check for user {username} (ID: {telegram_id})")
            
            # Notify only once if token expired
            if not token:
                logger.debug(f"❌ No token for user {username}")
                return False
                
            is_pg = hasattr(self.user_storage, 'update_token_expired_notified')
            notified = user.get("token_expired_notified", False)
            
            logger.debug(f"🔍 Testing token for user {username}")
            if not await self.university_api.test_token(token):
                logger.warning(f"❌ Token expired for user {username}")
                
                # Token is invalid, notify user to login manually
                if not notified:
                    await self.app.bot.send_message(
                        chat_id=telegram_id,
                        text="⏰ انتهت صلاحية الجلسة\n\nيرجى تسجيل الدخول مرة أخرى من خلال زر '🚀 تسجيل الدخول للجامعة' ثم إدخال بياناتك من جديد. هذا طبيعي ويحدث كل فترة.",
                        reply_markup=get_unregistered_keyboard()
                    )
                    # Mark as notified
                    if is_pg:
                        self.user_storage.update_token_expired_notified(telegram_id, True)
                    else:
                        user["token_expired_notified"] = True
                        if hasattr(self.user_storage, '_save_users'):
                            self.user_storage._save_users()
                return False
                
            logger.debug(f"✅ Token valid for user {username}")
            
            # Reset notification flag if token is valid
            if notified:
                if is_pg:
                    self.user_storage.update_token_expired_notified(telegram_id, False)
                else:
                    # Update file storage
                    user["token_expired_notified"] = False
                    if hasattr(self.user_storage, '_save_users'):
                        self.user_storage._save_users()
                        
            logger.debug(f"🔍 Fetching user data for {username}")
            user_data = await self.university_api.get_user_data(token)
            if not user_data or "grades" not in user_data:
                logger.info(f"No grade data available for {username} in this check.")
                return False
                
            new_grades = user_data.get("grades", [])
            logger.debug(f"📊 Found {len(new_grades)} new grades for user {username}")
            
            old_grades = self.grade_storage.get_user_grades(telegram_id)
            logger.debug(f"📊 Found {len(old_grades) if old_grades else 0} stored grades for user {username}")
            
            changed_courses = self._compare_grades(old_grades, new_grades)
            logger.debug(f"🔍 Grade comparison for {username}: {len(changed_courses)} changes detected")
            
            if changed_courses:
                logger.warning(f"GRADE CHECK: Found {len(changed_courses)} grade changes for user {username}. Sending notification.")
                display_name = user.get('fullname') or user.get('username', 'المستخدم')
                message = f"🎓 تم تحديث درجاتك في المواد التالية:\n\n"
                old_map = {g.get('code') or g.get('name'): g for g in old_grades if g.get('code') or g.get('name')}
                for grade in changed_courses:
                    name = grade.get('name', 'N/A')
                    code = grade.get('code', '-')
                    coursework = grade.get('coursework', 'لم يتم النشر')
                    final_exam = grade.get('final_exam', 'لم يتم النشر')
                    total = grade.get('total', 'لم يتم النشر')
                    key = code if code != '-' else name
                    old = old_map.get(key, {})
                    def show_change(field, label):
                        old_val = old.get(field, '—')
                        new_val = grade.get(field, '—')
                        if old_val != new_val and old_val != '—':
                            return f"{label}: {old_val} → {new_val}"
                        return None
                    changes = [
                        show_change('coursework', 'الأعمال'),
                        show_change('final_exam', 'النظري'),
                        show_change('total', 'النهائي'),
                    ]
                    changes = [c for c in changes if c]
                    if changes:
                        message += f"📚 {name} ({code})\n" + "\n".join(changes) + "\n\n"
                now_utc3 = datetime.now(timezone.utc) + timedelta(hours=3)
                message += f"🕒 وقت التحديث: {now_utc3.strftime('%Y-%m-%d %H:%M')} (UTC+3)"
                await self.app.bot.send_message(chat_id=telegram_id, text=message)
                return True
            else:
                logger.debug(f"✅ No grade changes for user {username}")
            return False
        except Exception as e:
            logger.error(f"❌ Error in _check_and_notify_user_grades for user {user.get('username', 'Unknown')}: {e}", exc_info=True)
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
        
        # Try to log in with university API
        await update.message.reply_text("🔄 جاري التحقق من بياناتك...\nChecking your credentials...")
        token = await self.university_api.login(username, password)
        
        # Record login attempt
        success = token is not None
        security_manager.record_login_attempt(telegram_id, success, username)
        
        if not token:
            await update.message.reply_text(
                "❌ تعذّر تسجيل الدخول. يرجى التأكد من صحة اسم المستخدم وكلمة المرور الجامعية وإعادة المحاولة.\n\n"
                "Login failed. Please check your university username and password and try again.",
                reply_markup=get_unregistered_keyboard()
            )
            # Restart registration from username
            return await self._register_start(update, context)
        
        # Get user info for welcome message
        logger.info(f"🔍 Fetching user info for registration...")
        user_info = await self.university_api.get_user_info(token)
        logger.info(f"🔍 User info result: {user_info}")
        
        if user_info:
            # The API returns 'fullname', 'firstname', 'lastname' fields
            api_fullname = user_info.get('fullname', '')
            api_firstname = user_info.get('firstname', '')
            api_lastname = user_info.get('lastname', '')
            api_username = user_info.get('username', username)
            email = user_info.get('email', '-')
            
            logger.info(f"🔍 API fullname: '{api_fullname}', firstname: '{api_firstname}', lastname: '{api_lastname}', username: '{api_username}', email: '{email}'")
            
            # Use the API name fields if available, otherwise use a more user-friendly fallback
            if api_fullname and api_fullname.strip():
                fullname = api_fullname.strip()
                logger.info(f"✅ Using API fullname: '{fullname}'")
                # Use the individual name fields if available, otherwise split the fullname
                if api_firstname and api_firstname.strip():
                    firstname = api_firstname.strip()
                    lastname = api_lastname.strip() if api_lastname else ''
                else:
                    # Fallback: split fullname into first and last
                    name_parts = fullname.split()
                    if len(name_parts) >= 2:
                        firstname = name_parts[0]
                        lastname = ' '.join(name_parts[1:])
                    else:
                        firstname = fullname
                        lastname = ''
            else:
                # Fallback: use a more descriptive name instead of student ID
                logger.warning(f"⚠️ API fullname is empty or whitespace, using fallback")
                fullname = f"طالب جامعة الشام ({api_username})"
                firstname = "طالب"
                lastname = "جامعة الشام"
        else:
            # Fallback when API call fails
            logger.warning(f"⚠️ User info API call failed, using fallback")
            fullname = f"طالب جامعة الشام ({username})"
            firstname = "طالب"
            lastname = "جامعة الشام"
            email = '-'
        
        # Store user data and token in context for later use
        context.user_data['user_data'] = {
            "username": username,
            "fullname": fullname,
            "firstname": firstname,
            "lastname": lastname,
            "email": email
        }
        context.user_data['token'] = token
        
        # Complete registration directly (no password storage)
        return await self._complete_registration(update, context)
    

    
    async def _complete_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Complete user registration"""
        telegram_id = update.effective_user.id
        user_data = context.user_data.get('user_data')
        token = context.user_data.get('token')
        
        if not user_data or not token:
            await update.message.reply_text(
                "❌ حدث خطأ في البيانات. يرجى المحاولة مرة أخرى.",
                reply_markup=get_unregistered_keyboard()
            )
            return ConversationHandler.END
        
        # Save user to database
        try:
            success = self.user_storage.save_user(
                telegram_id, 
                user_data['username'], 
                token, 
                user_data
            )
            
            if not success:
                logger.error(f"❌ Failed to save user {user_data['username']}")
                await update.message.reply_text(
                    "❌ حدث خطأ أثناء حفظ البيانات. يرجى المحاولة مرة أخرى.", 
                    reply_markup=get_unregistered_keyboard()
                )
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
            # Don't raise here, continue with registration
        
        # Show welcome message
        welcome_message = get_welcome_message(user_data['fullname'])
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
        await update.message.reply_text("تم إلغاء التسجيل.", reply_markup=get_main_keyboard())
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
                message = await self.grade_analytics.format_quote_dual_language(quote)
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
        if query.data == "back_to_main":
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

    async def _gpa_calc_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data['gpa_calc'] = {'courses': [], 'current': 0, 'count': 0}
        await update.message.reply_text("كم عدد المقررات التي تريد حساب المعدل التراكمي لها؟ (أدخل رقماً بين 1 و10)")
        return ASK_GPA_COURSE_COUNT

    async def _gpa_ask_course_count(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            count = int(update.message.text.strip())
            if not (1 <= count <= 10):
                raise ValueError
            context.user_data['gpa_calc']['count'] = count
            context.user_data['gpa_calc']['current'] = 1
            await update.message.reply_text(f"أدخل النسبة المئوية للمقرر رقم 1 (مثال: 85)")
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
            await update.message.reply_text(f"أدخل عدد نقاط ECTS المخصصة للمقرر رقم {current} (مثال: 4)")
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
                await update.message.reply_text(f"أدخل النسبة المئوية للمقرر رقم {context.user_data['gpa_calc']['current']} (دون إشارة %، مثال: 85)")
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
        gpa_str = f"{gpa:.3f}" if gpa is not None else "-"
        await update.message.reply_text(f"✅ المعدل التراكمي (GPA) للمقررات المدخلة: {gpa_str}", reply_markup=get_main_keyboard())
        context.user_data.pop('gpa_calc', None)
        return ConversationHandler.END