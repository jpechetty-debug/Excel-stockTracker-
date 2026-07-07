"""
Retry Wrapper
Provides generic, decoupled retry logic using tenacity.
"""

import functools
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import requests
from domain.exceptions import ProviderUnavailableError
from infrastructure.logging.logger import logger

def log_retry_attempt(retry_state):
    """Callback to log retry attempts."""
    exception = retry_state.outcome.exception()
    logger.warning(
        f"Retrying {retry_state.fn.__name__} due to {type(exception).__name__}: {exception}. "
        f"Attempt {retry_state.attempt_number}"
    )


# A standard, reusable retry decorator for network/API calls
with_api_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((requests.RequestException, ProviderUnavailableError)),
    before_sleep=log_retry_attempt,
    reraise=True
)

def api_retry_policy(func):
    """Wraps functions with standard API retry rules."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return with_api_retry(func)(*args, **kwargs)
    return wrapper
