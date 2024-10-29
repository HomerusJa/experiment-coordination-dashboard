"""Define exceptions that can be raised by the S³I client."""


class S3IException(Exception):
    """Base exception for all S³I-related exceptions."""

    def __init__(
        self,
        message: str,
        headers: dict | str | None = None,
        body: dict | str | None = None,
        status_code: int | None = None,
        response: str | None = None,
    ):
        """Initialize an S3IException instance.

        Args:
            message (str): The error message.
            headers (dict | str | None, optional): The headers associated with the error.
            body (dict | str | None, optional): The body of the error response.
            status_code (int | None, optional): The HTTP status code.
            response (str | None, optional): The full response as a string.
        """
        super().__init__(message)

        self.headers = headers
        self.body = body
        self.status_code = status_code
        self.response = response

    def __str__(self):
        """Return a string representation of the exception with all metadata."""
        base_message = super().__str__()
        metadata = []

        if self.headers is not None:
            metadata.append(f"Headers: {self.headers}")
        if self.body is not None:
            metadata.append(f"Body: {self.body}")
        if self.status_code is not None:
            metadata.append(f"Status Code: {self.status_code}")
        if self.response is not None:
            metadata.append(f"Response: {self.response}")

        # Join all metadata into a single string
        return f"{base_message} {'| '.join(metadata)}".strip()


class AuthenticationException(S3IException):
    """Raised when the authentication fails."""


class InvalidCredentialsException(AuthenticationException):
    """Raised when the credentials are invalid."""
