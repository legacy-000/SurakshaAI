import os
import logging
import sys

# Define log directory - use /tmp in serverless environments
_LOG_DIR = os.environ.get("LOG_DIR", "")
if not _LOG_DIR:
    try:
        _LOG_DIR = os.path.join(os.path.sep, "tmp", "logs")
        os.makedirs(_LOG_DIR, exist_ok=True)
    except OSError:
        _LOG_DIR = None

def setup_logger(logger_name: str, log_file_name: str = "", level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    if not logger.handlers:
        simple_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
        )
        
        if _LOG_DIR and log_file_name:
            log_file_path = os.path.join(_LOG_DIR, log_file_name)
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_file_path, maxBytes=10 * 1024 * 1024, backupCount=5
            )
            file_handler.setFormatter(simple_formatter)
            logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
        
    return logger

# --- Global Logger Placeholders ---
ChatLogger = setup_logger("ChatLogger", "chat.log")
AnalyticsLogger = setup_logger("AnalyticsLogger", "analytics.log")
PredictionLogger = setup_logger("PredictionLogger", "prediction.log")
NetworkLogger = setup_logger("NetworkLogger", "network.log")
ReportLogger = setup_logger("ReportLogger", "report.log")
SystemLogger = setup_logger("SystemLogger", "system.log")
