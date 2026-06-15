import logging
import sys

def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance.
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create handlers
        c_handler = logging.StreamHandler(sys.stdout)
        
        # Create formatters and add it to handlers
        c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        c_handler.setFormatter(c_format)
        
        # Add handlers to the logger
        logger.addHandler(c_handler)
        
    return logger
