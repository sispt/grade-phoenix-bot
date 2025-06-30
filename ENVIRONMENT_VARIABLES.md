# 🌍 Environment Variables Configuration Guide

**Telegram University Bot v2.1.3**

---

## 📋 Required Environment Variables

### **🔑 Core Bot Configuration**

| Variable | Description | Default Value | Required |
|----------|-------------|---------------|----------|
| `TELEGRAM_TOKEN` | Bot token from @BotFather | `your_bot_token_here` | ✅ **YES** |
| `ADMIN_ID` | Admin Telegram ID | `123456789` | ✅ **YES** |

### **👤 Admin Information**

| Variable | Description | Default Value | Required |
|----------|-------------|---------------|----------|
| `ADMIN_USERNAME` | Admin Telegram username | `@sisp_t` | ❌ No |
| `ADMIN_EMAIL` | Admin email address | `tox098123@gmail.com` | ❌ No |
| `ADMIN_NAME` | Admin full name | `Abdulrahman Abdulqader` | ❌ No |

### **🗄️ Database Configuration**

| Variable | Description | Default Value | Required |
|----------|-------------|---------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | `sqlite:///./data/bot.db` | ❌ No |

### **📱 Application Version**

| Variable | Description | Default Value | Required |
|----------|-------------|---------------|----------|
| `BOT_VERSION` | Application version | `2.1.3` | ❌ No |

### **🌐 Deployment Configuration**

| Variable | Description | Default Value | Required |
|----------|-------------|---------------|----------|
| `WEBHOOK_URL` | Webhook URL for deployment | Auto-generated | ❌ No |
| `PORT` | Server port | `8443` | ❌ No |

---

## 🚀 Setting Up Environment Variables

### **1. Local Development (.env file)**

Create a `.env` file in the project root:

```bash
# Core Bot Configuration
TELEGRAM_TOKEN=your_actual_bot_token_here
ADMIN_ID=your_telegram_id_here

# Admin Information
ADMIN_USERNAME=@your_username
ADMIN_EMAIL=your.email@example.com
ADMIN_NAME=Your Full Name

# Database (Optional - for PostgreSQL)
DATABASE_URL=postgresql://username:password@localhost:5432/bot_db

# Application Version
BOT_VERSION=2.1.3

# Deployment (Optional)
WEBHOOK_URL=https://your-domain.com/webhook
PORT=8443
```

### **2. Railway Deployment**

Set environment variables in Railway dashboard:

```bash
# Required
TELEGRAM_TOKEN=your_actual_bot_token_here
ADMIN_ID=your_telegram_id_here

# Optional Admin Info
ADMIN_USERNAME=@your_username
ADMIN_EMAIL=your.email@example.com
ADMIN_NAME=Your Full Name

# Optional Database
DATABASE_URL=postgresql://username:password@host:port/database

# Optional Version
BOT_VERSION=2.1.3
```

### **3. Heroku Deployment**

Set environment variables using Heroku CLI:

```bash
heroku config:set TELEGRAM_TOKEN=your_actual_bot_token_here
heroku config:set ADMIN_ID=your_telegram_id_here
heroku config:set ADMIN_USERNAME=@your_username
heroku config:set ADMIN_EMAIL=your.email@example.com
heroku config:set ADMIN_NAME="Your Full Name"
heroku config:set BOT_VERSION=2.1.3
```

### **4. Docker Deployment**

Create a `.env` file or use docker-compose:

```yaml
version: '3.8'
services:
  bot:
    build: .
    environment:
      - TELEGRAM_TOKEN=your_actual_bot_token_here
      - ADMIN_ID=your_telegram_id_here
      - ADMIN_USERNAME=@your_username
      - ADMIN_EMAIL=your.email@example.com
      - ADMIN_NAME=Your Full Name
      - BOT_VERSION=2.1.3
      - DATABASE_URL=postgresql://username:password@db:5432/bot_db
```

---

## 🔧 Configuration Examples

### **Minimal Configuration (Required Only)**

```bash
TELEGRAM_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_ID=987654321
```

### **Full Configuration (Recommended)**

```bash
# Core
TELEGRAM_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_ID=987654321

# Admin Info
ADMIN_USERNAME=@abdulrahman_dev
ADMIN_EMAIL=abdulrahman.abdulqader@example.com
ADMIN_NAME=Abdulrahman Abdulqader

# Database
DATABASE_URL=postgresql://bot_user:secure_password@localhost:5432/university_bot

# Version
BOT_VERSION=2.1.3

# Deployment
WEBHOOK_URL=https://shamunibot-production.up.railway.app/webhook
PORT=8443
```

