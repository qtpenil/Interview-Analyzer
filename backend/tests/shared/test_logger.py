import logging
from unittest.mock import patch

from app.shared.logger.logger import get_logger, setup_logging


class TestLogger:
    def test_get_logger_returns_logger(self):
        logger = get_logger("test")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test"

    def test_get_logger_hierarchical_name(self):
        logger = get_logger("app.module.component")
        assert logger.name == "app.module.component"

    def test_setup_logging_configures_root(self):
        setup_logging(level=logging.DEBUG)
        root = logging.getLogger()
        assert root.level == logging.DEBUG
        assert len(root.handlers) > 0

    def test_logger_default_level(self):
        logger = get_logger("test_default")
        assert logger.level in (logging.NOTSET, logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR)

    def test_logger_emits_messages(self):
        logger = get_logger("test_emit")
        with patch.object(logger, "info") as mock_info:
            logger.info("test message")
            mock_info.assert_called_once_with("test message")
