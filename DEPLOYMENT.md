# 🚀 دليل النشر - Telegram University Bot v2.1.3

## 📋 المتطلبات الأساسية

### 1. حساب Telegram Bot
1. اذهب إلى [@BotFather](https://t.me/BotFather) على Telegram
2. اكتب `/newbot` لإنشاء بوت جديد
3. اختر اسم للبوت (مثال: "بوت إشعارات الدرجات")
4. اختر username للبوت (مثال: `university_grades_bot`)
5. احفظ التوكن الذي ستحصل عليه

### 2. معرف Telegram الخاص بك
1. اذهب إلى [@userinfobot](https://t.me/userinfobot)
2. اكتب `/start`
3. احفظ معرف Telegram الخاص بك (مثال: `123456789`)

## 🌐 النشر على Railway

### الخطوة 1: إعداد GitHub
```bash
# إنشاء مستودع جديد على GitHub
git init
git add .
git commit -m "Initial commit - Telegram University Bot v2.1.3"
git branch -M main
git remote add origin https://github.com/yourusername/telegram-university-bot.git
git push -u origin main
```

### الخطوة 2: إعداد Railway
1. اذهب إلى [Railway.app](https://railway.app)
2. سجل دخولك بحساب GitHub
3. اضغط "New Project"
4. اختر "Deploy from GitHub repo"
5. اختر المستودع الذي أنشأته

### الخطوة 3: إعداد المتغيرات البيئية
في Railway، اذهب إلى "Variables" وأضف:

```bash
# متغيرات مطلوبة
TELEGRAM_TOKEN=your_bot_token_here
ADMIN_ID=your_telegram_id
DATABASE_URL=postgresql://username:password@host:port/database

# متغيرات اختيارية
ADMIN_USERNAME=@your_username
ADMIN_EMAIL=your_email@example.com
DEBUG_MODE=false
LOG_LEVEL=INFO
```

### الخطوة 4: النشر
1. Railway سيقوم بالبناء تلقائياً
2. انتظر حتى يكتمل البناء
3. البوت سيعمل تلقائياً

## 🔧 إعدادات النشر

### ملف Procfile
```
web: python main.py
```

### ملف requirements.txt
```
python-telegram-bot==20.7
aiohttp==3.9.1
beautifulsoup4==4.12.2
flask==3.0.0
python-dotenv==1.0.0
```

### ملف runtime.txt
```
python-3.11.7
```

## 📊 مراقبة البوت

### فحص الصحة
- **الرابط:** `https://your-app.railway.app/health`
- **الحالة:** يجب أن تعرض `{"status": "healthy"}`

### السجلات
- في Railway، اذهب إلى "Deployments"
- اضغط على آخر deployment
- شاهد "Logs" لمراقبة البوت

### الإحصائيات
- استخدم `/stats` في البوت (للمطور فقط)
- شاهد إحصائيات Railway في لوحة التحكم

## 🛠️ استكشاف الأخطاء

### مشاكل شائعة

#### 1. البوت لا يستجيب
```bash
# تحقق من:
- صحة TELEGRAM_TOKEN
- صحة ADMIN_ID
- سجلات Railway
```

#### 2. فشل في تسجيل الدخول
```bash
# تحقق من:
- صحة بيانات الجامعة
- اتصال الإنترنت
- حالة API الجامعة
```

#### 3. فشل في النشر
```bash
# تحقق من:
- صحة requirements.txt
- صحة Python version
- سجلات البناء في Railway
```

### أوامر التشخيص
```bash
# فحص الصحة
curl https://your-app.railway.app/health

# فحص الحالة
curl https://your-app.railway.app/status

# فحص الجذر
curl https://your-app.railway.app/
```

## 🔄 التحديثات

### تحديث البوت
```bash
# في GitHub
git add .
git commit -m "Update bot"
git push origin main

# Railway سيقوم بالتحديث تلقائياً
```

### إعادة تشغيل البوت
```bash
# في Railway
- اذهب إلى "Deployments"
- اضغط "Redeploy"
```

## 📱 اختبار البوت

### 1. اختبار أساسي
```
/start - بدء البوت
/help - المساعدة
```

### 2. اختبار تسجيل الدخول
```
/register - تسجيل الدخول بالجامعة
```

### 3. اختبار فحص الدرجات
```
/grades - فحص الدرجات
```

### 4. اختبار المطور
```
/stats - إحصائيات (للمطور فقط)
/broadcast - إشعار عام (للمطور فقط)
```

## 🔒 الأمان

### نصائح أمنية
1. **لا تشارك التوكن** مع أي شخص
2. **استخدم متغيرات بيئية** للمعلومات الحساسة
3. **راقب سجلات البوت** دورياً
4. **احتفظ بنسخ احتياطية** من البيانات
5. **حدث البوت** بانتظام

### مراقبة الأمان
- راجع سجلات Railway دورياً
- تحقق من إحصائيات البوت
- راقب الأنشطة المشبوهة

## 📞 الدعم

### في حالة المشاكل
1. **تحقق من السجلات** في Railway
2. **اختبر البوت** محلياً أولاً
3. **تواصل مع المطور:**
   - البريد الإلكتروني: tox098123@gmail.com
   - Telegram: @sisp_t

### موارد مفيدة
- [Railway Documentation](https://docs.railway.app)
- [Python Telegram Bot Documentation](https://python-telegram-bot.readthedocs.io)
- [GitHub Repository](https://github.com/yourusername/telegram-university-bot)

---

🔔 **بوت الإشعارات الجامعية** - نظام متقدم لإشعارات الدرجات الجامعية
👨‍💻 المطور: عبدالرحمن عبدالقادر 

# 🚂 Railway Deployment Guide

## 📋 Prerequisites

- Railway account
- Telegram Bot Token
- PostgreSQL database (Railway provides this)

## 🗄️ Database Setup

### 1. Create PostgreSQL Database on Railway

1. Go to your Railway project
2. Click "New" → "Database" → "PostgreSQL"
3. Wait for the database to be provisioned
4. Copy the `DATABASE_URL` from the database settings

### 2. Configure Environment Variables

Set these environment variables in your Railway project:

```bash
# Required
TELEGRAM_TOKEN=your_bot_token_here
ADMIN_ID=your_telegram_id
DATABASE_URL=postgresql://username:password@host:port/database

# Optional
ADMIN_USERNAME=@your_username
ADMIN_EMAIL=your_email@example.com
LOG_LEVEL=INFO
```

### 3. Database Migration

The bot will automatically run database migrations on startup. If you need to run them manually:

```bash
python migrations.py
```

## 🚀 Deployment Steps

### 1. Connect Your Repository

1. Go to Railway dashboard
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your bot repository
4. Railway will automatically detect it's a Python project

### 2. Configure Build Settings

Railway will automatically:
- Install dependencies from `requirements.txt`
- Use Python 3.11 (specified in `runtime.txt`)
- Run the bot using the command in `Procfile`

### 3. Set Environment Variables

In your Railway project settings, add these environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `TELEGRAM_TOKEN` | Your Telegram bot token | `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz` |
| `ADMIN_ID` | Your Telegram user ID | `123456789` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `ADMIN_USERNAME` | Your Telegram username | `@your_username` |
| `ADMIN_EMAIL` | Your email address | `admin@example.com` |
| `LOG_LEVEL` | Logging level | `INFO` |

### 4. Deploy

1. Railway will automatically deploy when you push to your main branch
2. Monitor the deployment logs for any errors
3. Check that the database migration completed successfully

## 🔧 Configuration

### Webhook Setup

The bot automatically configures webhooks for Railway:

```python
webhook_url = f"https://your-app-name.up.railway.app/{TELEGRAM_TOKEN}"
```

### Database Configuration

The bot automatically detects PostgreSQL from the `DATABASE_URL`:

```python
"USE_POSTGRESQL": bool(os.getenv("DATABASE_URL", "").startswith("postgresql"))
```

## 📊 Monitoring

### Railway Dashboard

- **Deployments**: Monitor deployment status and logs
- **Database**: View database metrics and connection status
- **Logs**: Real-time application logs

### Bot Commands

Use these commands to monitor your bot:

- `/stats` - View bot statistics (admin only)
- `/list_users` - List all users (admin only)

## 🔍 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check `DATABASE_URL` is correct
   - Ensure database is provisioned and running
   - Check Railway database logs

2. **Webhook Not Working**
   - Verify `TELEGRAM_TOKEN` is correct
   - Check Railway app is accessible
   - Review deployment logs

3. **Migration Errors**
   - Check database permissions
   - Verify `DATABASE_URL` format
   - Review migration logs

### Debug Commands

```bash
# Check database connection
python -c "from storage.models import DatabaseManager; from config import CONFIG; db = DatabaseManager(CONFIG['DATABASE_URL']); print(db.test_connection())"

# Run migrations manually
python migrations.py

# Check database status
python -c "from migrations import check_database_status; check_database_status()"
```

## 🔄 Updates

### Automatic Updates

Railway automatically redeploys when you push to your main branch.

### Manual Updates

1. Push changes to your repository
2. Railway will detect changes and redeploy
3. Monitor deployment logs
4. Verify bot functionality

## 📈 Scaling

### Railway Auto-Scaling

Railway automatically scales your application based on traffic.

### Database Scaling

- Railway PostgreSQL automatically handles scaling
- No additional configuration needed
- Monitor database usage in Railway dashboard

## 🔒 Security

### Environment Variables

- Never commit sensitive data to your repository
- Use Railway's environment variable system
- Rotate tokens regularly

### Database Security

- Railway PostgreSQL includes SSL encryption
- Automatic backups enabled
- Access controlled by Railway

## 📞 Support

### Railway Support

- Railway documentation: https://docs.railway.app/
- Railway Discord: https://discord.gg/railway

### Bot Support

- Check logs in Railway dashboard
- Use bot admin commands for diagnostics
- Contact bot developer for issues

## 🎯 Best Practices

1. **Environment Variables**: Always use environment variables for sensitive data
2. **Logging**: Monitor logs regularly for issues
3. **Backups**: Railway handles database backups automatically
4. **Testing**: Test changes locally before deploying
5. **Monitoring**: Use Railway's monitoring tools

## 📝 Notes

- Railway provides persistent storage for PostgreSQL
- Webhooks are automatically configured
- Database migrations run on startup
- Logs are available in Railway dashboard
- Environment variables are encrypted and secure 