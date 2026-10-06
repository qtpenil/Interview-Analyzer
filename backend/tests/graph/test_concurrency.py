import pytest

from app.integration.langGraph.concurrency import (
    LocalConcurrencyBackend,
    LocalSemaphore,
    deserialize_state,
    serialize_state,
)


class TestStateSerialization:
    def test_serialize_deserialize_roundtrip(self):
        state = {"key1": "value1", "key2": 42, "key3": [1, 2, 3]}
        serialized = serialize_state(state)
        deserialized = deserialize_state(serialized)
        assert deserialized == state

    def test_serialize_empty_dict(self):
        assert deserialize_state(serialize_state({})) == {}

    def test_serialize_none_values(self):
        state = {"key": None}
        assert deserialize_state(serialize_state(state)) == state


class TestLocalSemaphore:
    def test_acquire_release(self):
        sem = LocalSemaphore(1)
        assert sem.acquire("token-1") is True
        sem.release("token-1")
        assert sem.acquire("token-2") is True
        sem.release("token-2")

    def test_acquire_at_capacity(self):
        sem = LocalSemaphore(1)
        assert sem.acquire("token-1") is True
        assert sem.acquire("token-2") is False
        sem.release("token-1")
        assert sem.acquire("token-2") is True
        sem.release("token-2")


class TestLocalConcurrencyBackend:
    def test_backend_initialization(self):
        backend = LocalConcurrencyBackend()
        assert backend is not None
