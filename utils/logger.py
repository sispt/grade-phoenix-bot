"""
Enhanced Logging System for grade-phoenix-bot
Provides structured logging with different loggers for each component
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from config import CONFIG

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
        
        # Add timestamp with emoji
        record.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Add component emoji based on logger name
        component_emojis = {
            'bot': '🤖',
            'database': '🗄️',
            'api': '🌐',
            'security': '🔒',
            'admin': '👨‍💻',
            'migration': '🔄',
            'storage': '💾',
            'university': '🎓',
            'utils': '🛠️',
            'main': '🚀'
        }
        
        record.component_emoji = '📝'
        for component, emoji in component_emojis.items():
            if component in record.name.lower():
                record.component_emoji = emoji
                break
        
        return super().format(record)

def setup_logging():
    """Setup comprehensive logging system"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path(CONFIG.get("LOGS_DIR", "logs"))
    log_dir.mkdir(exist_ok=True)
    
    # Get log level from config
    log_level = getattr(logging, CONFIG.get("LOG_LEVEL", "INFO").upper())
    
    # Create formatters
    console_formatter = ColoredFormatter(
        '%(component_emoji)s %(timestamp)s - %(levelname)s - %(name)s: %(message)s'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    log_file = log_dir / CONFIG.get("LOG_FILE", "bot.log")
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=CONFIG.get("LOG_MAX_SIZE_MB", 10) * 1024 * 1024,  # Convert MB to bytes
        backupCount=CONFIG.get("LOG_BACKUP_COUNT", 5),
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Error file handler
    error_log_file = log_dir / "errors.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_file,
        maxBytes=CONFIG.get("LOG_MAX_SIZE_MB", 10) * 1024 * 1024,
        backupCount=CONFIG.get("LOG_BACKUP_COUNT", 5),
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # Log startup message
    logger = logging.getLogger("main")
    logger.info("🔧 Logging system initialized successfully")
    logger.info(f"📁 Log directory: {log_dir.absolute()}")
    logger.info(f"📊 Log level: {CONFIG.get('LOG_LEVEL', 'INFO')}")
    logger.info(f"🔄 Bot version: {CONFIG.get('BOT_VERSION', 'unknown')}")

def get_logger(name):
    """Get a logger with the specified name"""
    return logging.getLogger(name)

# Component-specific loggers
def get_bot_logger():
    """Get logger for bot core functionality"""
    return get_logger("bot.core")

def get_database_logger():
    """Get logger for database operations"""
    return get_logger("database")

def get_api_logger():
    """Get logger for API operations"""
    return get_logger("api")

def get_security_logger():
    """Get logger for security operations"""
    return get_logger("security")

def get_admin_logger():
    """Get logger for admin operations"""
    return get_logger("admin")

def get_migration_logger():
    """Get logger for migration operations"""
    return get_logger("migration")

def get_storage_logger():
    """Get logger for storage operations"""
    return get_logger("storage")

def get_university_logger():
    """Get logger for university API operations"""
    return get_logger("university")

def get_utils_logger():
    """Get logger for utility operations"""
    return get_logger("utils")

# Initialize logging when module is imported
setup_logging()

# Log module import
logger = get_logger("utils.logger")
logger.info("📦 Logger module imported and initialized") 