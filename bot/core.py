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
from storage.users import UserStorage  # Fallback for local development
from storage.grades import GradeStorage  # Fallback for local development
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
        
        # Initialize storage based on configuration
        self._initialize_storage()
        
    def _initialize_storage(self):
        """Initialize storage system based on configuration"""
        try:
            if CONFIG.get("USE_POSTGRESQL", False):
                # Use PostgreSQL
                logger.info("🗄️ Initializing PostgreSQL storage...")
                try:
                    self.db_manager = DatabaseManager(CONFIG["DATABASE_URL"])
                    
                    # Test database connection
                    if self.db_manager.test_connection():
                        self.user_storage = PostgreSQLUserStorage(self.db_manager)
                        self.grade_storage = PostgreSQLGradeStorage(self.db_manager)
                        logger.info("✅ PostgreSQL storage initialized successfully")
                    else:
                        logger.error("❌ PostgreSQL connection failed, falling back to file storage")
                        self._initialize_file_storage()
                except Exception as e:
                    logger.error(f"❌ PostgreSQL initialization failed: {e}")
                    logger.info("🔄 Falling back to file-based storage...")
                    self._initialize_file_storage()
            else:
                # Use file-based storage
                logger.info("📁 Initializing file-based storage...")
                self._initialize_file_storage()
                
        except Exception as e:
            logger.error(f"❌ Storage initialization failed: {e}")
            logger.info("🔄 Falling back to file-based storage...")
            self._initialize_file_storage()
    
    def _initialize_file_storage(self):
        """Initialize file-based storage as fallback"""
        try:
            self.user_storage = UserStorage()
            self.grade_storage = GradeStorage()
            logger.info("✅ File-based storage initialized successfully")
        except Exception as e:
            logger.error(f"❌ File storage initialization failed: {e}")
            raise
    
    async def start(self):
        """Start the bot"""
        import os
        try:
            # Initialize bot application
            self.app = Application.builder().token(CONFIG["TELEGRAM_TOKEN"]).build()
            
            # Update bot information
            await self._update_bot_info()
            
            # Add handlers
            self._add_handlers()
            
            # Start grade checking task
            if CONFIG["ENABLE_NOTIFICATIONS"]:
                self.grade_check_task = asyncio.create_task(self._grade_checking_loop())
            
            # Start webhook (for Railway)
            await self.app.initialize()
            await self.app.start()
            port = int(os.environ.get("PORT", 8443))
            
            # Dynamic webhook URL
            webhook_url = os.getenv("WEBHOOK_URL")
            if not webhook_url:
                # Fallback to Railway URL
                webhook_url = f"https://shamunibot-production.up.railway.app/{CONFIG['TELEGRAM_TOKEN']}"
            
            logger.info(f"DEBUG: Setting up webhook on port {port}")
            logger.info(f"DEBUG: Webhook URL: {webhook_url}")
            
            try:
                await self.app.updater.start_webhook(
                    listen="0.0.0.0",
                    port=port,
                    url_path=CONFIG["TELEGRAM_TOKEN"],
                    webhook_url=webhook_url
                )
                logger.info("DEBUG: Webhook started successfully")
            except Exception as webhook_error:
                logger.error(f"DEBUG: Webhook setup failed: {webhook_error}")
                # Fallback to polling if webhook fails
                logger.info("DEBUG: Falling back to polling mode")
                await self.app.updater.start_polling()
                logger.info("DEBUG: Polling started successfully")
            
            self.running = True
            logger.info("🤖 Bot started successfully with webhook!")
            logger.info(f"🌐 Webhook URL: {webhook_url}")
            
        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            raise
    
    async def _update_bot_info(self):
        """Update bot name and description"""
        try:
            logger.info("🔄 Updating bot information...")
            
            # Update bot name
            await self.app.bot.set_my_name(CONFIG["BOT_NAME"])
            logger.info(f"✅ Bot name updated to: {CONFIG['BOT_NAME']}")
            
            # Update bot description
            await self.app.bot.set_my_description(CONFIG["BOT_DESCRIPTION"])
            logger.info(f"✅ Bot description updated")
            
            # Update bot short description
            short_description = "بوت إشعارات الدرجات الجامعية - جامعة الشام"
            await self.app.bot.set_my_short_description(short_description)
            logger.info(f"✅ Bot short description updated")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to update bot info: {e}")
            # Continue anyway, this is not critical
    
    async def stop(self):
        """Stop the bot"""
        try:
            self.running = False
            
            if self.grade_check_task:
                self.grade_check_task.cancel()
            
            if self.app:
                await self.app.updater.stop()
                await self.app.stop()
                await self.app.shutdown()
            
            logger.info("🛑 Bot stopped successfully!")
            
        except Exception as e:
            logger.error(f"❌ Error stopping bot: {e}")
    
    def _add_handlers(self):
        """Add all bot handlers"""
        logger.info("DEBUG: Adding bot handlers...")
        
        # Basic commands
        self.app.add_handler(CommandHandler("start", self._start_command))
        self.app.add_handler(CommandHandler("help", self._help_command))
        self.app.add_handler(CommandHandler("register", self._register_start))
        logger.info("DEBUG: Basic command handlers added")
        
        # User commands
        self.app.add_handler(CommandHandler("grades", self._grades_command))
        self.app.add_handler(CommandHandler("profile", self._profile_command))
        self.app.add_handler(CommandHandler("settings", self._settings_command))
        self.app.add_handler(CommandHandler("support", self._support_command))
        logger.info("DEBUG: User command handlers added")
        
        # Admin commands
        self.app.add_handler(CommandHandler("stats", self._stats_command))
        self.app.add_handler(CommandHandler("list_users", self._list_users_command))
        self.app.add_handler(CommandHandler("restart", self._restart_command))
        logger.info("DEBUG: Admin command handlers added")
        
        # Conversation handlers (registration and broadcast) - these must come BEFORE the generic message handler
        self.app.add_handler(self._get_registration_handler())
        self.app.add_handler(self._get_broadcast_handler())
        logger.info("DEBUG: Conversation handlers added")
        
        # Callback query handler
        self.app.add_handler(CallbackQueryHandler(self._handle_callback))
        logger.info("DEBUG: Callback query handler added")
        
        # Message handler for buttons (should be last)
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        logger.info("DEBUG: Message handler added")
        
        # Add catch-all update logger
        self.app.add_handler(TypeHandler(Update, self._log_any_update))
        logger.info("DEBUG: TypeHandler for logging added")
        
        logger.info("DEBUG: All handlers added successfully!")
    
    def _get_registration_handler(self):
        """Get registration conversation handler"""
        logger.info("DEBUG: Creating registration conversation handler")
        handler = ConversationHandler(
            entry_points=[
                CommandHandler("register", self._register_start),
                MessageHandler(filters.Regex("^🚀 تسجيل الدخول$"), self._register_start)
            ],
            states={
                ASK_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._register_username)],
                ASK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self._register_password)],
            },
            fallbacks=[CommandHandler("cancel", self._cancel_registration)],
        )
        logger.info("DEBUG: Registration conversation handler created successfully")
        return handler
    
    def _get_broadcast_handler(self):
        """Get broadcast conversation handler"""
        return self.broadcast_system.get_conversation_handler()
    
    # Standard keyboard helper methods
    async def _send_message_with_keyboard(self, update: Update, message: str, keyboard_type: str = "main"):
        """Standard method to send message with keyboard"""
        if keyboard_type == "main":
            keyboard = get_main_keyboard()
        elif keyboard_type == "relogin":
            keyboard = get_main_keyboard_with_relogin()
        elif keyboard_type == "admin":
            keyboard = get_admin_keyboard()
        elif keyboard_type == "cancel":
            keyboard = get_cancel_keyboard()
        else:
            keyboard = get_main_keyboard()
        
        await update.message.reply_text(message, reply_markup=keyboard)
    
    async def _edit_message_no_keyboard(self, message_obj, new_text: str):
        """Standard method to edit message without keyboard"""
        try:
            await message_obj.edit_text(new_text)
            return True
        except Exception as e:
            logger.error(f"DEBUG: Failed to edit message: {e}")
            return False
    
    async def _send_error_with_keyboard(self, update: Update, error_message: str, keyboard_type: str = "main"):
        """Standard method to send error message with keyboard"""
        await self._send_message_with_keyboard(update, error_message, keyboard_type)
    
    # Command handlers
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = get_welcome_message()
        
        await self._send_message_with_keyboard(update, welcome_message, "main")
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = get_help_message()
        
        await self._send_message_with_keyboard(update, help_message, "main")
    
    async def _register_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start registration process"""
        logger.info("DEBUG: _register_start called")
        
        # Clear any existing user data
        context.user_data.clear()
        
        await self._send_message_with_keyboard(
            update, 
            "🚀 **تسجيل الدخول للبوت الجامعي**\n\n"
            "📝 **أدخل اسم المستخدم الجامعي:**\n"
            "مثال: ENG2324901\n\n"
            "💡 **ملاحظة:** استخدم اسم المستخدم الخاص بك في نظام الجامعة",
            "cancel"
        )
        
        return ASK_USERNAME
    
    async def _register_username(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle username input"""
        logger.info("DEBUG: _register_username called")
        username = update.message.text.strip()
        logger.info(f"DEBUG: Username received: {username}")
        
        # Validate username
        if not username:
            await self._send_message_with_keyboard(
                update,
                "اسم المستخدم مطلوب. حاول مرة أخرى:",
                "cancel"
            )
            return ASK_USERNAME
        
        # Check username format (basic validation)
        if len(username) < 3 or len(username) > 20:
            await self._send_message_with_keyboard(
                update,
                "اسم المستخدم يجب أن يكون بين 3 و 20 حرف. حاول مرة أخرى:",
                "cancel"
            )
            return ASK_USERNAME
        
        # Check if username contains only allowed characters
        if not username.replace('-', '').replace('_', '').isalnum():
            await self._send_message_with_keyboard(
                update,
                "اسم المستخدم يجب أن يحتوي على أحرف وأرقام فقط. حاول مرة أخرى:",
                "cancel"
            )
            return ASK_USERNAME
        
        # Store username in context
        context.user_data["username"] = username
        
        await self._send_message_with_keyboard(
            update,
            f"تم حفظ اسم المستخدم: {username}\n\n"
            "أدخل كلمة المرور:",
            "cancel"
        )
        
        return ASK_PASSWORD
    
    async def _register_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle password input and complete registration"""
        logger.info("DEBUG: _register_password called")
        password = update.message.text.strip()
        logger.info(f"DEBUG: Password received (length: {len(password)})")
        
        if not password:
            await update.message.reply_text("❌ كلمة المرور غير صالحة، حاول مرة أخرى:")
            return ASK_PASSWORD
        
        username = context.user_data.get("username")
        telegram_id = update.effective_user.id
        logger.info(f"DEBUG: Attempting login for user {username} (ID: {telegram_id})")
        
        # Show loading message
        loading_message = await update.message.reply_text("🔄 جاري تسجيل الدخول...")
        
        try:
            # Login to university
            logger.info(f"DEBUG: Attempting university login for {username}")
            token = await self.university_api.login(username, password)
            if not token:
                logger.warning(f"DEBUG: Login failed for user {username}")
                await self._edit_message_no_keyboard(loading_message, 
                    "فشل تسجيل الدخول. تحقق من بياناتك.\n— THE DIE IS CAST · based on beehouse"
                )
                await self._send_message_with_keyboard(
                    update,
                    "اضغط '🚀 تسجيل الدخول' للمحاولة مرة أخرى",
                    "main"
                )
                return ConversationHandler.END
            
            logger.info(f"DEBUG: Login successful for user {username}, token received")
            await self._edit_message_no_keyboard(loading_message, "📊 جاري جلب بياناتك...")
            
            # Fetch user data
            logger.info(f"DEBUG: Fetching user data for {username}")
            user_data = await self.university_api.get_user_data(token)
            if not user_data:
                logger.warning(f"DEBUG: Failed to fetch user data for {username}")
                await self._edit_message_no_keyboard(loading_message,
                    "❌ **فشل جلب بيانات الطالب**\n\n"
                    "حاول لاحقاً أو تواصل مع الدعم الفني.\n\n"
                    "📞 **الدعم:**\n"
                    "• المطور: @sisp_t\n"
                    "• البريد الإلكتروني: abdulrahmanabdulkader59@gmail.com"
                )
                await self._send_message_with_keyboard(
                    update,
                    "🔙 اضغط على '🚀 تسجيل الدخول' للمحاولة مرة أخرى",
                    "main"
                )
                return ConversationHandler.END
            
            logger.info(f"DEBUG: User data fetched successfully for {username}")
            
            # Save user
            logger.info(f"DEBUG: Saving user data for {username}")
            try:
                self.user_storage.save_user(telegram_id, username, password, token, user_data)
                logger.info(f"DEBUG: User saved successfully for {username}")
            except Exception as save_error:
                logger.error(f"DEBUG: Failed to save user data: {save_error}")
                # If PostgreSQL fails, try to fall back to file storage
                if ("NumericValueOutOfRange" in str(save_error) or 
                    "integer out of range" in str(save_error) or
                    "psycopg2.errors.NumericValueOutOfRange" in str(save_error)):
                    logger.info("DEBUG: PostgreSQL integer overflow detected, falling back to file storage")
                    try:
                        # Initialize file storage as fallback
                        from storage.users import UserStorage
                        from storage.grades import GradeStorage
                        self.user_storage = UserStorage()
                        self.grade_storage = GradeStorage()
                        logger.info("DEBUG: File storage initialized as fallback")
                        
                        # Try saving again with file storage
                        self.user_storage.save_user(telegram_id, username, password, token, user_data)
                        logger.info(f"DEBUG: User saved successfully with file storage for {username}")
                    except Exception as file_error:
                        logger.error(f"DEBUG: File storage also failed: {file_error}")
                        raise
                else:
                    raise
            
            # Save grades
            logger.info(f"DEBUG: Saving grades for {username}")
            try:
                grades = user_data.get("grades", [])
                self.grade_storage.save_grades(telegram_id, grades)
                logger.info(f"DEBUG: Grades saved successfully for {username}")
            except Exception as grade_error:
                logger.error(f"DEBUG: Failed to save grades: {grade_error}")
                # If PostgreSQL fails, grades should already be saved with file storage above
                if not any(error_type in str(grade_error) for error_type in [
                    "NumericValueOutOfRange", 
                    "integer out of range", 
                    "psycopg2.errors.NumericValueOutOfRange"
                ]):
                    raise
            
            logger.info(f"DEBUG: Registration completed successfully for user {username}")
            
            # Registration successful
            logger.info(f"DEBUG: Registration successful for user {username}")
            await self._edit_message_no_keyboard(loading_message, 
                f"تم تسجيل الدخول بنجاح.\n\n"
                f"مرحباً {username}.\n\n"
                f"يمكنك الآن متابعة درجاتك.\n\n"
                f"— THE DIE IS CAST · based on beehouse"
            )
            # Send keyboard in a separate message
            await update.message.reply_text(
                "تم التسجيل. استخدم القائمة الرئيسية.",
                reply_markup=get_main_keyboard()
            )
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"DEBUG: Network error during login: {e}")
            await self._edit_message_no_keyboard(loading_message, 
                "خطأ في الاتصال. حاول لاحقاً.\n— THE DIE IS CAST · based on beehouse"
            )
            await self._send_message_with_keyboard(
                update,
                "اضغط '🚀 تسجيل الدخول' للمحاولة مرة أخرى",
                "main"
            )
            return ConversationHandler.END
    
    async def _cancel_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel registration"""
        await update.message.reply_text(
            "تم إلغاء العملية. يمكنك المحاولة مرة أخرى.\n— THE DIE IS CAST · based on beehouse",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
    
    async def _grades_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /grades command"""
        telegram_id = update.effective_user.id
        logger.info(f"DEBUG: Grades command called by user {telegram_id}")
        
        if not self.user_storage.is_user_registered(telegram_id):
            logger.warning(f"DEBUG: Unregistered user {telegram_id} tried to access grades")
            await update.message.reply_text(
                "سجل دخولك أولاً.\n— THE DIE IS CAST · based on beehouse",
                reply_markup=get_main_keyboard()
            )
            return
        
        # Show loading message
        loading_message = await update.message.reply_text("جاري فحص الدرجات...")
        
        try:
            # Get user session
            session = self.user_storage.get_user_session(telegram_id)
            if not session:
                logger.warning(f"DEBUG: No session found for user {telegram_id}")
                await self._edit_message_no_keyboard(loading_message,
                    "انتهت الجلسة. سجل دخولك مجدداً.\n— THE DIE IS CAST · based on beehouse"
                )
                await self._send_message_with_keyboard(
                    update,
                    "اضغط '🚀 تسجيل الدخول' لتجديد الجلسة",
                    "main"
                )
                return
            
            token = session.get("token")
            username = session.get("username")
            password = session.get("password")
            
            if not token:
                logger.warning(f"DEBUG: No token found for user {telegram_id}")
                await self._edit_message_no_keyboard(loading_message,
                    "انتهت الجلسة. سجل دخولك مجدداً.\n— THE DIE IS CAST · based on beehouse"
                )
                await self._send_message_with_keyboard(
                    update,
                    "اضغط '🚀 تسجيل الدخول' لتجديد الجلسة",
                    "main"
                )
                return
            
            # Test token validity
            logger.info(f"DEBUG: Testing token for user {username}")
            if not await self.university_api.test_token(token):
                logger.info(f"DEBUG: Token expired for user {username}, attempting relogin")
                await self._edit_message_no_keyboard(loading_message, "جاري تجديد الجلسة...")
                
                if not password:
                    logger.warning(f"DEBUG: No password stored for user {username}")
                    await self._edit_message_no_keyboard(loading_message,
                        "انتهت الجلسة. سجل دخولك مجدداً.\n— THE DIE IS CAST · based on beehouse"
                    )
                    await self._send_message_with_keyboard(
                        update,
                        "اضغط '🚀 تسجيل الدخول' لتجديد الجلسة",
                        "main"
                    )
                    return
                
                # Attempt relogin
                new_token = await self.university_api.login(username, password)
                if not new_token:
                    logger.warning(f"DEBUG: Relogin failed for user {username}")
                    await self._edit_message_no_keyboard(loading_message,
                        "فشل تجديد الجلسة. سجل دخولك مجدداً.\n— THE DIE IS CAST · based on beehouse"
                    )
                    await self._send_message_with_keyboard(
                        update,
                        "اضغط '🚀 تسجيل الدخول' لتجديد الجلسة",
                        "main"
                    )
                    return
                
                # Update token
                logger.info(f"DEBUG: Token refreshed for user {username}")
                self.user_storage.update_user_token(telegram_id, new_token)
                token = new_token
            
            # Fetch fresh grades
            logger.info(f"DEBUG: Fetching fresh grades for user {username}")
            await self._edit_message_no_keyboard(loading_message, "جاري جلب الدرجات...")
            
            user_data = await self.university_api.get_user_data(token)
            if not user_data:
                logger.warning(f"DEBUG: Failed to fetch user data for {username}")
                await self._edit_message_no_keyboard(loading_message,
                    "فشل جلب الدرجات. حاول لاحقاً.\n— THE DIE IS CAST · based on beehouse"
                )
                await self._send_message_with_keyboard(
                    update,
                    "اضغط '📊 عرض الدرجات' للمحاولة مرة أخرى",
                    "main"
                )
                return
            
            grades = user_data.get("grades", [])
            logger.info(f"DEBUG: Retrieved {len(grades)} grades for user {username}")
            
            # Save fresh grades
            try:
                self.grade_storage.save_grades(telegram_id, grades)
                logger.info(f"DEBUG: Grades saved successfully for user {username}")
            except Exception as save_error:
                logger.error(f"DEBUG: Failed to save grades: {save_error}")
                # Continue even if save fails
            
            # Display grades
            if not grades:
                await self._edit_message_no_keyboard(loading_message,
                    "لا توجد درجات متاحة حالياً.\n— THE DIE IS CAST · based on beehouse"
                )
                await self._send_message_with_keyboard(
                    update,
                    "اضغط '📊 عرض الدرجات' للمحاولة مرة أخرى",
                    "main"
                )
                return
            
            # Format grades message
            grades_text = f"📊 **درجاتك الحالية:**\n\n"
            for i, grade in enumerate(grades, 1):
                course_name = grade.get("المقرر", "غير محدد")
                course_code = grade.get("كود المادة", "")
                practical = grade.get("درجة الأعمال", "لم يتم النشر")
                theoretical = grade.get("درجة النظري", "لم يتم النشر")
                final = grade.get("الدرجة", "لم يتم النشر")
                
                grades_text += f"**{i}. {course_name}**"
                if course_code:
                    grades_text += f" ({course_code})"
                grades_text += f"\n"
                grades_text += f"• الأعمال: {practical}\n"
                grades_text += f"• النظري: {theoretical}\n"
                grades_text += f"• النهائي: {final}\n\n"
            
            grades_text += "— THE DIE IS CAST · based on beehouse"
            
            # Split message if too long
            if len(grades_text) > 4096:
                parts = [grades_text[i:i+4096] for i in range(0, len(grades_text), 4096)]
                for i, part in enumerate(parts):
                    if i == 0:
                        await self._edit_message_no_keyboard(loading_message, part)
                    else:
                        await update.message.reply_text(part)
            else:
                await self._edit_message_no_keyboard(loading_message, grades_text)
            
            await self._send_message_with_keyboard(
                update,
                "اضغط '📊 عرض الدرجات' لتحديث الدرجات",
                "main"
            )
            
        except Exception as e:
            logger.error(f"DEBUG: Error in grades command: {e}")
            await self._edit_message_no_keyboard(loading_message,
                "حدث خطأ أثناء جلب الدرجات. حاول لاحقاً.\n— THE DIE IS CAST · based on beehouse"
            )
            await self._send_message_with_keyboard(
                update,
                "اضغط '📊 عرض الدرجات' للمحاولة مرة أخرى",
                "main"
            )
    
    async def _profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /profile command"""
        telegram_id = update.effective_user.id
        user = self.user_storage.get_user(telegram_id)
        
        if not user:
            await update.message.reply_text(
                "❌ لم يتم تسجيلك بعد. اضغط على '🚀 تسجيل الدخول' أولاً.",
                reply_markup=get_main_keyboard()
            )
            return
        
        grades = self.grade_storage.get_grades(telegram_id)
        
        message = f"""
👤 **معلوماتك الشخصية:**

🆔 **معرف التلجرام:** {telegram_id}
👨‍🎓 **اسم المستخدم:** {user.get('username', 'غير محدد')}
📧 **البريد الإلكتروني:** {user.get('email', 'غير محدد')}
👤 **الاسم الكامل:** {user.get('fullname', 'غير محدد')}

📊 **عدد المواد:** {len(grades)}
🕒 **آخر تحديث:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        await update.message.reply_text(message, reply_markup=get_main_keyboard())
    
    async def _settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command"""
        telegram_id = update.effective_user.id
        users_count = len(self.user_storage.get_all_users())
        grades_count = len(self.grade_storage.get_grades(telegram_id)) if telegram_id else 0
        
        settings_message = f"""
⚙️ **إعدادات البوت**

🔧 **الإعدادات الحالية:**
• 🔔 الإشعارات: {'مفعلة' if CONFIG["ENABLE_NOTIFICATIONS"] else 'معطلة'}
• ⚠️ إشعارات الأخطاء: {'مفعلة' if CONFIG["ENABLE_ERROR_NOTIFICATIONS"] else 'معطلة'}
• 🔄 فترة الفحص: كل {CONFIG["GRADE_CHECK_INTERVAL"]} دقائق
• 🔁 عدد المحاولات: {CONFIG["MAX_RETRY_ATTEMPTS"]}

📊 **إحصائيات البوت:**
• 👥 عدد المستخدمين: {users_count}
• 📈 عدد المواد: {grades_count}

🔗 **معلومات الاتصال:**
• 👨‍💻 المطور: {CONFIG["ADMIN_USERNAME"]}
• 📧 البريد الإلكتروني: {CONFIG["ADMIN_EMAIL"]}
• 🌐 موقع الجامعة: {CONFIG["UNIVERSITY_WEBSITE"]}

هل تريد تغيير أي إعداد؟ ⚙️
"""
        
        await update.message.reply_text(settings_message, reply_markup=get_main_keyboard())
    
    async def _support_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /support command"""
        support_text = """
📞 **الدعم الفني:**

Developed by Abdulrahman Abdulkader
Email: abdulrahmanabdulkader59@gmail.com
username on other platforms: @sisp_t

🔧 **في حالة وجود مشاكل:**
1. تأكد من صحة بياناتك الجامعية
2. تحقق من اتصال الإنترنت
3. تواصل مع المطور

💬 **ساعات الدعم:** 24/7
"""
        
        await update.message.reply_text(support_text, reply_markup=get_main_keyboard())
    
    async def _stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command (admin only)"""
        if update.effective_user.id != CONFIG["ADMIN_ID"]:
            return
        
        stats = await self.admin_dashboard.get_stats()
        await update.message.reply_text(stats, reply_markup=get_admin_keyboard())
    
    async def _list_users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /list_users command (admin only)"""
        if update.effective_user.id != CONFIG["ADMIN_ID"]:
            return
        
        users_list = await self.admin_dashboard.get_users_list()
        await update.message.reply_text(users_list, reply_markup=get_admin_keyboard())
    
    async def _restart_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /restart command (admin only)"""
        if update.effective_user.id != CONFIG["ADMIN_ID"]:
            return
        
        await update.message.reply_text("🔄 جاري إعادة تشغيل البوت...")
        await update.message.reply_text("✅ تم إعادة تشغيل البوت بنجاح!", reply_markup=get_admin_keyboard())
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages and button clicks"""
        text = update.message.text
        
        if text == "🚀 تسجيل الدخول":
            await self._register_start(update, context)
        elif text == "🔄 إعادة تسجيل الدخول":
            # Force re-registration by invalidating session first
            telegram_id = update.effective_user.id
            if self.user_storage.is_user_registered(telegram_id):
                self.user_storage.invalidate_user_session(telegram_id)
            await self._register_start(update, context)
        elif text == "📊 فحص الدرجات":
            await self._grades_command(update, context)
        elif text == "👤 معلوماتي":
            await self._profile_command(update, context)
        elif text == "⚙️ الإعدادات":
            await self._settings_command(update, context)
        elif text == "❓ المساعدة":
            await self._help_command(update, context)
        elif text == "📞 الدعم":
            await self._support_command(update, context)
        elif text == "🎛️ لوحة التحكم" and update.effective_user.id == CONFIG["ADMIN_ID"]:
            await self.admin_dashboard.show_dashboard(update, context)
        elif text == "🔙 العودة":
            await self._start_command(update, context)
        else:
            await update.message.reply_text(
                "❓ لم أفهم طلبك. استخدم الأزرار أدناه أو اكتب /help للمساعدة.",
                reply_markup=get_main_keyboard()
            )
    
    async def _handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries"""
        query = update.callback_query
        await query.answer()
        
        if query.from_user.id != CONFIG["ADMIN_ID"]:
            return
        
        await self.admin_dashboard.handle_callback(update, context)
    
    async def _grade_checking_loop(self):
        """Main loop for checking grades"""
        while self.running:
            try:
                logger.info("🔄 Starting grade check cycle...")
                
                users = self.user_storage.get_all_users()
                for user in users:
                    await self._check_user_grades(user)
                
                logger.info(f"✅ Grade check completed. Next check in {CONFIG['GRADE_CHECK_INTERVAL']} minutes")
                
                # Wait for next check
                await asyncio.sleep(CONFIG["GRADE_CHECK_INTERVAL"] * 60)
                
            except asyncio.CancelledError:
                logger.info("🛑 Grade checking task cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Error in grade checking: {e}")
                await asyncio.sleep(300)  # 5 minutes
    
    async def _check_user_grades(self, user):
        """Check grades for a specific user using stored token"""
        try:
            telegram_id = user.get("telegram_id")
            username = user.get("username")
            token = user.get("token")
            
            logger.info(f"🔍 DEBUG: Starting grade check for user {username} (ID: {telegram_id})")
            logger.info(f"🔑 DEBUG: User has token: {'Yes' if token else 'No'}")
            
            # Check if user has a valid token
            if not token:
                logger.warning(f"❌ DEBUG: No token found for user {username}, skipping grade check")
                return
            
            # Test if token is still valid
            logger.info(f"🔍 DEBUG: Testing token validity for user {username}")
            if not await self.university_api.test_token(token):
                logger.warning(f"⚠️ DEBUG: Token expired for user {username}, attempting re-authentication")
                
                # Try to re-authenticate using stored credentials
                password = user.get("password")
                if not password:
                    logger.error(f"❌ DEBUG: No password stored for user {username}, cannot re-authenticate")
                    return
                
                logger.info(f"🔄 DEBUG: Re-authenticating user {username} with stored credentials")
                new_token = await self.university_api.login(username, password)
                if new_token:
                    logger.info(f"✅ DEBUG: Re-authentication successful for user {username}")
                    token = new_token
                    # Update token in database
                    self.user_storage.update_user_token(telegram_id, token)
                else:
                    logger.error(f"❌ DEBUG: Re-authentication failed for user {username}")
                    return
            else:
                logger.info(f"✅ DEBUG: Token is valid for user {username}")
            
            # Get fresh grades using token
            logger.info(f"📊 DEBUG: Fetching fresh grades for user {username} using token")
            user_data = await self.university_api.get_user_data(token)
            if not user_data:
                logger.warning(f"❌ DEBUG: Failed to fetch data for user {username}")
                return
            
            new_grades = user_data.get("grades", [])
            logger.info(f"📚 DEBUG: Retrieved {len(new_grades)} grades for user {username}")
            
            # Get previous grades for comparison
            old_grades = self.grade_storage.get_grades(telegram_id)
            logger.info(f"📚 DEBUG: Previous grades count: {len(old_grades)}")
            
            # Compare grades
            if old_grades != new_grades:
                logger.info(f"🔄 DEBUG: Grades changed for user {username}")
                
                # Find specific changes
                changes = []
                for new_grade in new_grades:
                    course_name = new_grade.get("المقرر", "")
                    old_grade = next((g for g in old_grades if g.get("المقرر") == course_name), None)
                    
                    if not old_grade or old_grade != new_grade:
                        changes.append(new_grade)
                        logger.info(f"📝 DEBUG: Grade change detected for course '{course_name}'")
                
                logger.info(f"📊 DEBUG: Found {len(changes)} grade changes for user {username}")
                
                if changes:
                    # Notify user about changes
                    message = "🎓 **تم تحديث درجاتك:**\n\n"
                    for grade in changes:
                        # Safely extract all fields with proper validation
                        course_name = grade.get('المقرر', 'غير محدد')
                        course_code = grade.get('كود المادة', '')
                        practical_grade = grade.get('درجة الأعمال', 'لم يتم النشر')
                        theoretical_grade = grade.get('درجة النظري', 'لم يتم النشر')
                        final_grade = grade.get('الدرجة', 'لم يتم النشر')
                        
                        # Validate and clean the data
                        course_name = course_name.strip() if course_name else 'غير محدد'
                        course_code = course_code.strip() if course_code else ''
                        practical_grade = practical_grade.strip() if practical_grade else 'لم يتم النشر'
                        theoretical_grade = theoretical_grade.strip() if theoretical_grade else 'لم يتم النشر'
                        final_grade = final_grade.strip() if final_grade else 'لم يتم النشر'
                        
                        message += f"📚 **{course_name}**\n"
                        if course_code and course_code != '':
                            message += f"   🏷️ الكود: {course_code}\n"
                        message += f"   🔬 درجة الأعمال: {practical_grade}\n"
                        message += f"   ✍️ درجة النظري: {theoretical_grade}\n"
                        message += f"   🎯 الدرجة النهائية: {final_grade}\n\n"
                    
                    try:
                        await self.app.bot.send_message(chat_id=telegram_id, text=message)
                        logger.info(f"✅ DEBUG: Grade update notification sent to user {username}")
                    except Exception as e:
                        logger.error(f"❌ DEBUG: Failed to send grade update to user {username}: {e}")
                
                # Save new grades
                logger.info(f"💾 DEBUG: Saving updated grades for user {username}")
                self.grade_storage.save_grades(telegram_id, new_grades)
            else:
                logger.info(f"✅ DEBUG: No grade changes detected for user {username} - grades are the same as previous")
                
        except Exception as e:
            logger.error(f"❌ DEBUG: Error checking grades for user {user.get('username', 'unknown')}: {e}")
    
    async def _log_any_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Log any incoming update for debugging"""
        try:
            update_type = "Unknown"
            user_info = "Unknown"
            
            if update.message:
                update_type = "Message"
                user_info = f"ID: {update.effective_user.id}, Username: {update.effective_user.username}, Text: {update.message.text[:50]}..."
            elif update.callback_query:
                update_type = "Callback Query"
                user_info = f"ID: {update.effective_user.id}, Username: {update.effective_user.username}, Data: {update.callback_query.data}"
            elif update.edited_message:
                update_type = "Edited Message"
                user_info = f"ID: {update.effective_user.id}, Username: {update.effective_user.username}"
            
            logger.info(f"DEBUG: Received {update_type} update - {user_info}")
            
        except Exception as e:
            logger.error(f"DEBUG: Error logging update: {e}")
            logger.info(f"DEBUG: Raw update: {update}") 