import httpx

from groq import AuthenticationError, APIConnectionError, RateLimitError
from cv_optimizer.failure_messages import (
    analysis_failure_message,
    missing_api_key_message,
    over_length_message,
)

def make_response():
    request = httpx.Request("POST", "https://api.groq.com")
    return httpx.Response(401, request=request)


def test_missing_api_key_message():
    message = missing_api_key_message()

    assert "No API key is configured" in message
    assert "README" in message
    assert "restart the app" in message


def test_over_length_message():
    message = over_length_message(12400)

    assert message == (
        "This CV is 12,400 words - the limit is 10,000. "
        "Upload a shorter version."
    )


def test_invalid_api_key_message():
    error = AuthenticationError(
        "invalid api key",
        response=make_response(),
        body=None,
    )

    message = analysis_failure_message(error)

    assert "API key is invalid" in message
    assert "GROQ_API_KEY" in message


def test_provider_unreachable_message():
    error = APIConnectionError(
        message="connection failed",
        request=None,
    )

    message = analysis_failure_message(error)

    assert "could not be reached" in message
    assert "try again shortly" in message


def test_rate_limit_message():
    error = RateLimitError(
        "rate limited",
        response=make_response(),
        body=None,
    )

    message = analysis_failure_message(error)

    assert "rate-limited" in message
    assert "wait" in message
    assert "try" in message


def test_unexpected_error_does_not_expose_raw_exception():
    error = RuntimeError("SECRET INTERNAL ERROR 12345")

    message = analysis_failure_message(error)

    assert message == (
        "Something went wrong while analyzing your CV. "
        "Please try again shortly."
    )
    assert "SECRET INTERNAL ERROR 12345" not in message