---

## 🔍 How to Get Required Values

### **1. TELEGRAM_TOKEN**
1. Message @BotFather on Telegram
2. Send `/newbot`
3. Follow instructions to create bot
4. Copy the token provided

### **2. ADMIN_ID**
1. Message @userinfobot on Telegram
2. It will reply with your Telegram ID
3. Copy the ID number

### **3. ADMIN_USERNAME**
1. Your Telegram username (with @ symbol)
2. Example: `@abdulrahman_dev`

### **4. ADMIN_EMAIL**
1. Your email address
2. Used for admin notifications and support

### **5. ADMIN_NAME**
1. Your full name
2. Used in admin dashboard and logs

---

## 🔒 Security Best Practices

### **1. Never Commit Sensitive Data**
```bash
# ✅ Good - Use environment variables
TELEGRAM_TOKEN=${BOT_TOKEN}

# ❌ Bad - Hardcoded in code
TELEGRAM_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### **2. Use Strong Passwords**
```bash
# ✅ Good - Strong database password
DATABASE_URL=postgresql://user:StrongP@ssw0rd123!@localhost:5432/bot_db

# ❌ Bad - Weak password
DATABASE_URL=postgresql://user:password@localhost:5432/bot_db
```

### **3. Rotate Tokens Regularly**
- Change bot token every 6 months
- Update environment variables accordingly
- Monitor for unauthorized access

---

## 🧪 Testing Environment Variables

### **1. Check Configuration**
```bash
# Test if variables are loaded
python -c "import os; print('TELEGRAM_TOKEN:', 'SET' if os.getenv('TELEGRAM_TOKEN') else 'NOT SET')"
```

### **2. Validate Bot Token**
```bash
# Test bot token validity
curl -X GET "https://api.telegram.org/bot${TELEGRAM_TOKEN}/getMe"
```

### **3. Test Database Connection**
```bash
# Test database connectivity
python -c "from config import CONFIG; print('Database URL:', CONFIG['DATABASE_URL'])"
```

---

## 📊 Environment Variable Priority

The system loads environment variables in this order:

1. **System Environment Variables** (Highest Priority)
2. **.env file** (if present)
3. **Default Values** (Lowest Priority)

### **Example:**
```python
# If TELEGRAM_TOKEN is set in system environment
os.getenv("TELEGRAM_TOKEN", "default_value")
# Returns: system_environment_value

# If not set in system environment but in .env file
os.getenv("TELEGRAM_TOKEN", "default_value")
# Returns: .env_file_value

# If not set anywhere
os.getenv("TELEGRAM_TOKEN", "default_value")
# Returns: "default_value"
```

---

## 🚨 Troubleshooting

### **Common Issues:**

1. **"Missing TELEGRAM_TOKEN"**
   - Check if token is set correctly
   - Verify token format: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

2. **"Invalid ADMIN_ID"**
   - Ensure ADMIN_ID is a number
   - Get your ID from @userinfobot

3. **"Database Connection Failed"**
   - Check DATABASE_URL format
   - Verify database credentials
   - Ensure database server is running

4. **"Webhook Setup Failed"**
   - Check WEBHOOK_URL format
   - Ensure domain is accessible
   - Verify SSL certificate

---

## 📝 Example .env File

```bash
# ========================================
# Telegram University Bot v2.1.3
# Environment Configuration
# ========================================

# 🔑 Core Configuration (REQUIRED)
TELEGRAM_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_ID=987654321

# 👤 Admin Information (OPTIONAL)
ADMIN_USERNAME=@abdulrahman_dev
ADMIN_EMAIL=abdulrahman.abdulqader@example.com
ADMIN_NAME=Abdulrahman Abdulqader

# 🗄️ Database Configuration (OPTIONAL)
DATABASE_URL=postgresql://bot_user:secure_password@localhost:5432/university_bot

# 📱 Application Version (OPTIONAL)
BOT_VERSION=2.1.3

# 🌐 Deployment Configuration (OPTIONAL)
WEBHOOK_URL=https://shamunibot-production.up.railway.app/webhook
PORT=8443

# ========================================
# End of Configuration
# ========================================
```

---

**Last Updated:** 2025-06-30  
**Version:** 2.1.3  
**Author:** Abdulrahman Abdulqader 