"""Shared retry policy for every outbound external-API call in the project.

Rationale: the brief requires real retry/backoff on every external call rather
than each module rolling its own. `tenacity` gives us exponential backoff with
jitter and a hard attempt cap so a flaky provider degrades (raises after
retries exhausted) instead of hanging or crashing the whole pipeline.
"""

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

# Network/rate-limit errors are worth retrying; programming errors (bad args,
# auth failures) are not — callers should let those raise immediately by
# raising a non-retryable exception type from their client code.


def external_api_retry(exception_types: tuple[type[Exception], ...], attempts: int = 4):
    return retry(
        reraise=True,
        stop=stop_after_attempt(attempts),
        wait=wait_exponential_jitter(initial=1, max=20),
        retry=retry_if_exception_type(exception_types),
    )
