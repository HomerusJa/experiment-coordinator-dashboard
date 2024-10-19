import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.secrets
import anvil.server

class S3IException(Exception):
    """Base exception for all S³I-related exceptions."""

    def __init__(self, message: str, headers: dict | str | None = None, body: dict | str | None = None,
                 status_code: int | None = None, response: str | None = None):
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
  