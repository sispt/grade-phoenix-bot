# 📝 Update Summary | ملخص التحديث

## Overview | نظرة عامة
This update brings a major refactor and robustness improvements to the Telegram University Bot. The system now features a dual extraction mechanism for grades, improved error handling, and full harmony between all modules.

هذا التحديث يجلب إعادة هيكلة وتحسينات كبيرة في الموثوقية. النظام الآن يدعم استخراج الدرجات من الـAPI أو من ملفات HTML، مع معالجة أخطاء متقدمة وتكامل كامل بين جميع الوحدات.

---

## Key Changes | التغييرات الرئيسية
- **Dual Extraction System**: Grades are fetched via the university API, with automatic fallback to HTML parsing if the API fails.
- **Robust Parsing**: Flexible HTML/GraphQL table parsing supports both Arabic and English headers, and various table formats.
- **Unified Data Format**: Both extraction methods produce the same grade data structure for seamless storage and display.
- **Improved Error Handling**: More logging, retries, and graceful fallback in all layers.
- **Modular & Extensible**: All modules (API, bot, storage, config) are decoupled and easy to extend.
- **Test Coverage**: New and updated test scripts for both API and HTML extraction.

---

## Migration & Usage Notes | ملاحظات الاستخدام والترحيل
- **No manual migration needed**: The new system is backward compatible with previous grade data formats.
- **Configuration**: Ensure your `config.py` is up-to-date with the latest GraphQL queries.
- **Storage**: Both JSON and PostgreSQL storage are supported and work with the new unified format.
- **Testing**: Use `test_graphql_grades_parser.py` to verify extraction logic with sample data.

---

## Example Data Structure | مثال على بنية البيانات
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

## Credits | المطور
- Developed by Abdulrahman Abdelkader
- Contact: tox098123@gmail.com | Telegram: @sisp_t

---

**This update ensures maximum reliability, flexibility, and maintainability for all users.**

هذا التحديث يضمن أقصى درجات الموثوقية والمرونة وسهولة الصيانة لجميع المستخدمين. 

# Update Log | سجل التحديثات

## v{CONFIG['BOT_VERSION']} (Latest)

### العربية
- تم إزالة جميع المعلومات الثابتة (اسم الأدمن، الإيميل، النسخة) من الكود، وأصبحت تأتي من متغيرات البيئة (Railway/Heroku).
- عرض رقم النسخة في أوامر /start و /help.
- تحسين الحماية لجميع ميزات الأدمن.
- تنظيف الكود من التعليقات القديمة أو أي إشارات للذكاء الاصطناعي.
- تحسين رسائل الخطأ والتنبيهات.
- دعم كامل للتخزين على PostgreSQL أو ملفات.

### English
- All admin info (username, email) and bot version are now loaded from environment variables (no hardcoding).
- Bot version is shown in /start and /help commands.
- All admin/dashboard features are protected and configurable.
- Code cleaned from old/AI comments.
- Improved error handling and notifications.
- Full support for PostgreSQL and file-based storage. 