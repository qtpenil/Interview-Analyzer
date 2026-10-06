from unittest.mock import MagicMock, patch

import pytest

from app.integration.langGraph.retryManager import KeyRotator, RetryManager, is_transient_exception


class TestIsTransientException:
    def test_rate_limit_is_transient(self):
        exc = Exception("429 Too Many Requests")
        assert is_transient_exception(exc)

    def test_timeout_is_transient(self):
        exc = TimeoutError("Connection timed out")
        assert is_transient_exception(exc)

    def test_value_error_not_transient(self):
        exc = ValueError("Invalid input")
        assert not is_transient_exception(exc)

    def test_key_error_not_transient(self):
        exc = KeyError("Missing key")
        assert not is_transient_exception(exc)


class TestKeyRotator:
    def test_rotation_cycles_through_keys(self):
        rotator = KeyRotator("google")
        key0 = rotator.get_current_key()
        assert key0 is not None
        rotator.rotate()
        key1 = rotator.get_current_key()
        assert key1 is not None
        # With two keys configured, they should differ
        if len(rotator.keys) > 1:
            assert key1 != key0
            rotator.rotate()
            assert rotator.get_current_key() == key0  # wraps around

    def test_rotate_skips_to_next_key(self):
        rotator = KeyRotator("google")
        keys_before = rotator.keys[:]
        if len(keys_before) > 1:
            key0 = rotator.get_current_key()
            rotator.rotate()
            key1 = rotator.get_current_key()
            assert key1 != key0


class TestRetryManager:
    def test_retry_manager_initialized(self):
        manager = RetryManager()
        assert manager is not None
