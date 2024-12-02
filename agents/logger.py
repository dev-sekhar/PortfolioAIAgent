import logging
from config import LOG_CONFIG, LOG_LEVELS

def setup_logger(name):
    """Setup and return a logger instance"""
    # Create logger
    logger = logging.getLogger(name)
    
    # Set level from config
    logger.setLevel(LOG_LEVELS.get(LOG_CONFIG['level'], logging.INFO))
    
    # Create console handler and set level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logger.level)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt=LOG_CONFIG['format'],
        datefmt=LOG_CONFIG['date_format']
    )
    
    # Add formatter to handler
    console_handler.setFormatter(formatter)
    
    # Add handler to logger if it doesn't already have handlers
    if not logger.handlers:
        logger.addHandler(console_handler)
    
    return logger 