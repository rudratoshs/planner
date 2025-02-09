# src/utils/logger.py
import logging
import json
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from ..config.environment import env

# Log directory setup
LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, f"{env.SERVICE_NAME}.log")

# Custom JSON formatter
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if record.args:
            log_record.update(record.args)
        return json.dumps(log_record)

def setup_logging():
    logger = logging.getLogger(env.SERVICE_NAME)
    logger.setLevel(logging.INFO)

    # Console Handler (JSON format)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

    # File Handler (with log rotation)
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f"Could not set up file logging: {str(e)}")

    return logger

# Initialize logger
logger = setup_logging()