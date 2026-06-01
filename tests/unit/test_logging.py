import logging
from pathlib import Path

from idp.common.logging_config import get_logger, setup_logging


def test_setup_logging(tmp_path: Path) -> None:
    """Test logging setup."""
    # Reset logging handlers before test to ensure our new ones take effect
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    log_file = tmp_path / "test.log"
    setup_logging(log_level="DEBUG", log_file=str(log_file))

    logger = logging.getLogger("test")
    logger.debug("test message")

    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "test message" in content


def test_get_logger() -> None:
    """Test getting a logger instance."""
    logger = get_logger("test_module")
    assert logger.name == "test_module"
    assert isinstance(logger, logging.Logger)
