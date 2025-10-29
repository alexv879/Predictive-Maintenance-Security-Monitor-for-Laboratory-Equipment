"""
Retry utilities for handling transient failures.
"""

import time
import logging
from typing import Callable, Any, TypeVar, Optional
from functools import wraps

logger = logging.getLogger('retry_utils')

T = TypeVar('T')


def retry_on_failure(
    max_attempts: int = 3,
    delay_seconds: float = 1.0,
    backoff_multiplier: float = 2.0,
    exceptions: tuple = (Exception,),
    default_return: Any = None
) -> Callable:
    """
    Decorator to retry a function on failure with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        delay_seconds: Initial delay between retries
        backoff_multiplier: Multiply delay by this after each failure
        exceptions: Tuple of exception types to catch
        default_return: Value to return if all retries fail

    Example:
        @retry_on_failure(max_attempts=3, delay_seconds=0.5)
        def read_sensor():
            # May fail transiently
            return sensor.read()
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Optional[T]:
            delay = delay_seconds
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    if attempt > 1:
                        logger.info(f"{func.__name__} succeeded on attempt {attempt}")
                    return result
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt}/{max_attempts}): {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                        delay *= backoff_multiplier
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )

            # All attempts failed
            if default_return is not None:
                logger.warning(f"{func.__name__} returning default value: {default_return}")
                return default_return

            # Re-raise last exception if no default provided
            if last_exception:
                raise last_exception

        return wrapper
    return decorator
