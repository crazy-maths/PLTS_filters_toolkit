import logging
import os
import sys
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

def setup_logging():
    log_file = os.path.join(LOG_DIR, "app.log")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
    
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    console_stream = sys.stdout
    if sys.platform == "win32":
        import io
        console_stream = io.TextIOWrapper(
            sys.stdout.buffer, 
            encoding='utf-8', 
            errors='backslashreplace',
            line_buffering=True
        )
        
    console_handler = logging.StreamHandler(console_stream)
    console_handler.setFormatter(formatter)
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

def get_logger(name: str):
    return logging.getLogger(name)

def clear_logs():
    """Clears the contents of the application log file."""
    log_file = os.path.join(LOG_DIR, "app.log")
    try:
        if os.path.exists(log_file):
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("")
        root_logger = logging.getLogger()
        root_logger.info("Logs cleared by user.")
    except Exception as e:
        print(f"Failed to clear logs: {e}", file=sys.stderr)
        raise
