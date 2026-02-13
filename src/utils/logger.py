"""
Logger Setup Utility Module.

This module provides a centralized logging configuration function for the application.
It creates file-based loggers with standardized formatting and ensures proper directory
structure creation.
"""
import logging
import os
from appdatainternal.environment import get_env_config
ENVIRONMENT_LOCAL = get_env_config()
def setup_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    """
    Configure and return a logger instance with file output.
    
    Creates a logger that writes to a specified file with timestamp, logger name,
    level, and message formatting. Automatically creates parent directories if they
    don't exist. Prevents duplicate handlers from being added to existing loggers.
    
    Args:
        name (str): Name of the logger (typically module or component name).
        log_file (str): Path to the log file where messages will be written.
        level (int, optional): Logging level (e.g., logging.INFO, logging.DEBUG).
                              Defaults to logging.INFO.
    
    Returns:
        logging.Logger: Configured logger instance ready for use.
    
    Example:
        >>> logger = setup_logger('myapp', 'log/myapp.log')
        >>> logger.info('Application started')
    
    Note:
        Log format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        File encoding: UTF-8
        File mode: Append ('a')
    """
    if ENVIRONMENT_LOCAL == "LOCAL":
        log_file = f"tmp/{log_file}"

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent adding multiple handlers if logger already exists
    if not logger.hasHandlers():
        logger.addHandler(handler)

    return logger
