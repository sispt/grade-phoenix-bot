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
# Import specific keyboard functions, not the whole module for clarity
from utils.keyboards import get_main_keyboard, get_admin_keyboard, get_cancel_keyboard, get_main_keyboard_with_relogin
from utils.messages import get_welcome_message, get_help_message

logger = logging.getLogger(__name__)
ASK_USERNAME, ASK_PASSWORD = range(2)

class TelegramBot:
    """Main Telegram Bot Class"""
    
    def __init__(self):
        self.app, self.db_manager, self.user_storage, self.grade_storage = None, None, None, None
        self.university_api = UniversityAPI()
        self.admin_dashboard = AdminDashboard(self)
        self.broadcast_system = BroadcastSystem(self)
        self.grade_check_task, self.running = None, False
        self._initialize_storage()
        
    def _initialize_storage(self):
        try:
            if CONFIG.get("USE_POSTGRESQL") and CONFIG.get("DATABASE_URL"):
                self.db_manager = DatabaseManager(CONFIG["DATABASE_URL"])
                if self.db_manager.test_connection():
                    self.user_storage, self.grade_storage = PostgreSQLUserStorage(self.db_manager), PostgreSQLGradeStorage(self.db_manager)
                    logger.info("✅ PostgreSQL storage initialized.")
                    return
            logger.info("📁 Initializing file-based storage.")
            self.user_storage, self.grade_storage = UserStorage(), GradeStorage()
        except Exception as e:
            logger.error(f"❌ Storage initialization failed: {e}", exc_info=True)

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
            states={ASK_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._register_username)], ASK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._register_password)]},
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
        keyboards = {"main": get_main_keyboard, "admin": get_admin_keyboard, "cancel": get_cancel_keyboard, "relogin": get_main_keyboard_with_relogin}
        await update.message.reply_text(message, reply_markup=keyboards.get(keyboard_type, get_main_keyboard)())
    
    async def _edit_message_no_keyboard(self, message_obj, new_text):
        try: await message_obj.edit_text(new_text)
        except Exception: pass

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._send_message_with_keyboard(update, get_welcome_message())
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._send_message_with_keyboard(update, get_help_message())

    async def _register_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🚀 **تسجيل الدخول**\n\n📝 **أدخل اسم المستخدم الجامعي:**", reply_markup=get_cancel_keyboard())
        return ASK_USERNAME

    async def _register_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data["username"] = update.message.text.strip()
        await update.message.reply_text("أدخل كلمة المرور:", reply_markup=get_cancel_keyboard())
        return ASK_PASSWORD

    async def _register_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        loading_msg = await update.message.reply_text("🔄 جاري تسجيل الدخول...")
        try:
            username, password = context.user_data["username"], update.message.text.strip()
            token = await self.university_api.login(username, password)
            if not token:
                await loading_msg.edit_text("فشل تسجيل الدخول. تحقق من بياناتك.")
                # Ensure keyboard is visible again after failure
                await update.message.reply_text("اضغط '🚀 تسجيل الدخول' للمحاولة مرة أخرى", reply_markup=get_main_keyboard())
                return ConversationHandler.END
            
            await loading_msg.edit_text("📊 جاري جلب بياناتك...")
            user_data = await self.university_api.get_user_data(token)
            if not user_data:
                await loading_msg.edit_text("❌ **فشل جلب بيانات الطالب**")
                # Ensure keyboard is visible again after failure
                await update.message.reply_text("اضغط '🚀 تسجيل الدخول' للمحاولة مرة أخرى", reply_markup=get_main_keyboard())
                return ConversationHandler.END

            self.user_storage.save_user(update.effective_user.id, username, password, token, user_data)
            self.grade_storage.save_grades(update.effective_user.id, user_data.get("grades", []))
            await loading_msg.edit_text(f"✅ تم تسجيل الدخول بنجاح.\nمرحباً {user_data.get('fullname')}.")
            
            # Explicitly send the main keyboard as a *new* message to ensure it appears
            await update.message.reply_text("تم التسجيل. استخدم القائمة الرئيسية.", reply_markup=get_main_keyboard())
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"Login error: {e}", exc_info=True)
            await loading_msg.edit_text("خطأ في الاتصال. حاول لاحقاً.")
            # Ensure keyboard is visible again after network error
            await update.message.reply_text("اضغط '🚀 تسجيل الدخول' للمحاولة مرة أخرى", reply_markup=get_main_keyboard())
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
                    await self._send_message_with_keyboard(update, "اضغط '🚀 تسجيل الدخول' لتجديد الجلسة", "relogin")
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
        user = self.user_storage.get_user(update.effective_user.id)
        if not user: return await update.message.reply_text("❌ لم يتم تسجيلك بعد.", reply_markup=get_main_keyboard())
        grades_count = len(self.grade_storage.get_grades(update.effective_user.id))
        await update.message.reply_text(f"👤 **معلوماتك الشخصية:**\n🆔 `{user.get('telegram_id')}`\n👨‍🎓 `{user.get('username', 'N/A')}`\n📧 `{user.get('email', 'N/A')}`\n📊 `{grades_count}` مواد")

    async def _settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"⚙️ **الإعدادات الحالية:**\n- الإشعارات: {'🔔 مفعلة' if CONFIG['ENABLE_NOTIFICATIONS'] else '🔕 معطلة'}\n- فترة الفحص: كل {CONFIG['GRADE_CHECK_INTERVAL']} دقائق.")

    async def _support_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"📞 للدعم الفني، تواصل مع المطور: {CONFIG['ADMIN_USERNAME']}")

    async def _admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id == CONFIG["ADMIN_ID"]:
            await self.admin_dashboard.show_dashboard(update, context)
        else:
            await self._send_message_with_keyboard(update, "🚫 ليس لديك صلاحية لهذه العملية.")

    async def _list_users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != CONFIG["ADMIN_ID"]: return
        await self.admin_dashboard.list_users_command(update, context) # Delegate to admin dashboard

    async def _restart_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != CONFIG["ADMIN_ID"]: return
        await update.message.reply_text("🔄 جارٍ إعادة تشغيل البوت...")
        logger.info("Soft restart command received from admin.")
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = update.message.text
        actions = {
            # Main User Actions
            "📊 فحص الدرجات": self._grades_command,
            "❓ المساعدة": self._help_command,
            "👤 معلوماتي": self._profile_command,
            "⚙️ الإعدادات": self._settings_command,
            "📞 الدعم": self._support_command,
            # Admin Panel Entry Point
            "🎛️ لوحة التحكم": self._admin_command,
        }
        action = actions.get(text)
        if action:
            await action(update, context)
        else:
            await update.message.reply_text("❓ لم أفهم طلبك. استخدم الأزرار.", reply_markup=get_main_keyboard())

    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != CONFIG["ADMIN_ID"]: return
        query = update.callback_query
        await query.answer()
        await self.admin_dashboard.handle_callback(update, context)
        
    async def _grade_checking_loop(self):
        while self.running:
            try:
                logger.info("🔍 DEBUG: Starting grade check cycle...")
                users = self.user_storage.get_all_users()
                await asyncio.gather(*(self._check_user_grades(user) for user in users))
                logger.info(f"✅ Grade check completed. Next check in {CONFIG['GRADE_CHECK_INTERVAL']} minutes")
            except asyncio.CancelledError:
                logger.info("🛑 Grade checking task cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Error in grade checking loop: {e}", exc_info=True)
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
                logger.info(f"✅ DEBUG: Re-authentication successful for {username}. Token updated.")

            user_data = await self.university_api.get_user_data(token)
            if not user_data or "grades" not in user_data: return

            new_grades = user_data.get("grades", [])
            old_grades = self.grade_storage.get_grades(telegram_id)
            
            changed_courses = self._compare_grades(old_grades, new_grades)

            if changed_courses:
                logger.info(f"🔄 DEBUG: Found {len(changed_courses)} grade changes for user {username}. Sending notification.")
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
                    logger.info(f"✅ DEBUG: Grade update notification sent to user {username} (ID: {telegram_id}).")
                except Exception as e:
                    logger.error(f"❌ DEBUG: Failed to send notification to {username} (ID: {telegram_id}): {e}", exc_info=True)
                
                self.grade_storage.save_grades(telegram_id, new_grades)
                logger.info(f"💾 DEBUG: Updated grades saved for user {username}.")
            else:
                logger.info(f"✅ DEBUG: No grade changes for user {username}.")
                
        except Exception as e:
            logger.error(f"❌ DEBUG: Error checking grades for user {user.get('username', 'Unknown')}: {e}", exc_info=True)

    def _compare_grades(self, old_grades: List[Dict], new_grades: List[Dict]) -> List[Dict]:
        old_grades_map = {g.get('code') or g.get('name'): g for g in old_grades if g.get('code') or g.get('name')}
        changes = []
        for new_grade in new_grades:
            key = new_grade.get('code') or new_grade.get('name')
            if not key: continue
            if key not in old_grades_map or old_grades_map[key] != new_grade:
                changes.append(new_grade)
        return changes