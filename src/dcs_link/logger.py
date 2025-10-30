import logging
import sys

class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, '')

        formatted_message = super().format(record)
        
        if color and hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            return f"{color}{formatted_message}{self.RESET}"
        
        return formatted_message

class Logger():    
    def __init__(self, name: str = __package__, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = ColoredFormatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def debug(self, message: str): 
        self.logger.debug(message)
    
    def info(self, message: str): 
        self.logger.info(message)
    
    def warning(self, message: str): 
        self.logger.warning(message)
    
    def error(self, message: str): 
        self.logger.error(message)
    
    def critical(self, message: str): 
        self.logger.critical(message)