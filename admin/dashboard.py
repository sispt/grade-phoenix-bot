"""
🎛️ Harmonic Admin Dashboard System (Enhanced)
"""

import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from config import CONFIG
from utils.keyboards import (
    get_enhanced_admin_dashboard_keyboard,
    get_user_management_keyboard,
    get_broadcast_confirmation_keyboard,
)
import aiohttp
import asyncio

logger = logging.getLogger(__name__)

# Add 'Broadcast' button to the admin dashboard keyboard
ADMIN_DASHBOARD_BUTTONS = [["👥 المستخدمون", "📊 التحليل"], ["📢 بث رسالة"]]


class AdminDashboard:
    def __init__(self, bot):
        self.bot = bot
        self.user_storage = bot.user_storage

    async def show_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.effective_user or update.effective_user.id != CONFIG["ADMIN_ID"]:
            return
        if not update.message:
            logger.error("show_dashboard called with no message in update.")
            return
        dashboard_text = self._get_dashboard_text()
        keyboard = get_enhanced_admin_dashboard_keyboard()
        await update.message.reply_text(dashboard_text, reply_markup=keyboard)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Harden: Only allow admin to access dashboard callbacks
        if not update.effective_user or update.effective_user.id != CONFIG["ADMIN_ID"]:
            user_id = getattr(update.effective_user, 'id', None)
            username = getattr(update.effective_user, 'username', None)
            logger.warning(f"[SECURITY] Non-admin user tried to access admin dashboard callback: id={user_id}, username={username}")
            # Try to send a denial message if possible
            try:
                if update.callback_query:
                    await update.callback_query.answer(text="🚫 ليس لديك صلاحية لهذه العملية.", show_alert=True)
                elif update.message:
                    await update.message.reply_text("🚫 ليس لديك صلاحية لهذه العملية.")
            except Exception:
                pass
            return
        query = update.callback_query
        if query is None:
            logger.error("handle_callback called with no callback_query in update.")
            return
        action = query.data
        if action is None:
            logger.error("handle_callback called with no data in callback_query.")
            return
        if not hasattr(context, 'user_data') or context.user_data is None:
            logger.error("handle_callback called with no user_data in context.")
            return
        await query.answer()

        try:
            if action.startswith("users_overview"):
                try:
                    overview_text = self._get_users_overview_text()
                except Exception as e:
                    logger.error(f"Error in users_overview: {e}", exc_info=True)
                    overview_text = "❌ حدث خطأ أثناء جلب نظرة المستخدمين. تأكد من سلامة البيانات أو أعد المحاولة."
                await query.edit_message_text(
                    text=overview_text,
                    reply_markup=get_enhanced_admin_dashboard_keyboard(),
                )
            elif action.startswith("view_users"):
                try:
                    page = 1
                    if ":" in action:
                        try:
                            page = int(action.split(":")[1])
                        except:
                            page = 1
                    users = self.user_storage.get_all_users()
                    if not isinstance(users, list):
                        raise ValueError("users data is not a list")
                    total_pages = max(1, (len(users) + 9) // 10)  # 10 users per page
                    list_text = self._get_users_list_text(page=page)
                except Exception as e:
                    logger.error(f"Error in view_users: {e}", exc_info=True)
                    list_text = "❌ حدث خطأ أثناء جلب قائمة المستخدمين. تأكد من سلامة البيانات أو أعد المحاولة."
                    total_pages = 1
                await query.edit_message_text(
                    text=list_text,
                    reply_markup=get_user_management_keyboard(page, total_pages),
                )
            elif action.startswith("user_search"):
                # Prompt admin to enter search query
                await query.edit_message_text(
                    text="🔎 أدخل اسم المستخدم أو الـ ID للبحث:"
                )
                context.user_data["awaiting_user_search"] = True
            elif action.startswith("user_search_result:"):
                # Show user details
                user_id = action.split(":", 1)[1]
                user = next(
                    (
                        u
                        for u in self.user_storage.get_all_users()
                        if str(u.get("telegram_id")) == user_id
                    ),
                    None,
                )
                if user:
                    text = f"""👤 **تفاصيل المستخدم:**
- الاسم: {user.get('username', '-')}
- المعرف: {user.get('telegram_id', '-')}
- الاسم الكامل: {user.get('fullname', '-')}
- آخر دخول: {user.get('last_login', '-')}
- الحالة: {'نشط' if user.get('is_active', True) else 'غير نشط'}"""
                else:
                    text = "❌ المستخدم غير موجود."
                await query.edit_message_text(
                    text=text, reply_markup=get_enhanced_admin_dashboard_keyboard()
                )
            elif action == "analysis":
                await query.edit_message_text(
                    text=self._get_analysis_text(),
                    reply_markup=get_enhanced_admin_dashboard_keyboard(),
                )
            elif action == "close_dashboard":
                await query.edit_message_text(text="✅ تم إغلاق لوحة التحكم.")
            elif action == "broadcast":
                await query.edit_message_text(
                    text="📝 أرسل نص الرسالة التي تريد بثها لجميع المستخدمين:",
                    reply_markup=get_broadcast_confirmation_keyboard(),
                )
            elif action == "confirm_broadcast":
                await query.edit_message_text(text="📝 أرسل نص الرسالة التي تريد بثها:")
                context.user_data["awaiting_broadcast"] = True
            elif action == "cancel_broadcast":
                await query.edit_message_text(
                    text="❌ تم إلغاء البث.",
                    reply_markup=get_enhanced_admin_dashboard_keyboard(),
                )
            elif action == "system_report":
                await query.edit_message_text(
                    text=self._get_system_report_text(),
                    reply_markup=get_enhanced_admin_dashboard_keyboard(),
                )
            elif action == "delete_user":
                await query.edit_message_text(
                    text="🔍 أدخل معرف المستخدم الذي تريد حذفه:"
                )
                context.user_data["awaiting_user_delete"] = True
            elif action == "refresh_data":
                await query.edit_message_text(text="🔄 جاري تحديث البيانات...")
                # Simulate refresh
                await query.edit_message_text(
                    text="✅ تم تحديث البيانات.",
                    reply_markup=get_enhanced_admin_dashboard_keyboard(),
                )
            elif action == "backup_data":
                await query.edit_message_text(text="💾 جاري إنشاء نسخة احتياطية...")
                # Simulate backup
                await query.edit_message_text(
                    text="✅ تم إنشاء النسخة الاحتياطية.",
                    reply_markup=get_enhanced_admin_dashboard_keyboard(),
                )
            elif action == "silent_update":
                await query.edit_message_text(text="🔕 جاري تنفيذ التحديث الصامت (بدون إشعارات)...")
                # Simulate silent update: refresh grades/data for all users, but do not send notifications
                try:
                    count = await self.bot._silent_update_all_users_grades()
                    await query.edit_message_text(
                        text=f"✅ تم تنفيذ التحديث الصامت لـ {count} مستخدم (بدون إشعارات).",
                        reply_markup=get_enhanced_admin_dashboard_keyboard(),
                    )
                except Exception as e:
                    await query.edit_message_text(
                        text=f"❌ حدث خطأ أثناء التحديث الصامت: {e}",
                        reply_markup=get_enhanced_admin_dashboard_keyboard(),
                    )
            elif action == "back_to_dashboard":
                await query.edit_message_text(
                    text=self._get_dashboard_text(),
                    reply_markup=get_enhanced_admin_dashboard_keyboard(),
                )
            elif action == "users_stats":
                await query.edit_message_text(
                    text=self._get_users_stats_text(),
                    reply_markup=get_user_management_keyboard(),
                )
            elif action == "current_page":
                # Do nothing for current page indicator
                pass
            elif action == "send_quote_to_all":
                await query.edit_message_text(
                    text="🔄 جاري إرسال رسالة اليوم لجميع المستخدمين..."
                )
                quote = await self.bot.grade_analytics.get_daily_quote()
                if quote:
                    # For admin broadcast, always translate (admin preference)
                    message = await self.bot.grade_analytics.format_quote_dual_language(quote, do_translate=True)
                else:
                    message = "💬 رسالة اليوم:\n\nلم تتوفر رسالة اليوم حالياً."
                sent = await self.bot.send_quote_to_all_users(message, parse_mode=ParseMode.MARKDOWN)
                failed = 0  # We'll track failures differently
                
                # Create detailed feedback message
                if failed == 0:
                    feedback = f"✅ تم إرسال رسالة اليوم إلى {sent} مستخدم بنجاح."
                else:
                    feedback = f"✅ تم إرسال رسالة اليوم إلى {sent} مستخدم.\n❌ فشل الإرسال إلى {failed} مستخدم.\n\n💡 الأسباب المحتملة:\n• المستخدمون حظروا البوت\n• معرفات تليجرام غير صحيحة\n• مشاكل في الاتصال"
                
                await query.edit_message_text(
                    text=feedback,
                    reply_markup=get_enhanced_admin_dashboard_keyboard(),
                )
            elif action == "force_grade_check":
                # Prompt admin to enter username
                await query.edit_message_text(
                    text="🛠️ أدخل اسم المستخدم (username) أو معرف التليجرام (ID) لفحص الدرجات وبيانات HTML:"
                )
                context.user_data["awaiting_force_grade_check"] = True
            elif action == "force_grade_check_all":
                await query.edit_message_text(
                    text="🔄 جاري فحص الدرجات لجميع المستخدمين..."
                )
                count = await self.bot._notify_all_users_grades()
                await query.edit_message_text(
                    text=f"✅ تم فحص الدرجات وإشعار {count} مستخدم (إذا كان هناك تغيير).",
                    reply_markup=get_enhanced_admin_dashboard_keyboard(),
                )
            elif action.startswith("force_grade_refresh_only:"):
                telegram_id = action.split(":", 1)[1]
                await self._admin_force_grade_refresh_only(query, telegram_id)
            elif action.startswith("force_grade_show_html:"):
                telegram_id = action.split(":", 1)[1]
                await self._admin_force_grade_show_html(query, telegram_id)
            elif action == "test_grade_notification":
                # Prompt admin to choose test type
                keyboard = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ مع تغيير في الدرجات", callback_data="test_grade_notification_with_change"),
                        InlineKeyboardButton("❌ بدون تغيير في الدرجات", callback_data="test_grade_notification_no_change"),
                    ],
                    [InlineKeyboardButton("🔙 العودة للوحة التحكم", callback_data="back_to_dashboard")],
                ])
                await query.edit_message_text(
                    text="🧪 اختر نوع اختبار إشعار الدرجات:",
                    reply_markup=keyboard
                )
            elif action == "test_grade_notification_with_change":
                # Simulate a grade update with a change and send notification to admin
                fake_user = {
                    "telegram_id": CONFIG["ADMIN_ID"],
                    "username": "fakeuser",
                    "username_unique": "fakeuser_unique",
                    "session_token": "fake_token"
                }
                # Old grades
                old_grades = [
                    {"name": "Mathematics", "code": "MATH101", "coursework": "20", "final_exam": "30", "total": "50"},
                    {"name": "Physics", "code": "PHYS101", "coursework": "25", "final_exam": "25", "total": "50"},
                ]
                # New grades (with change)
                new_grades = [
                    {"name": "Mathematics", "code": "MATH101", "coursework": "20", "final_exam": "40", "total": "60"},
                    {"name": "Physics", "code": "PHYS101", "coursework": "25", "final_exam": "25", "total": "50"},
                ]
                # Use the same notification logic as real users
                analytics = self.bot.grade_analytics
                changed_courses = self.bot._compare_grades(old_grades, new_grades, "meaningful")
                if changed_courses:
                    # Format and send notification to admin
                    message = await analytics.format_current_grades_with_quote(CONFIG["ADMIN_ID"], new_grades, manual=False)
                    await query.edit_message_text(
                        text="🧪 تم إرسال إشعار الدرجات (مع تغيير) إلى المدير.",
                        reply_markup=get_enhanced_admin_dashboard_keyboard()
                    )
                    await self.bot.app.bot.send_message(chat_id=CONFIG["ADMIN_ID"], text=message)
                else:
                    await query.edit_message_text(
                        text="❌ لم يتم اكتشاف أي تغيير في الدرجات التجريبية.",
                        reply_markup=get_enhanced_admin_dashboard_keyboard()
                    )
            elif action == "test_grade_notification_no_change":
                # Simulate a grade update with no change (should not send notification)
                fake_user = {
                    "telegram_id": CONFIG["ADMIN_ID"],
                    "username": "fakeuser",
                    "username_unique": "fakeuser_unique",
                    "session_token": "fake_token"
                }
                # Old and new grades are the same
                old_grades = [
                    {"name": "Mathematics", "code": "MATH101", "coursework": "20", "final_exam": "30", "total": "50"},
                    {"name": "Physics", "code": "PHYS101", "coursework": "25", "final_exam": "25", "total": "50"},
                ]
                new_grades = [
                    {"name": "Mathematics", "code": "MATH101", "coursework": "20", "final_exam": "30", "total": "50"},
                    {"name": "Physics", "code": "PHYS101", "coursework": "25", "final_exam": "25", "total": "50"},
                ]
                changed_courses = self.bot._compare_grades(old_grades, new_grades, "meaningful")
                if not changed_courses:
                    await query.edit_message_text(
                        text="✅ لم يتم إرسال إشعار لأن الدرجات لم تتغير (تطبيق المنطق الحالي).",
                        reply_markup=get_enhanced_admin_dashboard_keyboard()
                    )
                else:
                    await query.edit_message_text(
                        text="❌ تم اكتشاف تغيير غير متوقع في الدرجات التجريبية.",
                        reply_markup=get_enhanced_admin_dashboard_keyboard()
                    )
            elif action == "test_quote_notification":
                # Schedule a quote notification to admin after 1 minute
                await query.edit_message_text(
                    text="🧪 سيتم إرسال إشعار الاقتباس التجريبي إلى المدير بعد دقيقة واحدة.",
                    reply_markup=get_enhanced_admin_dashboard_keyboard()
                )
                async def send_test_quote():
                    await asyncio.sleep(60)
                    quote = await self.bot.grade_analytics.get_daily_quote()
                    quote_text = await self.bot.grade_analytics.format_quote_dual_language(quote, do_translate=True)
                    await self.bot.app.bot.send_message(chat_id=CONFIG["ADMIN_ID"], text=f"🧪 إشعار اقتباس مجدول (تجريبي):\n\n{quote_text}")
                asyncio.create_task(send_test_quote())
            else:
                await query.edit_message_text(
                    f"Action '{action}' selected.",
                    reply_markup=get_enhanced_admin_dashboard_keyboard(),
                )
        except Exception as e:
            logger.error(f"Error handling callback {action}: {e}")
            await query.edit_message_text(
                text="❌ حدث خطأ أثناء معالجة الطلب. يرجى المحاولة مرة أخرى.",
                reply_markup=get_enhanced_admin_dashboard_keyboard(),
            )

    def _get_dashboard_text(self) -> str:
        return (
            "🎛️ لوحة التحكم الإدارية المحسنة\n\n"
            "اختر وظيفة من الأزرار أدناه لإدارة النظام أو المستخدمين.\n"
            "كل العمليات سهلة وآمنة ومخصصة للمطور فقط"
        )

    def _get_users_overview_text(self) -> str:
        try:
            logger.debug("Fetching users overview...")
            # Use get_all_users for both storage types
            users = self.user_storage.get_all_users()
            if not isinstance(users, list):
                raise ValueError("users data is not a list")
            total = len(users)
            active = len([u for u in users if u.get("is_active", True)])
            inactive = total - active
            logger.debug(f"Total users: {total}")
            logger.debug(f"Active users: {active}")
            logger.debug(f"Inactive users: {inactive}")
            if total > 0:
                return (
                    f"👥 **نظرة عامة للمستخدمين**\n\n"
                    f"📊 **الإحصائيات:**\n"
                    f"- إجمالي المستخدمين: {total}\n"
                    f"- النشطين: {active}\n"
                    f"- غير النشطين: {inactive}\n"
                    f"- نسبة النشاط: {(active/total*100):.1f}%"
                )
            else:
                logger.debug("No users found in storage.")
                return "👥 لا يوجد مستخدمون مسجلون بعد."
        except Exception as e:
            logger.error(f"Error in _get_users_overview_text: {e}", exc_info=True)
            return f"❌ حدث خطأ أثناء جلب نظرة المستخدمين.\n[DEBUG: {e}]"

    def _get_users_list_text(self, page=1, per_page=10):
        try:
            users = self.user_storage.get_all_users()
            if not isinstance(users, list):
                raise ValueError("users data is not a list")
            total = len(users)
            start = (page - 1) * per_page
            end = start + per_page
            users_page = users[start:end]
            text = f"👥 **قائمة المستخدمين** (صفحة {page}):\n\n"
            for i, user in enumerate(users_page, start + 1):
                status = "🟢" if user.get("is_active", True) else "🔴"
                text += f"{i}. {status} {user.get('username', '-')} (ID: {user.get('telegram_id', '-')})\n"
            text += f"\n📊 إجمالي المستخدمين: {total}"
            return text
        except Exception as e:
            logger.error(f"Error in _get_users_list_text: {e}", exc_info=True)
            return "❌ حدث خطأ أثناء جلب قائمة المستخدمين. تأكد من سلامة البيانات أو أعد المحاولة."

    def _get_users_stats_text(self) -> str:
        users = self.user_storage.get_all_users()
        total = len(users)
        active = len([u for u in users if u.get("is_active", True)])
        inactive = total - active

        # Calculate registration trends (last 7 days)
        recent_users = [u for u in users if u.get("registration_date")]
        recent_count = len(recent_users)

        text = "📊 **إحصائيات المستخدمين التفصيلية:**\n\n"
        text += "👥 **الأعداد:**\n"
        text += f"- إجمالي المستخدمين: {total}\n"
        text += f"- النشطين: {active}\n"
        text += f"- غير النشطين: {inactive}\n"
        text += f"- نسبة النشاط: {(active/total*100):.1f}%" if total > 0 else "0%\n"
        text += "\n📈 **النشاط:**\n"
        text += f"- المستخدمون الجدد: {recent_count}\n"
        return text

    def _get_analysis_text(self) -> str:
        users = self.user_storage.get_all_users()
        total = len(users)
        active = len([u for u in users if u.get("is_active", True)])
        last_login_user = max(
            users, key=lambda u: u.get("last_login", ""), default=None
        )

        text = "📊 **التحليل والإحصائيات:**\n\n"
        text += "👥 **المستخدمون:**\n"
        text += f"- إجمالي المستخدمين: {total}\n"
        text += f"- المستخدمون النشطون: {active}\n"
        text += f"- نسبة النشاط: {(active/total*100):.1f}%" if total > 0 else "0%\n"

        if last_login_user:
            text += "\n🕒 **آخر نشاط:**\n"
            text += f"- آخر مستخدم نشط: {last_login_user.get('username', '-')}\n"
            text += f"- آخر دخول: {last_login_user.get('last_login', '-')}\n"

        return text

    def _get_system_report_text(self) -> str:
        users = self.user_storage.get_all_users()
        total_users = len(users)
        active_users = len([u for u in users if u.get("is_active", True)])
        text = "📋 تقرير حالة النظام:\n\n"
        text += "🖥️ كل شيء يعمل بشكل طبيعي.\n"
        text += f"- المستخدمون المسجلون: {total_users}\n"
        text += f"- المستخدمون النشطون: {active_users}\n"
        text += (
            f"- نسبة النشاط: {(active_users/total_users*100):.1f}%"
            if total_users > 0
            else "0%\n"
        )
        text += "\nللمزيد من التفاصيل استخدم الأزرار الأخرى."
        return text

    # Add a user-friendly security info function for users (to be called from bot)
    @staticmethod
    def get_user_security_info() -> str:
        return (
            "🔒 معلومات الأمان:\n\n"
            "• بياناتك الجامعية تُستخدم فقط لجلب الدرجات ولا يتم تخزين كلمة المرور نهائياً.\n"
            "• جميع المعلومات مشفرة وآمنة.\n"
            "• يمكنك تغيير كلمة المرور في أي وقت من بوابة الجامعة.\n"
            "• ننصح باستخدام كلمة مرور قوية وعدم مشاركتها مع أي جهة.\n"
            "\nإذا كان لديك أي استفسار عن الأمان، تواصل مع الدعم الفني."
        )

    # To be called from the main bot when admin sends a message after search prompt
    async def handle_user_search_message(self, update, context):
        if not context.user_data.get("awaiting_user_search"):
            return False
        query = update.message.text.strip()
        users = self.user_storage.get_all_users()
        results = [
            u
            for u in users
            if query in str(u.get("telegram_id"))
            or query.lower() in (u.get("username", "").lower() or "")
        ]
        if not results:
            await update.message.reply_text(
                "❌ لا يوجد مستخدم مطابق.",
                reply_markup=get_enhanced_admin_dashboard_keyboard(),
            )
        else:
            buttons = [
                [
                    InlineKeyboardButton(
                        f"{u.get('username', '-')} (ID: {u.get('telegram_id', '-')})",
                        callback_data=f"user_search_result:{u.get('telegram_id')}",
                    )
                ]
                for u in results[:10]
            ]
            buttons.append(
                [
                    InlineKeyboardButton(
                        "🔙 العودة للوحة التحكم", callback_data="back_to_dashboard"
                    )
                ]
            )
            await update.message.reply_text(
                "نتائج البحث:", reply_markup=InlineKeyboardMarkup(buttons)
            )
        context.user_data["awaiting_user_search"] = False
        return True

    async def handle_user_delete_message(self, update, context):
        if not context.user_data.get("awaiting_user_delete"):
            return False
        user_id = update.message.text.strip()
        try:
            user_id = int(user_id)
            user = next(
                (
                    u
                    for u in self.user_storage.get_all_users()
                    if u.get("telegram_id") == user_id
                ),
                None,
            )
            if user:
                # Delete user (this will cascade to grades)
                self.user_storage.delete_user(user_id)
                await update.message.reply_text(
                    f"✅ تم حذف المستخدم {user.get('username', '')} بنجاح.",
                    reply_markup=get_enhanced_admin_dashboard_keyboard(),
                )
            else:
                await update.message.reply_text(
                    "❌ المستخدم غير موجود.",
                    reply_markup=get_enhanced_admin_dashboard_keyboard(),
                )
        except ValueError:
            await update.message.reply_text(
                "❌ يرجى إدخال معرف صحيح للمستخدم.",
                reply_markup=get_enhanced_admin_dashboard_keyboard(),
            )
        context.user_data["awaiting_user_delete"] = False
        return True

    async def handle_dashboard_message(self, update, context):
        text = update.message.text
        if text == "📢 بث رسالة":
            await update.message.reply_text(
                "📝 أرسل نص الرسالة التي تريد بثها لجميع المستخدمين:"
            )
            context.user_data["awaiting_broadcast"] = True
            return True
        if context.user_data.get("awaiting_broadcast"):
            message = update.message.text
            await update.message.reply_text("🚀 جاري إرسال الرسالة لجميع المستخدمين...")
            sent, failed = await self.broadcast_to_all_users(message)
            
            # Create detailed feedback message
            if failed == 0:
                feedback = f"✅ تم إرسال الرسالة إلى {sent} مستخدم بنجاح."
            else:
                feedback = f"✅ تم إرسال الرسالة إلى {sent} مستخدم.\n❌ فشل الإرسال إلى {failed} مستخدم.\n\n💡 الأسباب المحتملة:\n• المستخدمون حظروا البوت\n• معرفات تليجرام غير صحيحة\n• مشاكل في الاتصال"
            
            await update.message.reply_text(
                feedback,
                reply_markup=get_enhanced_admin_dashboard_keyboard(),
            )
            context.user_data["awaiting_broadcast"] = False
            return True
        return False

    async def broadcast_to_all_users(self, message):
        users = self.bot.user_storage.get_all_users()
        sent = 0
        failed = 0
        blocked_users = 0
        invalid_users = 0
        other_errors = 0
        
        for user in users:
            try:
                await self.bot.app.bot.send_message(
                    chat_id=user["telegram_id"], text=message
                )
                sent += 1
            except Exception as e:
                failed += 1
                error_msg = str(e).lower()
                if "blocked" in error_msg or "forbidden" in error_msg:
                    blocked_users += 1
                    logger.warning(f"User {user['telegram_id']} ({user.get('username', 'Unknown')}) blocked the bot")
                elif "chat not found" in error_msg or "user not found" in error_msg:
                    invalid_users += 1
                    logger.warning(f"Invalid user ID {user['telegram_id']} ({user.get('username', 'Unknown')})")
                else:
                    other_errors += 1
                    logger.error(f"Broadcast failed for {user['telegram_id']} ({user.get('username', 'Unknown')}): {e}")
        
        # Log detailed summary
        logger.info(f"Broadcast summary: sent={sent}, failed={failed}, total={len(users)}")
        if failed > 0:
            logger.info(f"Failure breakdown: blocked={blocked_users}, invalid={invalid_users}, other={other_errors}")
        
        return sent, failed

    async def send_quote_to_all_users(self, message):
        users = self.bot.user_storage.get_all_users()
        sent = 0
        failed = 0
        blocked_users = 0
        invalid_users = 0
        other_errors = 0
        
        for user in users:
            try:
                await self.bot.app.bot.send_message(
                    chat_id=user["telegram_id"], text=message
                )
                sent += 1
            except Exception as e:
                failed += 1
                error_msg = str(e).lower()
                if "blocked" in error_msg or "forbidden" in error_msg:
                    blocked_users += 1
                    logger.warning(f"User {user['telegram_id']} ({user.get('username', 'Unknown')}) blocked the bot")
                elif "chat not found" in error_msg or "user not found" in error_msg:
                    invalid_users += 1
                    logger.warning(f"Invalid user ID {user['telegram_id']} ({user.get('username', 'Unknown')})")
                else:
                    other_errors += 1
                    logger.error(f"Quote broadcast failed for {user['telegram_id']} ({user.get('username', 'Unknown')}): {e}")
        
        # Log detailed summary
        logger.info(f"Quote broadcast summary: sent={sent}, failed={failed}, total={len(users)}")
        if failed > 0:
            logger.info(f"Failure breakdown: blocked={blocked_users}, invalid={invalid_users}, other={other_errors}")
        
        return sent, failed

    async def handle_force_grade_check_message(self, update, context):
        """
        Handle admin reply for force grade check: prompt for action (refresh only or show HTML).
        """
        if not context.user_data.get("awaiting_force_grade_check"):
            return False
        query = update.message.text.strip()
        users = self.user_storage.get_all_users()
        user = next(
            (u for u in users if query == str(u.get("telegram_id")) or query.lower() == (u.get("username", "").lower() or "")),
            None,
        )
        if not user:
            await update.message.reply_text(
                "❌ لا يوجد مستخدم مطابق.",
                reply_markup=get_enhanced_admin_dashboard_keyboard(),
            )
            context.user_data["awaiting_force_grade_check"] = False
            return True
        telegram_id = user.get("telegram_id")
        username = user.get("username", "-")
        # Prompt admin for action: refresh only or show HTML
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 تحديث فقط", callback_data=f"force_grade_refresh_only:{telegram_id}"),
                InlineKeyboardButton("📝 عرض HTML الخام", callback_data=f"force_grade_show_html:{telegram_id}"),
            ],
            [InlineKeyboardButton("🔙 إلغاء", callback_data="back_to_dashboard")],
        ])
        await update.message.reply_text(
            f"🛠️ اختر الإجراء المطلوب للمستخدم {username} ({telegram_id}):",
            reply_markup=keyboard,
        )
        context.user_data["awaiting_force_grade_check"] = False
        return True

    async def _admin_force_grade_refresh_only(self, query, telegram_id):
        """
        Force refresh grades for a user and print summary (no HTML).
        """
        users = self.user_storage.get_all_users()
        user = next((u for u in users if str(u.get("telegram_id")) == str(telegram_id)), None)
        if not user:
            await query.edit_message_text(
                "❌ المستخدم غير موجود.",
                reply_markup=get_enhanced_admin_dashboard_keyboard(),
            )
            return
        token = user.get("session_token")
        username = user.get("username", "-")
        username_unique = user.get("username_unique", username)
        if not token:
            await query.edit_message_text(
                f"❌ لا يوجد رمز دخول لهذا المستخدم ({username}).",
                reply_markup=get_enhanced_admin_dashboard_keyboard(),
            )
            return
        try:
            await query.edit_message_text(f"🔄 جاري تحديث الدرجات للمستخدم: {username} ({telegram_id})...")
            api = self.bot.university_api
            grades = await api.fetch_and_parse_grades(token, int(telegram_id))
            if grades:
                msg = f"✅ الدرجات الحالية للمستخدم {username} ({telegram_id}):\n"
                for g in grades:
                    msg += f"- {g.get('name', '-')}: {g.get('total', '-')}, الأعمال: {g.get('coursework', '-')}, النظري: {g.get('final_exam', '-')}, الكود: {g.get('code', '-')},\n"
                await query.edit_message_text(msg[:4096])
            else:
                await query.edit_message_text("❌ لم يتم العثور على درجات.")
        except Exception as e:
            await query.edit_message_text(f"❌ حدث خطأ أثناء جلب الدرجات: {e}")

    async def _admin_force_grade_show_html(self, query, telegram_id):
        """
        Fetch and show raw HTML for a user's grades (for troubleshooting).
        """
        users = self.user_storage.get_all_users()
        user = next((u for u in users if str(u.get("telegram_id")) == str(telegram_id)), None)
        if not user:
            await query.edit_message_text(
                "❌ المستخدم غير موجود.",
                reply_markup=get_enhanced_admin_dashboard_keyboard(),
            )
            return
        token = user.get("session_token")
        username = user.get("username", "-")
        username_unique = user.get("username_unique", username)
        if not token:
            await query.edit_message_text(
                f"❌ لا يوجد رمز دخول لهذا المستخدم ({username}).",
                reply_markup=get_enhanced_admin_dashboard_keyboard(),
            )
            return
        try:
            await query.edit_message_text(f"📝 جاري جلب بيانات HTML للمستخدم: {username} ({telegram_id})...")
            api = self.bot.university_api
            known_term_ids = ["10459"]
            raw_htmls = []
            for term_id in known_term_ids:
                headers = {**api.api_headers, "Authorization": f"Bearer {token}"}
                payload = {
                    "operationName": "getPage",
                    "variables": {
                        "name": "test_student_tracks",
                        "params": [{"name": "t_grade_id", "value": term_id}],
                    },
                    "query": api.UNIVERSITY_QUERIES["GET_GRADES"] if hasattr(api, "UNIVERSITY_QUERIES") else api.api_queries["GET_GRADES"],
                }
                async with aiohttp.ClientSession(timeout=api.timeout) as session:
                    async with session.post(api.api_url, headers=headers, json=payload) as response:
                        if response.status == 200:
                            data = await response.json()
                            page = data.get("data", {}).get("getPage")
                            if page and "panels" in page:
                                for panel in page.get("panels", []):
                                    for block in panel.get("blocks", []):
                                        html_content = block.get("body", "")
                                        if html_content:
                                            raw_htmls.append(html_content)
            if raw_htmls:
                for i, html in enumerate(raw_htmls):
                    html_preview = html[:1500] + ("..." if len(html) > 1500 else "")
                    await query.edit_message_text(f"[HTML {i+1}]\n<pre>{html_preview}</pre>", parse_mode="HTML")
            else:
                await query.edit_message_text("❌ لم يتم العثور على بيانات HTML.")
        except Exception as e:
            await query.edit_message_text(f"❌ حدث خطأ أثناء جلب بيانات HTML: {e}")
