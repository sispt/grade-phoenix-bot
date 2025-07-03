![Project Logo](logo.png)

# 🎓 Telegram University Bot

**Version: 2.5.7** | **Security Rating: A+** | **Status: Production Ready**

[![Tests](https://img.shields.io/badge/Tests-20%2F20%20Passing-brightgreen)](run_tests.py)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](requirements.txt)
[![Security](https://img.shields.io/badge/Security-A--Level-brightgreen)](docs/security/SECURITY_AUDIT.md)

A secure, user-friendly Telegram bot for university students to receive grade notifications and academic updates with comprehensive security features and transparent credential handling.

## 🚀 Features

### 📊 Core Features
- **Real-time Grade Notifications:** Instant alerts when grades change
- **Grade Analytics:** Comprehensive analysis with insights and trends
- **Motivational Quotes:** Contextual wisdom based on academic performance
- **Grade History:** Track progress over time with detailed statistics
- **Current & Old Term Grades:** Access both current and historical academic data

### 🔐 Security & Privacy
- **Enterprise Security:** Rate limiting, audit logging
- **Security Headers:** Comprehensive security headers (CSP, HSTS, X-Frame-Options)
- **User Transparency:** Clear explanation of credential handling
- **Input Validation:** Comprehensive validation for all user inputs
- **SQL Injection Protection:** SQLAlchemy ORM prevents injection attacks
- **GDPR Compliance:** Full data protection and privacy policy
- **Security Monitoring:** Real-time security statistics and alerts

### 👨‍💼 Admin Features
- **Admin Dashboard:** User analytics and management
- **Broadcast System:** Send messages to all users
- **User Management:** Search, view, and manage user accounts
- **Security Statistics:** Real-time security monitoring dashboard
- **Backup & Restore:** Automated data backup system

### 🎯 Smart Features
- **Automated Grade Checks:** Periodic background monitoring
- **Multi-Storage Support:** PostgreSQL and file-based storage
- **Automatic Migrations:** Database schema updates
- **Contextual Quotes:** Philosophy-based motivational messages
- **User Settings:** Customizable notification preferences

## 📁 Project Structure

```
telegram_university_bot/
├── 📁 admin/                 # Admin functionality
│   ├── dashboard.py         # Admin dashboard
│   └── broadcast.py         # Broadcast system
├── 📁 bot/                   # Core bot logic
│   └── core.py              # Main bot implementation
├── 📁 security/              # Security modules
│   ├── enhancements.py      # Security features
│   ├── headers.py           # Security headers
│   ├── input_validation.py  # Input validation
│   └── transparency.py      # Security transparency
├── 📁 storage/               # Data storage layer
│   ├── models.py            # Database models
│   ├── user_storage.py      # User management
│   ├── grade_storage.py     # Grade management
│   └── credential_cache.py  # Credential caching
├── 📁 university/            # University API integration
│   └── api_client.py        # API client
├── 📁 utils/                 # Utility modules
│   ├── messages.py          # Message templates
│   ├── keyboards.py         # Bot keyboards
│   ├── analytics.py         # Analytics utilities
│   └── settings.py          # Settings management
├── 📁 tests/                 # Test suite
│   ├── api/                 # API tests
│   ├── security/            # Security tests
│   └── storage/             # Storage tests
├── 📁 docs/                  # Documentation
├── main.py                  # Application entry point
├── config.py                # Configuration
└── requirements.txt         # Dependencies
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL (recommended for production)
- Telegram Bot Token

### Installation

1. **Clone and setup:**
```bash
git clone <your-repo-url>
cd telegram_university_bot
pip install -r requirements.txt
```

2. **Set environment variables:**
```bash
export TELEGRAM_TOKEN="your_bot_token"
export ADMIN_ID="your_telegram_id"
export DATABASE_URL="postgresql://user:pass@host:port/db"  # Optional
```

3. **Run tests:**
```bash
python run_tests.py
```

4. **Start the bot:**
```bash
python main.py
```

## 🔐 Security Implementation

### **Authentication & Authorization**
- **No Password Storage:** Passwords are never stored or hashed; used only for login and immediately discarded
- **Rate Limiting:** 5 login attempts per 5 minutes, 15-minute blocks
- **Session Management:** 1-hour timeouts, max 3 sessions per user
- **Input Validation:** Comprehensive validation using validators package
- **Security Headers:** CSP, HSTS, X-Frame-Options, X-Content-Type-Options

### **Data Protection**
- **No Plain Text Storage:** Passwords never stored in plain text
- **Encrypted Transmission:** All data transmitted securely
- **Environment Variables:** Sensitive configuration stored securely
- **GDPR Compliance:** Full data protection measures

### **Monitoring & Auditing**
- **Security Event Logging:** All security events logged with risk levels
- **Real-time Statistics:** Admin dashboard for security monitoring
- **Audit Trail:** Complete audit trail for compliance
- **Threat Detection:** Automated detection of suspicious activity

### **User Transparency**
Users see clear security information:
- Security level indicator (High)
- Explanation of credential handling
- Privacy policy and data protection info
- Security commands: `/security_info`, `/security_audit`, `/privacy_policy`

## 🧪 Testing

```bash
# Run all tests
python run_tests.py

# Run security tests
python -m pytest tests/security/

# Run specific test categories
python -m pytest tests/api/
python -m pytest tests/security/
python -m pytest tests/storage/
```

**Test Coverage:** 20/20 tests passing (pytest + manual tests)

## 🎯 User Experience

### **New User Journey**
1. **Start:** Simple welcome explaining what the bot does
2. **Security Info:** Clear explanation of credential handling
3. **Registration:** Easy login process with validation
4. **Welcome:** Personalized welcome with security status
5. **Usage:** Intuitive interface with helpful commands

### **Grade Access**
- **Current Term Grades:** Latest academic performance
- **Old Term Grades:** Historical academic data with analysis
- **Rich Analytics:** Detailed insights with motivational quotes
- **Clear Navigation:** Intuitive button layout and commands

### **Admin Experience**
1. **Dashboard:** Comprehensive admin panel (`/admin`)
2. **Security Stats:** Real-time security monitoring (`/security_stats`)
3. **User Management:** Full user control and analytics
4. **Broadcast System:** Easy communication with users

## 🔧 Configuration

### **Environment Variables**
| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `TELEGRAM_TOKEN` | Telegram bot token | ✅ | - |
| `ADMIN_ID` | Admin Telegram ID | ✅ | - |
| `DATABASE_URL` | PostgreSQL connection | ❌ | SQLite |
| `BOT_VERSION` | Bot version | ❌ | dev |
| `GRADE_CHECK_INTERVAL` | Check interval (minutes) | ❌ | 15 |
| `QUOTE_SCHEDULE` | Daily quote broadcast time | ❌ | 14:00 |

### **Security Configuration**
- **Rate Limiting:** 5 attempts per 5 minutes
- **Session Timeout:** 1 hour
- **Max Sessions:** 3 per user
- **Audit Log Retention:** Configurable
- **Security Headers:** CSP, HSTS, X-Frame-Options, X-Content-Type-Options
- **Security Level:** A+ (Enterprise-grade)

## 📚 Documentation

- **Security Audit:** `docs/security/SECURITY_AUDIT.md`
- **Update History:** `docs/updates/UPDATE.md`
- **Security Improvements:** `docs/updates/SECURITY_IMPROVEMENTS.md`

## 🚨 Monitoring & Maintenance

### **Daily Checks**
- Bot responsiveness
- Error log review
- Security event monitoring
- User activity tracking

### **Weekly Checks**
- Database health
- Backup verification
- Security statistics review
- Performance monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `python run_tests.py`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the documentation in `/docs`
- Review security audit: `docs/security/SECURITY_AUDIT.md`
- Contact the development team

---

**Last Updated:** December 2024  
**Security Rating:** A+ (Enterprise-grade)  
**Version:** 2.5.7

## Quote and Translation System (Updated)

- Quotes are always fetched in English from APIs using a wide range of intellectual keywords.
- Each quote is translated to Arabic using the googletrans library, configured with `service_urls` and `user_agent` as per the official documentation.
- Strict debugging logs and error handling are implemented for translation attempts.
- The dual-language quote (always wrapped in double quotes) is included at the end of:
  - Current term grade messages
  - Past term grade messages
  - Grade update notifications
  - All broadcast quote messages (admin and scheduled)
- Only English quotes are fetched; Arabic quotes are never fetched directly.
- The button and keyboard system is robust, covers all user flows (registration, error recovery, admin, settings, notifications, broadcasts), and uses both reply and inline keyboards for optimal UX.
- **Note:** Translation reliability depends on Google and the maintenance of the googletrans library. If you encounter persistent errors, check your library version and configuration, or consider the official Google Cloud Translation API for production use. Translation tests are skipped if the API is blocked (403), so test results reflect only actual code issues.
- The daily quote broadcast time is controlled by the `QUOTE_SCHEDULE` environment variable (see above). The scheduler always uses UTC+3 and validates the format strictly.

## Example Output

```
"The only way to do great work is to love what you do."
"الطريقة الوحيدة للقيام بعمل عظيم هي أن تحب ما تفعله."
— Steve Jobs
```

## July 2025 Update: New Logo & Repo Name

- The project now features a new official logo, symbolizing academic achievement and growth.
- The repository has been renamed to `grade-phoenix-bot` to reflect the new branding and vision.
