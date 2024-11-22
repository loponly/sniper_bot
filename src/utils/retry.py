import time
from functools import wraps
from typing import Callable
import logging

def retry_on_exception(
    retries: int = 3,
    delay: int = 5,
    exceptions: tuple = (Exception,),
    logger: logging.Logger = None
):
    """Decorator for retrying functions on exception"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if logger:
                        logger.error(f"Attempt {i+1}/{retries} failed: {str(e)}")
                    if i == retries - 1:
                        raise
                    time.sleep(delay)
            return None
        return wrapper
    return decorator 