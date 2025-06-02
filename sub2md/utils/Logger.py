import logging
import sys
from pathlib import Path
from typing import Optional

class Logger:
    """Configure and manage logging for the Substack scraper."""
    
    def __init__(self, debug: bool = False, log_file: Optional[str] = None):
        """
        Initialize the logger.
        
        Args:
            debug (bool): Enable debug logging
            log_file (Optional[str]): Path to log file. If None, logs to console only
        """
        self.logger = logging.getLogger('sub2md')
        self.logger.setLevel(logging.DEBUG if debug else logging.INFO)
        
        # Clear any existing handlers
        self.logger.handlers = []
        
        # Create formatters
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str) -> None:
        """Log a debug message."""
        self.logger.debug(message)
    
    def info(self, message: str) -> None:
        """Log an info message."""
        self.logger.info(message)
    
    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.logger.warning(message)
    
    def error(self, message: str) -> None:
        """Log an error message."""
        self.logger.error(message)
    
    def critical(self, message: str) -> None:
        """Log a critical message."""
        self.logger.critical(message)
    
    def exception(self, message: str) -> None:
        """Log an exception message with traceback."""
        self.logger.exception(message) 