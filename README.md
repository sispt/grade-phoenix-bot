# 🎓 Telegram University Bot (Based on Beehouse v2.1)

## Overview | نظرة عامة
A robust Telegram bot for university students to fetch and display their course grades. Supports both direct API extraction and HTML fallback for maximum reliability.

بوت متكامل لجلب الدرجات الجامعية من نظام الجامعة وعرضها عبر تيليجرام. يدعم استخراج الدرجات من API أو من ملفات HTML عند الحاجة.

---

## What's New | ما الجديد؟
- **Admin/Contact info is now fully configurable via environment variables (no hardcoding).**
- **Bot version is shown in /start and /help, and is set via BOT_VERSION env variable.**
- **All admin actions and dashboard features are protected and configurable.**
- **Cleaner code, no AI or debug comments.**
- **Improved error handling and notifications.**
- **PostgreSQL and file-based storage both supported.**

---

## Features | الميزات
- **Dual Extraction System**: Fetch grades via university API or fallback to HTML parsing.
- **Robust Error Handling**: Retries, logging, and graceful fallback.
- **Flexible Data Parsing**: Supports Arabic and English table headers.
- **Extensible Storage**: Save grades in JSON files or PostgreSQL.
- **Modular Design**: Easy to maintain and extend.
- **Admin Dashboard**: View stats, broadcast, manage users (admin only).
- **Notifications**: Automatic grade change notifications.
- **Multi-language Support**: Arabic and English.

---

## Environment Variables | متغيرات البيئة
Set these in your Railway/Heroku/OS environment:
- `TELEGRAM_TOKEN`: Bot token
- `ADMIN_ID`: Telegram user ID of the admin
- `ADMIN_USERNAME`: Admin's Telegram username (e.g. @your_admin)
- `ADMIN_EMAIL`: Admin's email (for contact)
- `BOT_VERSION`: Bot version string (shown in /start, /help)
- `DATABASE_URL`: PostgreSQL connection string (if using DB)
- `GRADE_CHECK_INTERVAL`: Interval between grade checks (in **minutes**)
- (Other config variables as needed in `config.py`)

---

## Architecture | بنية النظام
```
[User]
   |
[Telegram Bot]
   |
[UniversityAPI]
   |-------------------|
[API Extraction]   [HTML Fallback]
   |                    |
[Grades Data] <---[Storage Layer]
```

---

## Main Modules | الوحدات الرئيسية
- `university/api.py`: API integration, login, token, grades extraction (API & HTML)
- `config.py`: All GraphQL queries and configuration
- `bot/core.py`: Telegram bot logic, user interaction, fallback handling
- `storage/grades.py` & `storage/postgresql_grades.py`: Grades storage (file/DB)
- `test_graphql_grades_parser.py`: Test for grades extraction logic

---

## How Grades Extraction Works | كيف يعمل استخراج الدرجات
1. **API First**: Attempts to fetch grades using GraphQL API queries.
2. **Fallback**: If API fails or returns no grades, parses saved HTML files for grades tables.
3. **Unified Format**: Both methods produce the same data structure for seamless storage and display.

### Example Data Structure | مثال على بنية البيانات
```python
{
  "course": "اللغة العربية (1)",
  "code": "ARAB100",
  "ects": 2,
  "practical": "38",
  "theoretical": "49",
  "total": "87 %"
}
```

---

## Setup | الإعداد
1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure `config.py` with your university and bot credentials.
3. Run the bot:
   ```bash
   python main.py
   ```

---

## Extensibility | قابلية التوسعة
- Add new GraphQL queries in `config.py` as needed.
- Extend HTML parsing logic in `api.py` for new table formats.
- Switch storage backend by updating the storage module.

---

## Credits | المطور
- Developed by: Abdulrahman Abdulkader
- Contact: abdulrahmanabdulkader59@gmail.com | Telegram: @sisp_t

---

**This project is designed for reliability, flexibility, and easy maintenance.**

مشروع مصمم للموثوقية والمرونة وسهولة الصيانة. 

## Running Tests

To run the unit tests, make sure you have the dev dependencies installed:

```
pip install -r requirements.txt
```

Then run:

```
pytest
```

This will automatically discover and run all tests in the project.

## Admin Dashboard

The admin dashboard is only accessible to the admin (as set in `ADMIN_ID`). Features include:
- User overview and analytics
- Broadcast message to all users (admin only)
- View and search users

## Broadcast Feature

Admins can send a broadcast message to all users from the dashboard. Only admins see this option.

## Grade Notification Logic

- The bot checks for grade changes every `GRADE_CHECK_INTERVAL` minutes (configurable via environment variable or config.py).
- Only changed courses are notified to the user, with both old and new values shown.
- Notifications are sent in Arabic, mentioning the user's university full name.

## Running & Deployment

1. Set required environment variables (see above).
2. Deploy to your preferred platform (Railway, Heroku, etc.).
3. Set `GRADE_CHECK_INTERVAL` in your environment or config.py as needed.
4. Start the bot with `python main.py`.

For more details, see comments in the code and UPDATE.md.
