# 🔑 Token Usage & Debug Logging Update

## 📋 **Summary of Changes**

This update ensures that the bot properly uses stored tokens for all university API requests and provides comprehensive debug logging to track requests and grade comparisons.

## ✅ **Key Improvements Made**

### 1. **Token-Based Authentication** 🔑
- **Before**: Bot used username/password for re-authentication
- **After**: Bot uses stored tokens first, only re-authenticates when token expires
- **Benefit**: More efficient, secure, and faster API requests

### 2. **Enhanced Debug Logging** 📊
- **Added**: Detailed debug logs for all API requests
- **Added**: Token validity checks with clear status messages
- **Added**: Grade comparison logging showing when grades are the same/different
- **Added**: Request tracking for university API calls

### 3. **Improved Error Handling** 🛡️
- **Added**: Better token validation before making requests
- **Added**: Graceful fallback to re-authentication when needed
- **Added**: Clear error messages for debugging

## 🔧 **Technical Changes**

### **Bot Core (`bot/core.py`)**

#### **Grade Checking Loop (`_check_user_grades`)**
```python
# NEW: Token-first approach
token = user.get("token")
if not token:
    logger.warning(f"❌ DEBUG: No token found for user {username}, skipping grade check")
    return

# Test token validity
if not await self.university_api.test_token(token):
    logger.warning(f"⚠️ DEBUG: Token expired for user {username}, attempting re-authentication")
    # Only then try username/password re-authentication
```

#### **Grades Command (`_grades_command`)**
```python
# NEW: Enhanced token handling
token = session.get("token")
logger.info(f"🔍 DEBUG: Grades command - User {username} (ID: {telegram_id})")
logger.info(f"🔑 DEBUG: User has token: {'Yes' if token else 'No'}")

# Test token before making requests
if not await self.university_api.test_token(token):
    logger.info(f"⚠️ DEBUG: Token expired for user {username}, attempting re-authentication")
```

### **University API (`university/api.py`)**

#### **Token Testing (`test_token`)**
```python
# NEW: Detailed debug logging
logger.info(f"🔍 DEBUG: Testing token validity...")
logger.info(f"🌐 DEBUG: Making token test request to {self.api_url}")
logger.info(f"📡 DEBUG: Token test response status: {response.status}")
logger.info(f"✅ DEBUG: Token is {'valid' if is_valid else 'invalid'}")
```

#### **Grade Fetching (`_get_grades`)**
```python
# NEW: Request tracking
logger.info(f"🔍 DEBUG: Starting grade fetch with token...")
logger.info(f"🔍 DEBUG: Will try {len(possible_pages)} possible pages for grades")

for page_name in possible_pages:
    logger.info(f"🌐 DEBUG: Trying page: {page_name}")
    logger.info(f"📡 DEBUG: Making request to {self.api_url} for page: {page_name}")
    logger.info(f"📡 DEBUG: Page {page_name} response status: {response.status}")
```

## 📊 **Debug Log Examples**

### **Token Validation**
```
🔍 DEBUG: Testing token validity...
🌐 DEBUG: Making token test request to https://api.staging.sis.shamuniversity.com/graphql
📡 DEBUG: Token test response status: 200
✅ DEBUG: Token is valid
```

### **Grade Checking**
```
🔍 DEBUG: Starting grade check for user ENG2324901 (ID: 123456789)
🔑 DEBUG: User has token: Yes
🔍 DEBUG: Testing token validity for user ENG2324901
✅ DEBUG: Token is valid for user ENG2324901
📊 DEBUG: Fetching fresh grades for user ENG2324901 using token
📚 DEBUG: Retrieved 5 grades for user ENG2324901
📚 DEBUG: Previous grades count: 5
✅ DEBUG: No grade changes detected for user ENG2324901 - grades are the same as previous
```

### **Grade Changes Detected**
```
🔄 DEBUG: Grades changed for user ENG2324901
📝 DEBUG: Grade change detected for course 'MATH113'
📊 DEBUG: Found 1 grade changes for user ENG2324901
✅ DEBUG: Grade update notification sent to user ENG2324901
💾 DEBUG: Saving updated grades for user ENG2324901
```

### **API Requests**
```
🔍 DEBUG: Starting grade fetch with token...
🔍 DEBUG: Will try 8 possible pages for grades
🌐 DEBUG: Trying page: homepage
📡 DEBUG: Making request to https://api.staging.sis.shamuniversity.com/graphql for page: homepage
📡 DEBUG: Page homepage response status: 200
✅ DEBUG: Page homepage has valid data structure
🎉 DEBUG: Found 5 grades in page: homepage
```

## 🗄️ **Database Storage**

### **PostgreSQL Storage** ✅
- Tokens are properly stored in the `users` table
- `update_user_token()` method updates tokens correctly
- `get_user_session()` returns token with other session data

### **File Storage** ✅
- Tokens are stored in `users.json` file
- `update_user_token()` method updates tokens correctly
- `get_user_session()` returns token with other session data

## 🔄 **Token Lifecycle**

1. **Registration**: Token obtained and stored during user registration
2. **Validation**: Token tested before each API request
3. **Refresh**: If token expires, re-authenticate using stored credentials
4. **Update**: New token stored in database/file
5. **Invalidation**: Token cleared when user logs out or session expires

## 📈 **Benefits**

### **Performance** ⚡
- Faster API requests (no need to re-authenticate every time)
- Reduced server load on university systems
- More efficient grade checking cycles

### **Security** 🔒
- Tokens are more secure than storing passwords
- Automatic token refresh when expired
- Proper session management

### **Debugging** 🐛
- Clear visibility into API requests
- Easy tracking of grade changes
- Detailed error logging for troubleshooting

### **User Experience** 👤
- Faster response times
- More reliable grade checking
- Better error messages

## 🚀 **Deployment Notes**

1. **No Breaking Changes**: All existing functionality preserved
2. **Backward Compatible**: Works with existing user data
3. **Enhanced Logging**: More detailed logs for monitoring
4. **Token Migration**: Existing users will get tokens on next login

## 📝 **Monitoring**

### **Key Log Patterns to Watch**
- `🔍 DEBUG: Starting grade check for user` - Grade checking started
- `✅ DEBUG: Token is valid` - Token validation successful
- `🔄 DEBUG: Grades changed for user` - Grade updates detected
- `✅ DEBUG: No grade changes detected` - No updates found
- `❌ DEBUG: Token expired` - Token refresh needed

### **Performance Metrics**
- Token validation success rate
- Grade change detection frequency
- API request response times
- Re-authentication frequency

---

**Update Date**: December 2024  
**Version**: 2.0.0  
**Status**: ✅ **READY FOR DEPLOYMENT** 