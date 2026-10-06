from unittest.mock import patch

import pytest

from app.integration.langGraph.provider_strategy import ProviderManager


class TestProviderManager:
    def test_provider_manager_initialized(self):
        manager = ProviderManager()
        assert manager is not None

    def test_get_provider(self):
        manager = ProviderManager()
        provider = manager.get_provider("google")
        assert provider is not None

    def test_get_provider_invalid(self):
        manager = ProviderManager()
        with pytest.raises(Exception):
            manager.get_provider("nonexistent_provider")

    def test_google_provider_builds_model(self):
        with patch("app.integration.langGraph.provider_strategy.ChatGoogleGenerativeAI") as mock:
            manager = ProviderManager()
            provider = manager.get_provider("google")
            provider.build_model(api_key="fake-key")
            mock.assert_called()

    def test_openai_provider_builds_model(self):
        with patch("app.integration.langGraph.provider_strategy.ChatOpenAI") as mock:
            manager = ProviderManager()
            provider = manager.get_provider("openai")
            provider.build_model(api_key="sk-fake")
            mock.assert_called()
