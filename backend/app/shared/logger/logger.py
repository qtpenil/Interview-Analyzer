import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s"


def setup_logging(level: int = logging.INFO):
    """
    Configure application-wide logging.
    Call once during startup.

    Handlers are attached both to the root logger AND to a dedicated "app"
    logger. The "app" logger is set to NOT propagate, so that framework
    logging bootstrap (e.g. Celery's worker, which clears/replaces the root
    logger handlers) cannot silently drop our application logs.
    """

    formatter = logging.Formatter(LOG_FORMAT)

    # Console output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        filename=LOG_DIR / "application.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    handlers = [console_handler, file_handler]

    # Root logger — best effort, may be overridden by frameworks (e.g. Celery).
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    for handler in handlers:
        if handler not in root_logger.handlers:
            root_logger.addHandler(handler)

    # Dedicated "app" logger — immune to root handler manipulation.
    app_logger = logging.getLogger("app")
    app_logger.setLevel(level)
    app_logger.propagate = False
    for handler in handlers:
        if handler not in app_logger.handlers:
            app_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    """

    return logging.getLogger(name)
