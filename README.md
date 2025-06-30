# 🎓 Telegram University Bot (BeeHouse Notif)

## Overview | نظرة عامة
A robust Telegram bot for university students to fetch and display their course grades. Supports both direct API extraction and HTML fallback for maximum reliability.

بوت متكامل لجلب الدرجات الجامعية من نظام الجامعة وعرضها عبر تيليجرام. يدعم استخراج الدرجات من API أو من ملفات HTML عند الحاجة.

---

## Features | الميزات
- **Dual Extraction System**: Fetch grades via university API or fallback to HTML parsing.
- **Robust Error Handling**: Retries, logging, and graceful fallback.
- **Flexible Data Parsing**: Supports Arabic and English table headers.
- **Extensible Storage**: Save grades in JSON files or PostgreSQL.
- **Modular Design**: Easy to maintain and extend.

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
- Developed by Abdulrahman Abdelkader
- Contact: tox098123@gmail.com | Telegram: @sisp_t

---

**This project is designed for reliability, flexibility, and easy maintenance.**

مشروع مصمم للموثوقية والمرونة وسهولة الصيانة. 