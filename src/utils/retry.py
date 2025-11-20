"""Retry utilities for network operations and other transient failures.

This module provides pre-configured tenacity decorators for common retry scenarios.
You can also use tenacity decorators directly if you need more control.
"""

import logging

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from exceptions import CensusAPIError, NetworkError

logger = logging.getLogger(__name__)


def log_retry(retry_state):
    """Log retry attempts."""
    logger.warning(
        f"Attempt {retry_state.attempt_number} failed for "
        f"{retry_state.fn.__name__}: {retry_state.outcome.exception()}. Retrying..."
    )


def log_final_failure(retry_state):
    """Log final failure after all attempts."""
    logger.error(
        f"All attempts failed for {retry_state.fn.__name__}: {retry_state.outcome.exception()}"
    )


# Pre-configured retry decorators for common use cases

retry_with_backoff = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1.0, max=60.0),
    retry=retry_if_exception_type((Exception,)),
    reraise=True,
    before_sleep=log_retry,
    after=log_final_failure,
)

retry_on_rate_limit = retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=60.0, max=300.0),
    retry=retry_if_exception_type((CensusAPIError, NetworkError, Exception)),
    reraise=True,
    before_sleep=log_retry,
    after=log_final_failure,
)
