from logging import Logger
import logging


def get_logger() -> Logger:

    logger = logging.getLogger("mbctl")
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

mb_logger = get_logger()
