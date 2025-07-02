#!/usr/bin/env python3
"""
Logger utility for XML Fiscal Manager Pro
Centralized logging configuration and utilities
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime


def setup_logging(log_level=logging.INFO, log_dir="logs"):
    """
    Setup centralized logging for the application
    
    Args:
        log_level: Logging level (default: INFO)
        log_dir: Directory for log files (default: "logs")
    """
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler - detailed logging
    log_file = log_path / f"xml_fiscal_manager_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Console handler - simple logging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # Create specialized loggers
    
    # Database operations logger
    db_logger = logging.getLogger('database')
    db_file_handler = logging.handlers.RotatingFileHandler(
        log_path / f"database_{datetime.now().strftime('%Y%m%d')}.log",
        maxBytes=5*1024*1024,
        backupCount=3,
        encoding='utf-8'
    )
    db_file_handler.setFormatter(detailed_formatter)
    db_logger.addHandler(db_file_handler)
    
    # XML processing logger
    xml_logger = logging.getLogger('xml_processor')
    xml_file_handler = logging.handlers.RotatingFileHandler(
        log_path / f"xml_processing_{datetime.now().strftime('%Y%m%d')}.log",
        maxBytes=5*1024*1024,
        backupCount=3,
        encoding='utf-8'
    )
    xml_file_handler.setFormatter(detailed_formatter)
    xml_logger.addHandler(xml_file_handler)
    
    # Authentication logger
    auth_logger = logging.getLogger('auth')
    auth_file_handler = logging.handlers.RotatingFileHandler(
        log_path / f"auth_{datetime.now().strftime('%Y%m%d')}.log",
        maxBytes=2*1024*1024,
        backupCount=3,
        encoding='utf-8'
    )
    auth_file_handler.setFormatter(detailed_formatter)
    auth_logger.addHandler(auth_file_handler)
    
    # UI operations logger
    ui_logger = logging.getLogger('ui')
    ui_file_handler = logging.handlers.RotatingFileHandler(
        log_path / f"ui_{datetime.now().strftime('%Y%m%d')}.log",
        maxBytes=3*1024*1024,
        backupCount=3,
        encoding='utf-8'
    )
    ui_file_handler.setFormatter(detailed_formatter)
    ui_logger.addHandler(ui_file_handler)
    
    # Log initial setup message
    logger.info("Logging system initialized")
    logger.info(f"Log files location: {log_path.absolute()}")
    
    return logger


def get_logger(name=None):
    """
    Get a logger instance
    
    Args:
        name: Logger name (default: None for root logger)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def log_function_call(func):
    """
    Decorator to log function calls
    
    Usage:
        @log_function_call
        def my_function():
            pass
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling function: {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Function {func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Function {func.__name__} failed with error: {e}")
            raise
    return wrapper


def log_performance(func):
    """
    Decorator to log function performance
    
    Usage:
        @log_performance
        def my_function():
            pass
    """
    import time
    
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            logger.info(f"Function {func.__name__} executed in {execution_time:.4f} seconds")
            return result
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            logger.error(f"Function {func.__name__} failed after {execution_time:.4f} seconds: {e}")
            raise
    
    return wrapper


class ContextLogger:
    """
    Context manager for logging with additional context
    
    Usage:
        with ContextLogger("Processing XML files") as logger:
            logger.info("Processing file 1")
            logger.info("Processing file 2")
    """
    
    def __init__(self, context_name, logger_name=None):
        self.context_name = context_name
        self.logger = get_logger(logger_name)
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting: {self.context_name}")
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        if exc_type is None:
            self.logger.info(f"Completed: {self.context_name} (Duration: {duration})")
        else:
            self.logger.error(f"Failed: {self.context_name} (Duration: {duration}) - Error: {exc_val}")
        
        return False  # Don't suppress exceptions


# Setup default logging on module import
if not logging.getLogger().handlers:
    setup_logging() 