from logging import Logger
import logging
from rich.logging import RichHandler


def get_logger() -> Logger:

    logger = logging.getLogger("mbctl")
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        ch = RichHandler(
            show_time=True,
            show_level=True,
            show_path=False,
            rich_tracebacks=True,
            markup=True,
        )
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter("%(message)s")
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

mb_logger = get_logger()
