"""Sanitizer for removing sensitive information from SQL queries."""

import re
from typing import Optional


class QuerySanitizer:
    """Sanitizes SQL queries to remove sensitive information."""

    # Patterns for sensitive data
    PATTERNS = [
        # Password patterns
        (r"PASSWORD\s*=\s*['\"]([^'\"]+)['\"]", "PASSWORD='***'"),
        (r"PASSWORD\s*=\s*(\S+)", "PASSWORD=***"),

        # API key patterns
        (r"API_KEY\s*=\s*['\"]([^'\"]+)['\"]", "API_KEY='***'"),
        (r"APIKEY\s*=\s*['\"]([^'\"]+)['\"]", "APIKEY='***'"),

        # Token patterns
        (r"TOKEN\s*=\s*['\"]([^'\"]+)['\"]", "TOKEN='***'"),
        (r"BEARER\s+['\"]?([A-Za-z0-9\-._~+/]+=*)['\"]?", "BEARER '***'"),

        # Secret patterns
        (r"SECRET\s*=\s*['\"]([^'\"]+)['\"]", "SECRET='***'"),

        # Credit card patterns (simple version)
        (r"\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b", "****-****-****-****"),

        # AWS keys
        (r"AKIA[0-9A-Z]{16}", "AKIA****************"),

        # Generic credential patterns in connection strings
        (r"(://[^:/@]+:)([^@]+)(@)", r"\1***\3"),
    ]

    MAX_PREVIEW_LENGTH = 100

    @staticmethod
    def sanitize(query_text: Optional[str]) -> str:
        """Remove sensitive information from query text.

        Args:
            query_text: The SQL query text to sanitize

        Returns:
            Sanitized query text
        """
        if not query_text:
            return ""

        sanitized = query_text

        # Apply all sanitization patterns
        for pattern, replacement in QuerySanitizer.PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

        return sanitized

    @staticmethod
    def create_preview(query_text: Optional[str], max_length: int = MAX_PREVIEW_LENGTH) -> str:
        """Create a sanitized preview of the query text.

        Args:
            query_text: The SQL query text
            max_length: Maximum length of preview (default: 100)

        Returns:
            Sanitized and truncated query preview
        """
        if not query_text:
            return ""

        # First sanitize, then truncate
        sanitized = QuerySanitizer.sanitize(query_text)

        if len(sanitized) <= max_length:
            return sanitized

        return sanitized[:max_length]
