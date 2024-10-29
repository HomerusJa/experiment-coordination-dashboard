"""Define the authenticators for the S³I Identity Provider, including token management and credential handling."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import httpx

from . import s3i_logger
from .exceptions import AuthenticationException, InvalidCredentialsException

logger = s3i_logger.getChild("auth")

DEFAULT_IDP_URL = "https://idp.s3i.vswf.dev/auth/realms/KWH/protocol/openid-connect/token"


@dataclass
class Token:
    """Represents an authentication token, including refresh details.

    Attributes:
        auth_scheme (str): The type of token, such as 'Bearer'.
        token_content (str): The main token string.
        expires_at (datetime): Expiry time of the token.
        refresh_token (str): Token used for refreshing the main token.
        refresh_expires_at (datetime): Expiry time of the refresh token.
    """

    auth_scheme: str
    token_content: str
    expires_at: datetime
    refresh_token: str
    refresh_expires_at: datetime

    @property
    def expired(self) -> bool:
        """Check if the token is expired.

        Returns:
            bool: True if the token is expired, False otherwise.
        """
        return datetime.now() < self.expires_at

    @property
    def refresh_expired(self) -> bool:
        """Check if the refresh token is expired.

        Returns:
            bool: True if the refresh token is expired, False otherwise.
        """
        return datetime.now() < self.refresh_expires_at

    @property
    def full_token(self) -> str:
        """Return the full token string with the authentication scheme.

        Returns:
            str: The full token including its scheme.
        """
        return f"{self.auth_scheme} {self.token_content}"

    @property
    def header(self) -> dict:
        """Generate the authorization header.

        Returns:
            dict: The authorization header containing the token.
        """
        return {"Authorization": self.full_token}


class BaseAuthenticator:
    """Base class for authenticators handling token retrieval and refresh.

    Attributes:
        idp_url (str): URL of the Identity Provider.
        client (httpx.Client): HTTP client for making requests.
        external_client (bool): Flag to check if the client was provided externally.
    """

    def __init__(self, client: httpx.Client = None, idp_url: str = DEFAULT_IDP_URL):
        """Initialize the authenticator with an HTTP client and Identity Provider URL.

        Args:
            client (httpx.Client, optional): HTTP client for requests. Defaults to a new client if not provided.
            idp_url (str): URL of the Identity Provider. Defaults to DEFAULT_IDP_URL.
        """
        self.__token: Optional[Token] = None
        self.idp_url = idp_url
        self.client = client or httpx.Client()
        self.external_client = client is None

    def __del__(self):
        """Close the HTTP client if it was not provided externally."""
        if not self.external_client:
            self.client.close()

    def obtain_token(self) -> Token:
        """Retrieve a token from the S³I Identity Provider.

        Returns:
            Token: The current or newly retrieved token.

        Raises:
            AuthenticationException: If the token could not be obtained.
        """
        if self.__token and not self.__token.expired:
            logger.debug("Token is still valid.")
        elif self.__token and not self.__token.refresh_expired:
            logger.debug("Token is expired, but refresh token is still valid.")
            self.__token = self._refresh_token()
        else:
            logger.debug("Token is expired and refresh token is also expired.")
            self.__token = self._get_token_from_idp()

        if self.__token is None:
            raise AuthenticationException("Could not obtain token from S³I Identity Provider.")
        logger.success("Token obtained successfully.")

        return self.__token

    def _get_token_from_idp(self) -> Token:
        """Request a new token from the Identity Provider.

        Returns:
            Token: A new authentication token.

        Raises:
            AuthenticationException: If the token request fails.
            InvalidCredentialsException: If provided credentials are invalid.
        """
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = self._build_auth_payload()  # Abstract method to be overridden

        logger.trace(f"Starting request to {self.idp_url}.")
        response = self.client.post(self.idp_url, headers=headers, data=payload)

        if response.status_code >= 400:
            if response.text == '{"error":"invalid_client","error_description":"Invalid client credentials"}':
                raise InvalidCredentialsException(
                    "Invalid client credentials.",
                    status_code=response.status_code,
                    response=response.text,
                )
            raise AuthenticationException(
                "Could not obtain token from S³I Identity Provider.",
                status_code=response.status_code,
                response=response.text,
            )

        resp_json = response.json()
        return Token(
            auth_scheme=resp_json.get("token_type"),
            token_content=resp_json.get("access_token"),
            expires_at=datetime.now() + timedelta(seconds=resp_json["expires_in"]),
            refresh_token=resp_json.get("refresh_token"),
            refresh_expires_at=datetime.now() + timedelta(seconds=resp_json["refresh_expires_in"]),
        )

    def _refresh_token(self) -> Token:
        """Refresh the current token using the refresh token.

        Returns:
            Token: A refreshed authentication token.

        Raises:
            AuthenticationException: If refreshing the token fails.
        """
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.__token.refresh_token,
        }

        logger.trace(f"Starting request to {self.idp_url}.")
        response = self.client.post(self.idp_url, headers=headers, data=payload)

        if response.status_code >= 400:
            raise AuthenticationException(
                "Could not refresh token from S³I Identity Provider.",
                status_code=response.status_code,
                response=response.text,
            )

    def _build_auth_payload(self) -> dict:
        """Abstract method to build the payload for authentication.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError("This method should be implemented by subclasses.")


class ClientAuthenticator(BaseAuthenticator):
    """Authenticator for client credentials grant type, providing client ID and secret."""

    def __init__(
        self,
        id: str,
        secret: str,
        client: httpx.Client = None,
        idp_url: str = DEFAULT_IDP_URL,
    ):
        """Initialize the ClientAuthenticator with client credentials.

        Args:
            id (str): Client ID.
            secret (str): Client secret.
            client (httpx.Client, optional): HTTP client for requests. Defaults to a new client if not provided.
            idp_url (str): URL of the Identity Provider. Defaults to DEFAULT_IDP_URL.
        """
        super().__init__(client, idp_url)
        self.__id = id
        self.__secret = secret

    def _build_auth_payload(self) -> dict:
        """Build the payload for client credentials grant.

        Returns:
            dict: The payload with client credentials.
        """
        return {
            "grant_type": "client_credentials",
            "client_id": self.__id,
            "client_secret": self.__secret,
        }


class PasswordAuthenticator(BaseAuthenticator):
    """Authenticator for password grant type, providing client ID, secret, username, and password."""

    def __init__(
        self,
        id: str,
        secret: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        client: httpx.Client = None,
        idp_url: str = DEFAULT_IDP_URL,
    ):
        """Initialize the PasswordAuthenticator with client and user credentials.

        Args:
            id (str): Client ID.
            secret (str): Client secret.
            username (str): User's username.
            password (str): User's password.
            client (httpx.Client, optional): HTTP client for requests. Defaults to a new client if not provided.
            idp_url (str): URL of the Identity Provider. Defaults to DEFAULT_IDP_URL.
        """
        super().__init__(client, idp_url)
        self.__username = username
        self.__password = password
        self.__id = id
        self.__secret = secret

    def _build_auth_payload(self) -> dict:
        """Build the payload for password grant.

        Returns:
            dict: The payload with client and user credentials.
        """
        payload = (
            {
                "grant_type": "password",
                "client_id": self.__id,
                "client_secret": self.__secret,
            }
            | {"username": self.__username, "password": self.__password}
            if self.__username and self.__password
            else {}
        )
        return payload
