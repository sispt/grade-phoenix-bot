"""
🎨 Telegram Message Color and Formatting Demo
Shows different ways to add colors and styling to bot messages
"""

from telegram.constants import ParseMode

def get_html_colored_message():
    """HTML formatting with colors"""
    return """
<b>🎨 HTML Formatting Examples:</b>

<code>🔴 Red Text</code>
<code>🟢 Green Text</code>
<code>🔵 Blue Text</code>

<b>Bold Text</b>
<i>Italic Text</i>
<u>Underlined Text</u>
<s>Strikethrough Text</s>

<pre>Monospace Text</pre>

<a href="https://t.me/your_bot">Link Text</a>

<code>Inline Code</code>

<pre><code class="language-python">
def hello_world():
    print("Hello, World!")
</code></pre>
"""

def get_markdown_colored_message():
    """Markdown formatting"""
    return """
**🎨 Markdown Formatting Examples:**

`🔴 Red Text`
`🟢 Green Text`
`🔵 Blue Text`

**Bold Text**
*Italic Text*
__Underlined Text__
~~Strikethrough Text~~

`Inline Code`

```python
def hello_world():
    print("Hello, World!")
```

[Link Text](https://t.me/your_bot)
"""

def get_grade_colored_message():
    """Example of colored grade display"""
    return """
🎓 **<b>درجات الفصل الحالي</b>**

📚 <b>المادة:</b> <code>برمجة الحاسوب</code>
🔬 <b>العملي:</b> <code style="color: #00ff00;">85%</code>
✍️ <b>التحريري:</b> <code style="color: #ffaa00;">78%</code>
🎯 <b>النهائي:</b> <code style="color: #ff0000;">92%</code>

📊 <b>المعدل التراكمي:</b> <code style="color: #0088ff;">3.45</code>

<pre>📈 التقدم: ██████████ 100%</pre>
"""

def get_status_colored_message():
    """Example of status indicators with colors"""
    return """
🔄 **<b>حالة النظام</b>**

✅ <code style="color: #00ff00;">متصل بالجامعة</code>
✅ <code style="color: #00ff00;">قاعدة البيانات نشطة</code>
⚠️ <code style="color: #ffaa00;">فحص الدرجات قيد التشغيل</code>
❌ <code style="color: #ff0000;">إشعارات معطلة</code>

📊 <b>إحصائيات:</b>
• 👥 المستخدمين: <code>1,234</code>
• 🔔 الإشعارات: <code>5,678</code>
• ⚠️ الأخطاء: <code style="color: #ff0000;">3</code>
"""

def get_alert_colored_message():
    """Example of alert/notification with colors"""
    return """
🚨 **<b>تنبيه مهم!</b>**

⚠️ <code style="color: #ff0000;">انتهت صلاحية الجلسة</code>

📝 <b>الإجراء المطلوب:</b>
• إعادة تسجيل الدخول
• تحديث كلمة المرور
• التحقق من البيانات

⏰ <b>الوقت المتبقي:</b> <code style="color: #ffaa00;">30 دقيقة</code>

<a href="https://t.me/your_bot">🔗 إعادة التسجيل</a>
"""

# Usage examples:
if __name__ == "__main__":
    print("HTML Formatting:")
    print(get_html_colored_message())
    print("\n" + "="*50 + "\n")
    
    print("Markdown Formatting:")
    print(get_markdown_colored_message())
    print("\n" + "="*50 + "\n")
    
    print("Grade Display with Colors:")
    print(get_grade_colored_message())
    print("\n" + "="*50 + "\n")
    
    print("Status Indicators:")
    print(get_status_colored_message())
    print("\n" + "="*50 + "\n")
    
    print("Alert Message:")
    print(get_alert_colored_message()) 