import logging
import sys

def setup_logger(name: str = None) -> logging.Logger:

    logger = logging.getLogger(name or "Grafos")
    logger.setLevel(logging.INFO)

    # Evita log duplicado se já existir handler
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
