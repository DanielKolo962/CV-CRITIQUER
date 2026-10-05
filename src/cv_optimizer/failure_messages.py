from groq import AuthenticationError, APIConnectionError, RateLimitError


def missing_api_key_message() -> str:
    return (
        "No API key is configured. "
        "See the README for how to add one, then restart the app."
    )


def over_length_message(word_count: int) -> str:
    return (
        f"This CV is {word_count:,} words - the limit is 10,000. "
        "Upload a shorter version."
    )


def analysis_failure_message(error: Exception) -> str:
    if isinstance(error, AuthenticationError):
        return (
            "The API key is invalid. "
            "Check your GROQ_API_KEY and try again."
        )

    if isinstance(error, APIConnectionError):
        return (
            "The analysis service could not be reached. "
            "Please try again shortly."
        )

    if isinstance(error, RateLimitError):
        return (
            "The analysis service has rate-limited your request. "
            "Please wait a moment before trying again."
        )

    return (
        "Something went wrong while analyzing your CV. "
        "Please try again shortly."
    )
