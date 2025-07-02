"""
Security Enhancements Module
Implements rate limiting, audit logging, session management, and input validation
"""
import logging
import json
import validators
import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
from collections import defaultdict
import asyncio
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class SecurityEvent:
    """Security event data structure"""
    timestamp: str
    event_type: str
    user_id: int
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    success: bool = True
    risk_level: str = "LOW"

class RateLimiter:
    """Rate limiting implementation for security"""
    
    def __init__(self):
        self.attempts: Dict[int, List[datetime]] = defaultdict(list)
        self.blocked_users: Dict[int, datetime] = {}
        self.max_attempts = 5
        self.window_seconds = 300  # 5 minutes
        self.block_duration = 900  # 15 minutes
    
    def is_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to make requests"""
        now = datetime.now()
        
        # Check if user is blocked
        if user_id in self.blocked_users:
            if now < self.blocked_users[user_id]:
                return False
            else:
                del self.blocked_users[user_id]
        
        # Clean old attempts
        self._clean_old_attempts(user_id, now)
        
        # Check current attempts
        if len(self.attempts[user_id]) >= self.max_attempts:
            self.blocked_users[user_id] = now + timedelta(seconds=self.block_duration)
            return False
        
        return True
    
    def record_attempt(self, user_id: int, success: bool = True):
        """Record a user attempt"""
        now = datetime.now()
        self.attempts[user_id].append(now)
        
        if not success:
            # Failed attempts count more heavily
            self.attempts[user_id].append(now)
            self.attempts[user_id].append(now)
        
        # Check if user should be blocked after this attempt
        if len(self.attempts[user_id]) >= self.max_attempts:
            self.blocked_users[user_id] = now + timedelta(seconds=self.block_duration)
    
    def _clean_old_attempts(self, user_id: int, now: datetime):
        """Remove attempts older than the window"""
        cutoff = now - timedelta(seconds=self.window_seconds)
        self.attempts[user_id] = [
            attempt for attempt in self.attempts[user_id] 
            if attempt > cutoff
        ]
    
    def get_attempts_count(self, user_id: int) -> int:
        """Get current attempts count for user"""
        now = datetime.now()
        self._clean_old_attempts(user_id, now)
        return len(self.attempts[user_id])

class AuditLogger:
    """Enhanced audit logging system"""
    
    def __init__(self, log_file: str = "logs/security_audit.log"):
        self.log_file = log_file
        self.events: List[SecurityEvent] = []
        self.max_events = 1000  # Keep last 1000 events in memory
    
    def log_security_event(self, event_type: str, user_id: int, 
                          details: Dict[str, Any], success: bool = True,
                          risk_level: str = "LOW", ip_address: Optional[str] = None,
                          user_agent: Optional[str] = None):
        """Log a security event"""
        event = SecurityEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            user_id=user_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            risk_level=risk_level
        )
        
        # Add to memory
        self.events.append(event)
        if len(self.events) > self.max_events:
            self.events.pop(0)
        
        # Log to file
        self._write_to_file(event)
        
        # Log to console for high-risk events
        if risk_level in ["HIGH", "CRITICAL"]:
            logger.warning(f"SECURITY ALERT: {event_type} - User {user_id} - {risk_level}")
    
    def _write_to_file(self, event: SecurityEvent):
        """Write event to log file"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(event), ensure_ascii=False) + '\n')
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def get_recent_events(self, hours: int = 24) -> List[SecurityEvent]:
        """Get recent security events"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return [
            event for event in self.events
            if datetime.fromisoformat(event.timestamp) > cutoff
        ]
    
    def get_events_by_type(self, event_type: str) -> List[SecurityEvent]:
        """Get events by type"""
        return [event for event in self.events if event.event_type == event_type]
    
    def get_events_by_user(self, user_id: int) -> List[SecurityEvent]:
        """Get events by user ID"""
        return [event for event in self.events if event.user_id == user_id]

class SessionManager:
    """Enhanced session management"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = 3600  # 1 hour
        self.max_sessions_per_user = 3
    
    def create_session(self, user_id: int, token: str, user_data: Dict[str, Any] | None = None):
        """Create a new session for user"""
        now = datetime.now()
        
        # Clean old sessions for this user
        self._clean_user_sessions(user_id)
        
        # Check session limit
        if len([s for s in self.sessions.values() if s.get('user_id') == user_id]) >= self.max_sessions_per_user:
            # Remove oldest session
            oldest_session = min(
                [s for s in self.sessions.values() if s.get('user_id') == user_id],
                key=lambda x: x.get('created_at', now)
            )
            session_id = oldest_session.get('session_id')
            if session_id:
                del self.sessions[session_id]
        
        # Create new session
        session_id = f"{user_id}_{now.timestamp()}"
        self.sessions[session_id] = {
            'session_id': session_id,
            'user_id': user_id,
            'token': token,
            'user_data': user_data or {},
            'created_at': now,
            'last_activity': now,
            'is_active': True
        }
        
        return session_id
    
    def get_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get active session for user"""
        self._clean_expired_sessions()
        
        for session in self.sessions.values():
            if session.get('user_id') == user_id and session.get('is_active'):
                session['last_activity'] = datetime.now()
                return session
        
        return None
    
    def update_session_activity(self, user_id: int):
        """Update session activity timestamp"""
        session = self.get_session(user_id)
        if session:
            session['last_activity'] = datetime.now()
    
    def invalidate_session(self, user_id: int):
        """Invalidate user session"""
        for session in self.sessions.values():
            if session.get('user_id') == user_id:
                session['is_active'] = False
    
    def _clean_user_sessions(self, user_id: int):
        """Clean old sessions for specific user"""
        now = datetime.now()
        sessions_to_remove = []
        
        for session_id, session in self.sessions.items():
            if session.get('user_id') == user_id:
                last_activity = session.get('last_activity', now)
                if (now - last_activity).total_seconds() > self.session_timeout:
                    sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
    
    def _clean_expired_sessions(self):
        """Clean all expired sessions"""
        now = datetime.now()
        sessions_to_remove = []
        
        for session_id, session in self.sessions.items():
            last_activity = session.get('last_activity', now)
            if (now - last_activity).total_seconds() > self.session_timeout:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.sessions[session_id]

class SecurityManager:
    """Main security manager that coordinates all security features"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.audit_logger = AuditLogger()
        self.session_manager = SessionManager()
    
    def check_login_attempt(self, user_id: int, ip_address: Optional[str] = None) -> bool:
        """Check if login attempt is allowed"""
        if not self.rate_limiter.is_allowed(user_id):
            self.audit_logger.log_security_event(
                "LOGIN_BLOCKED", user_id, 
                {"reason": "rate_limit_exceeded", "ip_address": ip_address},
                success=False, risk_level="MEDIUM"
            )
            return False
        return True
    
    def record_login_attempt(self, user_id: int, success: bool, 
                           username: str, ip_address: Optional[str] = None):
        """Record login attempt"""
        self.rate_limiter.record_attempt(user_id, success)
        
        event_type = "LOGIN_SUCCESS" if success else "LOGIN_FAILED"
        risk_level = "LOW" if success else "MEDIUM"
        
        self.audit_logger.log_security_event(
            event_type, user_id,
            {"username": username, "ip_address": ip_address},
            success=success, risk_level=risk_level
        )
    
    def create_user_session(self, user_id: int, token: str, user_data: Dict[str, Any] | None = None):
        """Create user session"""
        session_id = self.session_manager.create_session(user_id, token, user_data)
        self.audit_logger.log_security_event(
            "SESSION_CREATED", user_id,
            {"session_id": session_id, "user_data_keys": list(user_data.keys()) if user_data else []}
        )
        return session_id
    
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        # Get recent events (last 24 hours)
        recent_events = self.audit_logger.get_recent_events(24)
        failed_logins = len([e for e in recent_events if e.event_type == "LOGIN_FAILED"])
        
        return {
            "total_events_24h": len(recent_events),
            "failed_logins": failed_logins,
            "rate_limiter": {
                "blocked_users": len(self.rate_limiter.blocked_users),
                "total_attempts": sum(len(attempts) for attempts in self.rate_limiter.attempts.values())
            },
            "audit_logger": {
                "total_events": len(self.audit_logger.events),
                "recent_events": len(recent_events)
            },
            "session_manager": {
                "active_sessions": len([s for s in self.session_manager.sessions.values() if s.get('is_active')])
            }
        }

# Global security manager instance
security_manager = SecurityManager()

# Password hashing functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)

def is_password_hashed(password: str) -> bool:
    """Check if password is already hashed"""
    return password.startswith('$2b$')

def migrate_plain_password(password: str) -> str:
    """Migrate plain text password to hash"""
    if is_password_hashed(password):
        return password
    return hash_password(password)

# Input validation functions
def is_valid_email(email: str) -> bool:
    """Validate email format"""
    return validators.email(email) is True

def is_valid_url(url: str) -> bool:
    """Validate URL format"""
    return validators.url(url) is True

def is_valid_ipv4(ip: str) -> bool:
    """Validate IPv4 format"""
    return validators.ipv4(ip) is True

def is_valid_length(value: str, min_len: int | None = None, max_len: int | None = None) -> bool:
    """Validate string length"""
    if not isinstance(value, str):
        return False
    
    if min_len is not None and len(value) < min_len:
        return False
    
    if max_len is not None and len(value) > max_len:
        return False
    
    return True 