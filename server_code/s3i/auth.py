from dataclasses import dataclass
from datetime import datetime

import httpx
from exp_co.s3i.exceptions import AuthenticationException, InvalidCredentialsException
from loguru import logger

DEFAULT_IDP_URL = (
    "https://idp.s3i.vswf.dev/auth/realms/KWH/protocol/openid-connect/token"
)


@dataclass
class Token:
    auth_scheme: str
    token_content: str
    expires_at: datetime

    refresh_token: str
    refresh_expires_at: datetime

    @property
    def expired(self) -> bool:
        return datetime.now() < self.expires_at

    @property
    def refresh_expired(self) -> bool:
        return datetime.now() < self.refresh_expires_at

    @property
    def full_token(self) -> str:
        return f"{self.auth_scheme} {self.token_content}"

    @property
    def header(self) -> dict:
        return {"Authorization": self.full_token}


class BaseAuthenticator:
    def __init__(
        self, client: httpx.AsyncClient = None, idp_url: str = DEFAULT_IDP_URL
    ):
        self.__token: Optional[Token] = None
        self.idp_url = idp_url
        self.client = client or httpx.AsyncClient()
        self.external_client = client is None

    def __del__(self):
        if not self.external_client:
            self.client.close()

    async def obtain_token(self) -> Token:
        """Obtain a token from the S³I Identity Provider."""
        if self.__token and not self.__token.expired:
            logger.debug("Token is still valid.")
        elif self.__token and not self.__token.refresh_expired:
            logger.debug("Token is expired, but refresh token is still valid.")
            self.__token = await self._refresh_token()
        else:
            logger.debug("Token is expired and refresh token is also expired.")
            self.__token = await self._get_token_from_idp()

        if self.__token is None:
            raise AuthenticationException(
                "Could not obtain token from S³I Identity Provider."
            )
        logger.success("Token obtained successfully.")

        return self.__token

    async def _get_token_from_idp(self) -> Token:
        """Get a token from the S³I Identity Provider."""
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = self._build_auth_payload()  # Abstract method to be overridden

        logger.trace(f"Starting request to {self.idp_url}.")
        response = await self.client.post(self.idp_url, headers=headers, data=payload)

        if response.status_code >= 400:
            if (
                response.text
                == '{"error":"invalid_client","error_description":"Invalid client credentials"}'
            ):
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
            refresh_expires_at=datetime.now()
            + timedelta(seconds=resp_json["refresh_expires_in"]),
        )

    async def _refresh_token(self) -> Token:
        """Refresh a token from the S³I Identity Provider."""
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.__token.refresh_token,
        }

        logger.trace(f"Starting request to {self.idp_url}.")
        response = await self.client.post(self.idp_url, headers=headers, data=payload)

        if response.status_code >= 400:
            raise AuthenticationException(
                "Could not refresh token from S³I Identity Provider.",
                status_code=response.status_code,
                response=response.text,
            )

    def _build_auth_payload(self) -> dict:
        """Abstract method to build the payload for authentication, to be implemented by subclasses."""
        raise NotImplementedError("This method should be implemented by subclasses.")


class ClientAuthenticator(BaseAuthenticator):
    """Authenticator for client credentials grant type."""

    def __init__(
        self,
        id: str,
        secret: str,
        client: httpx.AsyncClient = None,
        idp_url: str = DEFAULT_IDP_URL,
    ):
        super().__init__(client, idp_url)
        self.__id = id
        self.__secret = secret

    def _build_auth_payload(self) -> dict:
        """Build the payload for client credentials grant."""
        return {
            "grant_type": "client_credentials",
            "client_id": self.__id,
            "client_secret": self.__secret,
        }


class PasswordAuthenticator(BaseAuthenticator):
    """Authenticator for password grant type."""

    def __init__(
        self,
        id: str,
        secret: str,
        username: str,
        password: str,
        client: httpx.AsyncClient = None,
        idp_url: str = DEFAULT_IDP_URL,
    ):
        super().__init__(client, idp_url)
        self.__username = username
        self.__password = password
        self.__id = id
        self.__secret = secret

    def _build_auth_payload(self) -> dict:
        """Build the payload for password grant."""
        return {
            "grant_type": "password",
            "client_id": self.__id,
            "client_secret": self.__secret,
            "username": self.__username,
            "password": self.__password,
        }
