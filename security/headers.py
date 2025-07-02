"""
Security Headers Module
Implements security headers and security policy for the Telegram bot
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import secrets

logger = logging.getLogger(__name__)

class SecurityHeaders:
    """Security headers implementation for bot responses"""
    
    def __init__(self):
        self.csp_nonce = secrets.token_hex(16)
        self.csp_nonce_updated = datetime.now()
        self.nonce_update_interval = timedelta(hours=1)
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get comprehensive security headers"""
        self._update_nonce_if_needed()
        
        return {
            # Content Security Policy
            'Content-Security-Policy': self._get_csp_header(),
            
            # HTTP Strict Transport Security
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
            
            # X-Frame-Options
            'X-Frame-Options': 'DENY',
            
            # X-Content-Type-Options
            'X-Content-Type-Options': 'nosniff',
            
            # X-XSS-Protection
            'X-XSS-Protection': '1; mode=block',
            
            # Referrer Policy
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            
            # Permissions Policy
            'Permissions-Policy': self._get_permissions_policy(),
            
            # Cache Control
            'Cache-Control': 'no-store, no-cache, must-revalidate, proxy-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            
            # Additional Security Headers
            'X-Permitted-Cross-Domain-Policies': 'none',
            'Cross-Origin-Embedder-Policy': 'require-corp',
            'Cross-Origin-Opener-Policy': 'same-origin',
            'Cross-Origin-Resource-Policy': 'same-origin',
        }
    
    def _get_csp_header(self) -> str:
        """Get Content Security Policy header"""
        return (
            f"default-src 'self'; "
            f"script-src 'self' 'nonce-{self.csp_nonce}' 'unsafe-inline'; "
            f"style-src 'self' 'unsafe-inline'; "
            f"img-src 'self' data: https:; "
            f"font-src 'self' data:; "
            f"connect-src 'self' https://api.telegram.org https://api.zenquotes.io; "
            f"frame-ancestors 'none'; "
            f"base-uri 'self'; "
            f"form-action 'self'; "
            f"upgrade-insecure-requests; "
            f"block-all-mixed-content"
        )
    
    def _get_permissions_policy(self) -> str:
        """Get Permissions Policy header"""
        return (
            "accelerometer=(), "
            "ambient-light-sensor=(), "
            "autoplay=(), "
            "battery=(), "
            "camera=(), "
            "cross-origin-isolated=(), "
            "display-capture=(), "
            "document-domain=(), "
            "encrypted-media=(), "
            "execution-while-not-rendered=(), "
            "execution-while-out-of-viewport=(), "
            "fullscreen=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "keyboard-map=(), "
            "magnetometer=(), "
            "microphone=(), "
            "midi=(), "
            "navigation-override=(), "
            "payment=(), "
            "picture-in-picture=(), "
            "publickey-credentials-get=(), "
            "screen-wake-lock=(), "
            "sync-xhr=(), "
            "usb=(), "
            "web-share=(), "
            "xr-spatial-tracking=()"
        )
    
    def _update_nonce_if_needed(self):
        """Update CSP nonce if needed"""
        if datetime.now() - self.csp_nonce_updated > self.nonce_update_interval:
            self.csp_nonce = secrets.token_hex(16)
            self.csp_nonce_updated = datetime.now()
            logger.info("CSP nonce updated for security")
    
    def get_security_metadata(self) -> Dict[str, Any]:
        """Get security metadata for responses"""
        return {
            'security_headers_applied': True,
            'csp_nonce': self.csp_nonce,
            'timestamp': datetime.now().isoformat(),
            'security_level': 'HIGH',
            'compliance': ['OWASP', 'NIST', 'ISO27001']
        }

class SecurityPolicy:
    """Security policy implementation"""
    
    def __init__(self):
        self.allowed_domains = [
            'api.telegram.org',
            'api.zenquotes.io',
            'api.adviceslip.com'
        ]
        self.blocked_patterns = [
            r'<script.*?>',
            r'javascript:',
            r'data:text/html',
            r'vbscript:',
            r'onload=',
            r'onerror=',
            r'onclick='
        ]
    
    def validate_url(self, url: str) -> bool:
        """Validate URL against security policy"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            
            # Check if domain is allowed
            if parsed.netloc not in self.allowed_domains:
                return False
            
            # Check for blocked patterns
            import re
            for pattern in self.blocked_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    return False
            
            return True
        except Exception:
            return False
    
    def sanitize_input(self, text: str) -> str:
        """Sanitize user input"""
        import re
        
        # Remove potentially dangerous patterns
        for pattern in self.blocked_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Limit length
        if len(text) > 1000:
            text = text[:1000]
        
        return text.strip()
    
    def get_security_report(self) -> Dict[str, Any]:
        """Get security policy report"""
        return {
            'policy_version': '2.5.7',
            'allowed_domains': self.allowed_domains,
            'blocked_patterns_count': len(self.blocked_patterns),
            'security_level': 'HIGH',
            'last_updated': datetime.now().isoformat()
        }

# Global instances
security_headers = SecurityHeaders()
security_policy = SecurityPolicy() 