"""
Test Security Headers Module
"""

import pytest
from security.headers import (
    SecurityHeaders,
    SecurityPolicy,
    security_headers,
    security_policy,
)
import os
import re

SEMVER_REGEX = r'^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$'
raw_version = os.getenv("BOT_VERSION", "v3.0.0")
if re.match(SEMVER_REGEX, raw_version):
    expected_version = raw_version
else:
    expected_version = "v3.0.0"


class TestSecurityHeaders:
    """Test SecurityHeaders class"""

    def test_security_headers_initialization(self):
        """Test SecurityHeaders initialization"""
        headers = SecurityHeaders()
        assert headers.csp_nonce is not None
        assert len(headers.csp_nonce) == 32  # 16 bytes = 32 hex chars
        assert headers.nonce_update_interval.total_seconds() == 3600  # 1 hour

    def test_get_security_headers(self):
        """Test getting security headers"""
        headers = SecurityHeaders()
        security_headers_dict = headers.get_security_headers()

        # Check that all required headers are present
        required_headers = [
            "Content-Security-Policy",
            "Strict-Transport-Security",
            "X-Frame-Options",
            "X-Content-Type-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Permissions-Policy",
            "Cache-Control",
            "Pragma",
            "Expires",
            "X-Permitted-Cross-Domain-Policies",
            "Cross-Origin-Embedder-Policy",
            "Cross-Origin-Opener-Policy",
            "Cross-Origin-Resource-Policy",
        ]

        for header in required_headers:
            assert header in security_headers_dict
            assert security_headers_dict[header] is not None
            assert len(security_headers_dict[header]) > 0

    def test_csp_header_content(self):
        """Test Content Security Policy header content"""
        headers = SecurityHeaders()
        csp_header = headers._get_csp_header()

        # Check that CSP contains required directives
        required_directives = [
            "default-src",
            "script-src",
            "style-src",
            "img-src",
            "font-src",
            "connect-src",
            "frame-ancestors",
            "base-uri",
            "form-action",
            "upgrade-insecure-requests",
            "block-all-mixed-content",
        ]

        for directive in required_directives:
            assert directive in csp_header

    def test_permissions_policy(self):
        """Test Permissions Policy header"""
        headers = SecurityHeaders()
        permissions_policy = headers._get_permissions_policy()

        # Check that permissions policy contains required features
        required_features = [
            "accelerometer",
            "camera",
            "geolocation",
            "microphone",
            "payment",
            "usb",
        ]

        for feature in required_features:
            assert feature in permissions_policy

    def test_get_security_metadata(self):
        """Test security metadata"""
        headers = SecurityHeaders()
        metadata = headers.get_security_metadata()

        assert metadata["security_headers_applied"] is True
        assert metadata["csp_nonce"] is not None
        assert metadata["security_level"] == "HIGH"
        assert "OWASP" in metadata["compliance"]
        assert "NIST" in metadata["compliance"]
        assert "ISO27001" in metadata["compliance"]


class TestSecurityPolicy:
    """Test SecurityPolicy class"""

    def test_security_policy_initialization(self):
        """Test SecurityPolicy initialization"""
        policy = SecurityPolicy()
        assert len(policy.allowed_domains) > 0
        assert len(policy.blocked_patterns) > 0

    def test_validate_url_allowed_domains(self):
        """Test URL validation for allowed domains"""
        policy = SecurityPolicy()

        # Test allowed domains
        assert policy.validate_url("https://api.telegram.org/bot123/sendMessage")
        assert policy.validate_url("https://api.zenquotes.io/api/random")
        assert policy.validate_url("https://api.adviceslip.com/advice")

    def test_validate_url_blocked_domains(self):
        """Test URL validation for blocked domains"""
        policy = SecurityPolicy()

        # Test blocked domains
        assert not policy.validate_url("https://malicious-site.com/evil")
        assert not policy.validate_url("http://suspicious-domain.org/api")

    def test_validate_url_blocked_patterns(self):
        """Test URL validation for blocked patterns"""
        policy = SecurityPolicy()

        # Test blocked patterns
        assert not policy.validate_url('javascript:alert("xss")')
        assert not policy.validate_url('data:text/html,<script>alert("xss")</script>')
        assert not policy.validate_url(
            "https://api.telegram.org/bot123/sendMessage?onload=evil"
        )

    def test_sanitize_input(self):
        """Test input sanitization"""
        policy = SecurityPolicy()

        # Test script removal
        input_text = '<script>alert("xss")</script>Hello World'
        sanitized = policy.sanitize_input(input_text)
        assert "<script>" not in sanitized
        assert "Hello World" in sanitized

        # Test HTML tag removal
        input_text = "<p>Hello</p><b>World</b>"
        sanitized = policy.sanitize_input(input_text)
        assert "<p>" not in sanitized
        assert "<b>" not in sanitized
        assert "Hello" in sanitized
        assert "World" in sanitized

        # Test length limiting
        long_input = "A" * 2000
        sanitized = policy.sanitize_input(long_input)
        assert len(sanitized) <= 1000

    def test_get_security_report(self):
        """Test security policy report"""
        policy = SecurityPolicy()
        report = policy.get_security_report()

        assert report["policy_version"] == expected_version
        assert len(report["allowed_domains"]) > 0
        assert report["blocked_patterns_count"] > 0
        assert report["security_level"] == "HIGH"


class TestGlobalInstances:
    """Test global security instances"""

    def test_global_security_headers(self):
        """Test global security_headers instance"""
        assert security_headers is not None
        assert isinstance(security_headers, SecurityHeaders)

        headers = security_headers.get_security_headers()
        assert "Content-Security-Policy" in headers

    def test_global_security_policy(self):
        """Test global security_policy instance"""
        assert security_policy is not None
        assert isinstance(security_policy, SecurityPolicy)

        report = security_policy.get_security_report()
        assert report["policy_version"] == expected_version


if __name__ == "__main__":
    pytest.main([__file__])
