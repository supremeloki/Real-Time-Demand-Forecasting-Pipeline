import logging
import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, root_dir)
sys.path.insert(0, os.path.join(root_dir, "src"))

from src.utils.config_reader import ConfigReader


def setup_logging(name: str):
    config = ConfigReader()
    log_level = config.get("logging.level", "INFO").upper()

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if log_level == "DEBUG":
            file_handler = logging.FileHandler(f"app_{name}_debug.log")
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger
