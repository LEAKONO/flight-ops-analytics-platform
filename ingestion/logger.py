import logging
import sys


def get_logger(name):
    """
    Returns a configured logger that writes structured, leveled output
    to both the console and a persistent log file.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        # Avoid adding duplicate handlers if this is called multiple times
        # (e.g. once per module) within the same process.
        return logger

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # console: INFO and above
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler("pipeline.log")
    file_handler.setLevel(logging.DEBUG)  # file: everything, including DEBUG
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger