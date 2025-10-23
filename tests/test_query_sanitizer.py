"""Tests for query sanitizer."""

import pytest
from entropydata_connector.query_sanitizer import QuerySanitizer


def test_sanitize_password():
    """Test sanitizing password in query."""
    query = "CREATE USER foo PASSWORD='secret123' ROLE admin"
    sanitized = QuerySanitizer.sanitize(query)
    assert "secret123" not in sanitized
    assert "PASSWORD=" in sanitized
    assert "***" in sanitized


def test_sanitize_api_key():
    """Test sanitizing API key in query."""
    query = "SET API_KEY='abc123xyz'"
    sanitized = QuerySanitizer.sanitize(query)
    assert "abc123xyz" not in sanitized
    assert "API_KEY='***'" in sanitized


def test_sanitize_connection_string():
    """Test sanitizing connection string with credentials."""
    query = "CONNECT TO postgresql://user:password@host/db"
    sanitized = QuerySanitizer.sanitize(query)
    assert "password" not in sanitized or "://user:***@host/db" in sanitized


def test_sanitize_none():
    """Test sanitizing None returns empty string."""
    assert QuerySanitizer.sanitize(None) == ""


def test_sanitize_empty():
    """Test sanitizing empty string."""
    assert QuerySanitizer.sanitize("") == ""


def test_create_preview():
    """Test creating query preview."""
    long_query = "SELECT " + ", ".join([f"col{i}" for i in range(100)])
    preview = QuerySanitizer.create_preview(long_query)

    assert len(preview) <= 100
    assert preview.startswith("SELECT")


def test_create_preview_short_query():
    """Test creating preview of short query."""
    short_query = "SELECT * FROM users"
    preview = QuerySanitizer.create_preview(short_query)

    assert preview == short_query


def test_create_preview_with_sensitive_data():
    """Test preview sanitizes sensitive data."""
    query = "SELECT * FROM users WHERE password='secret123'"
    preview = QuerySanitizer.create_preview(query)

    assert "secret123" not in preview
    assert "***" in preview
