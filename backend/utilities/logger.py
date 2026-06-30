import os
import logging
from logging.handlers import RotatingFileHandler

# Define log directory
LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs"))
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logger(logger_name: str, log_file_name: str, level=logging.INFO) -> logging.Logger:
    """
    Utility function to configure and retrieve rotating file loggers.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers if logger is re-initialized
    if not logger.handlers:
        log_file_path = os.path.join(LOG_DIR, log_file_name)
        
        # Rotating File Handler: Max 10MB per file, keeping up to 5 backups
        file_handler = RotatingFileHandler(
            log_file_path, maxBytes=10 * 1024 * 1024, backupCount=5
        )
        
        # Format logs professionally
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] [TraceId: %(message)s]'
        )
        # Custom format helper to support structured and plain messages
        simple_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
        )
        
        file_handler.setFormatter(simple_formatter)
        logger.addHandler(file_handler)
        
        # Console Handler
        console_handler = logging.StreamHandler()
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
