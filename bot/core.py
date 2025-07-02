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
from typing import Dict, List, Any
import re

from config import CONFIG
from storage.models import DatabaseManager
from storage.user_storage import UserStorage, PostgreSQLUserStorage
from storage.grade_storage import GradeStorage, PostgreSQLGradeStorage
from university.api_client import UniversityAPI
from admin.dashboard import AdminDashboard
from admin.broadcast import BroadcastSystem
from utils.keyboards import (
    get_main_keyboard, get_admin_keyboard, get_cancel_keyboard, 
    get_main_keyboard_with_relogin, get_unregistered_keyboard,
    remove_keyboard, get_error_recovery_keyboard
)
from utils.messages import get_welcome_message, get_help_message, get_simple_welcome_message, get_security_welcome_message, get_credentials_security_info_message
from security.transparency import SecurityTransparency
from security.enhancements import security_manager, is_valid_length
from security.headers import security_headers, security_policy

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
        self.security_transparency = SecurityTransparency()
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
        self.app.add_handler(CommandHandler("old_grades", self._old_grades_command))
        self.app.add_handler(CommandHandler("profile", self._profile_command))
        self.app.add_handler(CommandHandler("settings", self._settings_command))
        self.app.add_handler(CommandHandler("support", self._support_command))
        # Security transparency commands
        self.app.add_handler(CommandHandler("security_info", self._security_info_command))
        self.app.add_handler(CommandHandler("security_audit", self._security_audit_command))
        self.app.add_handler(CommandHandler("privacy_policy", self._privacy_policy_command))
        self.app.add_handler(CommandHandler("security_stats", self._security_stats_command))
        self.app.add_handler(CommandHandler("security_headers", self._security_headers_command))
        # Use a different command for the admin panel entry to avoid confusion with the keyboard
        self.app.add_handler(CommandHandler("admin", self._admin_command))
        self.app.add_handler(CommandHandler("notify_grades", self._admin_notify_grades))
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))

    async def _send_message_with_keyboard(self, update, message, keyboard_type="main"):
        keyboards = {
            "main": get_main_keyboard, 
            "admin": get_admin_keyboard, 
            "cancel": get_cancel_keyboard, 
            "relogin": get_main_keyboard_with_relogin, 
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
            "🎓 **دليل استخدام البوت**\n\n"
            "**كيفية الاستخدام:**\n"
            "1. اضغط '🚀 تسجيل الدخول' وأدخل بياناتك الجامعية\n"
            "2. استخدم الأزرار لفحص الدرجات والإعدادات\n"
            "3. للمساعدة تواصل مع المطور\n\n"
            "**الأوامر الأساسية:**\n"
            "/start - بدء الاستخدام\n"
            "/help - المساعدة\n"
            "/grades - التحقق من درجات الفصل الحالي\n"
            "/old_grades - التحقق من درجات الفصل السابق\n"
            "/profile - معلوماتي\n"
            "/settings - الإعدادات\n"
            "/support - الدعم الفني\n\n"
            "**أوامر الأمان:**\n"
            "/security_info - معلومات الأمان\n"
            "/security_audit - تقرير التدقيق الأمني\n"
            "/security_headers - معلومات معايير الأمان (للمطور فقط)\n"
            "/privacy_policy - سياسة الخصوصية\n"
        )
        
        if is_admin:
            help_text += "\n**أوامر المدير:**\n/security_stats - إحصائيات الأمان\n/admin - لوحة التحكم\n"
        
        help_text += f"\n👨‍💻 المطور: {CONFIG.get('ADMIN_USERNAME', '@admin')}"
        
        await update.message.reply_text(help_text, parse_mode='Markdown')

    async def _security_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show detailed security information"""
        try:
            security_info = self.security_transparency.get_detailed_security_info('ar')
            await update.message.reply_text(security_info, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text("عذراً، حدث خطأ أثناء عرض معلومات الأمان.")
            logger.error(f"Error in _security_info_command: {e}", exc_info=True)

    async def _security_audit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show security audit summary"""
        try:
            audit_summary = self.security_transparency.get_security_audit_summary('ar')
            await update.message.reply_text(audit_summary, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text("عذراً، حدث خطأ أثناء عرض تقرير التدقيق.")
            logger.error(f"Error in _security_audit_command: {e}", exc_info=True)

    async def _privacy_policy_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show privacy policy"""
        try:
            privacy_policy = self.security_transparency.get_privacy_policy('ar')
            await update.message.reply_text(privacy_policy, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text("عذراً، حدث خطأ أثناء عرض سياسة الخصوصية.")
            logger.error(f"Error in _privacy_policy_command: {e}", exc_info=True)

    async def _security_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show security statistics (admin only)"""
        try:
            if update.effective_user.id != CONFIG["ADMIN_ID"]:
                await update.message.reply_text("🚫 هذا الأمر متاح للمدير فقط.")
                return
            
            stats = security_manager.get_security_stats()
            stats_message = (
                "🔐 **إحصائيات الأمان (24 ساعة)**\n\n"
                f"📊 إجمالي الأحداث: {stats['total_events_24h']}\n"
                f"❌ محاولات تسجيل فاشلة: {stats['failed_logins']}\n"
                f"🚫 محاولات محظورة: {stats['blocked_attempts']}\n"
                f"👥 الجلسات النشطة: {stats['active_sessions']}\n"
                f"⚠️ أحداث عالية الخطورة: {stats['high_risk_events']}\n\n"
                "💡 هذه الإحصائيات تساعد في مراقبة الأمان"
            )
            await update.message.reply_text(stats_message, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text("عذراً، حدث خطأ أثناء جلب إحصائيات الأمان.")
            logger.error(f"Error in _security_stats_command: {e}", exc_info=True)

    async def _security_headers_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show security headers information (admin only)"""
        try:
            if update.effective_user.id != CONFIG["ADMIN_ID"]:
                await update.message.reply_text("🚫 هذا الأمر متاح للمطور فقط.")
                return
            
            headers = security_headers.get_security_headers()
            metadata = security_headers.get_security_metadata()
            policy_report = security_policy.get_security_report()
            
            headers_message = (
                "🔒 **Security Headers Information**\n\n"
                "**Applied Headers:**\n"
            )
            
            for header, value in headers.items():
                # Truncate long values for display
                display_value = value[:100] + "..." if len(value) > 100 else value
                headers_message += f"• {header}: {display_value}\n"
            
            headers_message += f"\n**Security Metadata:**\n"
            headers_message += f"• Security Level: {metadata['security_level']}\n"
            headers_message += f"• Compliance: {', '.join(metadata['compliance'])}\n"
            headers_message += f"• CSP Nonce: {metadata['csp_nonce'][:16]}...\n"
            
            headers_message += f"\n**Security Policy:**\n"
            headers_message += f"• Policy Version: {policy_report['policy_version']}\n"
            headers_message += f"• Allowed Domains: {len(policy_report['allowed_domains'])}\n"
            headers_message += f"• Blocked Patterns: {policy_report['blocked_patterns_count']}\n"
            
            await update.message.reply_text(headers_message, parse_mode='Markdown')
        except Exception as e:
            await update.message.reply_text("عذراً، حدث خطأ أثناء جلب معلومات معايير الأمان.")
            logger.error(f"Error in _security_headers_command: {e}", exc_info=True)

    async def _grades_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            # Store the action for error recovery
            context.user_data['last_action'] = 'grades'
            
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
            logger.error(f"Error in _grades_command: {e}", exc_info=True)
            await self._send_message_with_keyboard(
                update, 
                "❌ حدث خطأ أثناء جلب الدرجات. يرجى المحاولة مرة أخرى أو التواصل مع الدعم.",
                "error_recovery"
            )

    async def _old_grades_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show old term grades with analysis and quotes"""
        try:
            # Store the action for error recovery
            context.user_data['last_action'] = 'old_grades'
            
            telegram_id = update.effective_user.id
            user = self.user_storage.get_user(telegram_id)
            if not user:
                await update.message.reply_text("❗️ يجب التسجيل أولاً.")
                return
            token = user.get("token")
            if not token:
                await update.message.reply_text("❗️ يجب إعادة تسجيل الدخول.")
                return
            
            # Fetch old grades from API
            old_grades = await self.university_api.get_old_grades(token)
            if not old_grades:
                await update.message.reply_text("📚 لا توجد درجات سابقة متاحة للفصل الدراسي الأول 2024/2025.")
                return
            
            # Format grades with analytics and quotes
            formatted_message = await self.grade_analytics.format_old_grades_with_analysis(telegram_id, old_grades)
            await update.message.reply_text(formatted_message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in _old_grades_command: {e}", exc_info=True)
            await self._send_message_with_keyboard(
                update, 
                "❌ حدث خطأ أثناء جلب الدرجات السابقة. يرجى المحاولة مرة أخرى أو التواصل مع الدعم.",
                "error_recovery"
            )

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
        user_id = update.effective_user.id
        
        try:
            # Admin user search mode
            if user_id == CONFIG["ADMIN_ID"] and context.user_data.get('awaiting_user_search'):
                handled = await self.admin_dashboard.handle_user_search_message(update, context)
                if handled:
                    return
            
            # Admin user delete mode
            if user_id == CONFIG["ADMIN_ID"] and context.user_data.get('awaiting_user_delete'):
                handled = await self.admin_dashboard.handle_user_delete_message(update, context)
                if handled:
                    return
            
            # --- FIX: Handle admin broadcast mode ---
            if user_id == CONFIG["ADMIN_ID"] and context.user_data.get('awaiting_broadcast'):
                handled = await self.admin_dashboard.handle_dashboard_message(update, context)
                if handled:
                    return
            
            # Error recovery actions
            if text in ["🔄 إعادة المحاولة", "🏠 العودة للرئيسية"]:
                await self._handle_error_recovery(update, context, text)
                return
            
            # Enhanced action mapping with new button labels
            actions = {
                # Main grade actions
                "📊 درجات الفصل الحالي": self._grades_command,
                "📚 درجات الفصل السابق": self._old_grades_command,
                
                # User actions
                "👤 معلوماتي الشخصية": self._profile_command,
                "⚙️ الإعدادات والتخصيص": self._settings_command,
                
                # Support and help
                "📞 الدعم الفني": self._support_command,
                "❓ المساعدة والدليل": self._help_command,
                
                # Registration actions
                "🚀 تسجيل الدخول للجامعة": self._register_start,
                "🔄 إعادة تسجيل الدخول": self._register_start,
                
                # Admin actions
                "🎛️ لوحة التحكم الإدارية": self._admin_command,
                "🔙 العودة للوحة الرئيسية": self._return_to_main,
                
                # Legacy button support (for backward compatibility)
                "📊 التحقق من درجات الفصل الحالي": self._grades_command,
                "📚 التحقق من درجات الفصل السابق": self._old_grades_command,
                "👤 معلوماتي": self._profile_command,
                "⚙️ الإعدادات": self._settings_command,
                "📞 الدعم": self._support_command,
                "❓ المساعدة": self._help_command,
                "🚀 تسجيل الدخول": self._register_start,
                "🎛️ لوحة التحكم": self._admin_command,
                "🔙 العودة": self._return_to_main,
            }
            
            action = actions.get(text)
            if action:
                await action(update, context)
            else:
                # Enhanced error message with helpful guidance
                keyboard_to_show = get_main_keyboard() if self.user_storage.is_user_registered(user_id) else get_unregistered_keyboard()
                await update.message.reply_text(
                    "❓ لم أفهم طلبك\n\n"
                    "💡 **نصائح:**\n"
                    "• استخدم الأزرار أدناه للتنقل\n"
                    "• اكتب /help للمساعدة\n"
                    "• اكتب /start للعودة للرئيسية\n\n"
                    "📞 للمساعدة: اضغط '📞 الدعم الفني'",
                    reply_markup=keyboard_to_show
                )
        except Exception as e:
            logger.error(f"Error in _handle_message: {e}", exc_info=True)
            await self._send_message_with_keyboard(
                update, 
                "❌ حدث خطأ غير متوقع\n\n"
                "**الحلول:**\n"
                "• جرب مرة أخرى بعد قليل\n"
                "• إذا استمرت المشكلة، تواصل مع الدعم\n"
                "• تأكد من اتصالك بالإنترنت\n\n"
                "📞 للمساعدة: اضغط '📞 الدعم الفني'",
                "error_recovery"
            )

    async def _handle_error_recovery(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle error recovery actions from the error recovery keyboard."""
        text = update.message.text
        user_id = update.effective_user.id
        
        if text == "🔄 إعادة المحاولة":
            # Try to restore the last action context
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
                    await self._send_message_with_keyboard(
                        update, 
                        "❌ فشلت إعادة المحاولة. يرجى المحاولة مرة أخرى لاحقاً.",
                        "error_recovery"
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
        # This correctly delegates all admin button clicks to the dashboard handler
        await self.admin_dashboard.handle_callback(update, context)

    async def _admin_notify_grades(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != CONFIG["ADMIN_ID"]:
            await update.message.reply_text("🚫 ليس لديك صلاحية لهذه العملية.")
            return
        await update.message.reply_text("🔄 جاري فحص الدرجات لجميع المستخدمين...")
        count = await self._notify_all_users_grades()
        await update.message.reply_text(f"✅ تم فحص الدرجات وإشعار {count} مستخدم (إذا كان هناك تغيير).")

    async def get_token_expiration_stats(self) -> Dict[str, Any]:
        """Get statistics about token expiration for admin insights"""
        try:
            users = self.user_storage.get_all_users()
            total_users = len(users)
            expired_tokens = 0
            valid_tokens = 0
            no_tokens = 0
            
            for user in users:
                token = user.get('token')
                if not token:
                    no_tokens += 1
                elif not await self.university_api.test_token(token):
                    expired_tokens += 1
                else:
                    valid_tokens += 1
            
            return {
                'total_users': total_users,
                'valid_tokens': valid_tokens,
                'expired_tokens': expired_tokens,
                'no_tokens': no_tokens,
                'expiration_rate': (expired_tokens / total_users * 100) if total_users > 0 else 0
            }
        except Exception as e:
            logger.error(f"❌ Error getting token expiration stats: {e}", exc_info=True)
            return {
                'total_users': 0,
                'valid_tokens': 0,
                'expired_tokens': 0,
                'no_tokens': 0,
                'expiration_rate': 0
            }

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
            if not token:
                return False
            # Re-authenticate if needed
            if not await self.university_api.test_token(token):
                logger.warning(f"❌ Token expired for {username}. User needs to re-register with password.")
                
                # Notify user about token expiration with helpful message
                try:
                    display_name = user.get('fullname') or user.get('username', 'المستخدم')
                    expiration_message = (
                        f"⏰ **مرحباً {display_name}**\n\n"
                        f"🔐 **انتهت صلاحية جلسة تسجيل الدخول**\n\n"
                        f"**لماذا حدث هذا؟**\n"
                        f"• انتهت صلاحية الجلسة تلقائياً\n"
                        f"• هذا طبيعي ويحدث كل فترة\n"
                        f"• بياناتك آمنة ومشفرة\n\n"
                        f"**الحل:**\n"
                        f"• اضغط '🔄 إعادة تسجيل الدخول'\n"
                        f"• أدخل بياناتك مرة أخرى\n"
                        f"• ستتمكن من متابعة درجاتك\n\n"
                        f"💡 **نصيحة:**\n"
                        f"يمكنك استخدام '🔄 إعادة تسجيل الدخول' في أي وقت"
                    )
                    
                    await self.app.bot.send_message(
                        chat_id=telegram_id, 
                        text=expiration_message, 
                        parse_mode='Markdown',
                        reply_markup=get_main_keyboard_with_relogin()
                    )
                    
                    # Mark user as needing re-authentication
                    self.user_storage.update_user(telegram_id, {'token': None})
                    
                    logger.info(f"✅ Token expiration notification sent to user {username} (ID: {telegram_id}).")
                except Exception as e:
                    logger.error(f"❌ Error sending token expiration notification: {e}", exc_info=True)
                
                return False
                
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
        user_id = update.effective_user.id
        
        # Check rate limiting
        if not security_manager.check_login_attempt(user_id):
            await update.message.reply_text(
                "🚫 تم حظر محاولات تسجيل الدخول مؤقتاً بسبب كثرة المحاولات الفاشلة.\n"
                "يرجى المحاولة مرة أخرى بعد 15 دقيقة.",
                reply_markup=get_unregistered_keyboard()
            )
            return ConversationHandler.END
        
        # Show security info message before asking for credentials
        await update.message.reply_text(get_credentials_security_info_message())
        
        await update.message.reply_text(
            "يرجى إدخال الكود الجامعي الخاص بك. إذا احتجت للمساعدة، اضغط على '❓ المساعدة'."
        )
        return ASK_USERNAME

    async def _register_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = update.message.text.strip()
        
        # Enhanced validation using validators package
        if not is_valid_length(username, min_len=7, max_len=20):
            await update.message.reply_text(
                "❌ الكود الجامعي يجب أن يكون بين 7 و 20 حرف.\n\n"
                "❌ University code must be between 7 and 20 characters."
            )
            return ASK_USERNAME
        
        # University code format validation: 3+ letters followed by 4+ digits (e.g., ENG2425041)
        if not re.fullmatch(r"[A-Za-z]{3,}[0-9]{4,}", username):
            await update.message.reply_text(
                "❌ الكود الجامعي يجب أن يكون على الشكل: 3 أحرف أو أكثر ثم 4 أرقام أو أكثر (مثال: ENG2425041).\n\n"
                "❌ University code must be in the form: 3+ letters then 4+ digits (e.g., ENG2425041)."
            )
            return ASK_USERNAME
        
        context.user_data['username'] = username
        await update.message.reply_text("يرجى إدخال كلمة المرور:")
        return ASK_PASSWORD

    async def _register_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        username = context.user_data.get('username')
        password = update.message.text.strip()
        telegram_id = update.effective_user.id
        
        # Basic password validation to prevent injection attacks
        if not is_valid_length(password, min_len=1, max_len=100):
            await update.message.reply_text(
                "❌ كلمة المرور غير صحيحة.\n\n"
                "❌ Invalid password format."
            )
            return ASK_PASSWORD
        
        # Check for potential injection patterns
        if any(char in password for char in ['<', '>', '"', "'", '&', ';', '|', '`', '$', '(', ')', '{', '}']):
            await update.message.reply_text(
                "❌ كلمة المرور تحتوي على رموز غير مسموحة.\n\n"
                "❌ Password contains invalid characters."
            )
            return ASK_PASSWORD
        
        # Verify credentials with University API
        await update.message.reply_text("🔄 جاري التحقق من بياناتك...\nChecking your credentials...")
        token = await self.university_api.login(username, password)
        
        # Log login attempt
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
        # Fetch user info for welcome message
        user_info = await self.university_api._get_user_info(token)
        if user_info:
            fullname = user_info.get('fullname', username)
            firstname = user_info.get('firstname', fullname.split()[0] if ' ' in fullname else fullname)
            lastname = user_info.get('lastname', fullname.split()[1] if ' ' in fullname else '')
            email = user_info.get('email', '-')
        else:
            fullname = username
            firstname = username
            lastname = ''
            email = '-'
        
        user_data = {
            "username": username,
            "fullname": fullname,
            "firstname": firstname,
            "lastname": lastname,
            "email": email
        }
        self.user_storage.save_user(telegram_id, username, password, token=token, user_data=user_data)
        
        # Create secure session
        security_manager.create_user_session(telegram_id, token, user_data)
        
        # Show user-friendly welcome message
        welcome_message = get_welcome_message(fullname)
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        return ConversationHandler.END

    async def _return_to_main(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Return to main keyboard from admin interface"""
        keyboard_to_show = get_main_keyboard() if self.user_storage.is_user_registered(update.effective_user.id) else get_unregistered_keyboard()
        await update.message.reply_text(
            "تمت العودة إلى القائمة الرئيسية.",
            reply_markup=keyboard_to_show
        )

    async def _cancel_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("تم إلغاء التسجيل.")
        return ConversationHandler.END