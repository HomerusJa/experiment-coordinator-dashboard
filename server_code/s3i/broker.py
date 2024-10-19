import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.secrets
import anvil.server

from loguru import logger
import httpx

from . import exceptions

DEFAULT_BROKER_URL = "https://broker.s3i.vswf.dev"


class Broker:
    def __init__(self, id: str, secret: str, client: httpx.AsyncClient = None, broker_url: str = DEFAULT_BROKER_URL):
        self.broker_url = broker_url
        self.client = client or httpx.AsyncClient()
        self.external_client = client is None
        self.auth = ClientAuthenticator(id, secret, self.client)

    def __del__(self):
        if not self.external_client:
            self.client.close()

    async def send(self, endpoint: str, message: dict):
        """Send a message to the message broker."""
        token = await self.auth.obtain_token()
        headers = {"Content-Type": "application/json"} | token.header
        url = f"{self.broker_url}/{endpoint}"

        logger.trace(f"Sending request to {url}.")
        response = await self.client.post(url, headers=headers, json=message)

        if response.status_code != 201:
            raise S3IException(f"Failed to send message to {endpoint}.",
                               headers=response.headers,
                               body=message,
                               status_code=response.status_code,
                               response=response.text)
        logger.success("Message sent successfully.")

    async def receive(self, event: bool = False, all: bool = False) -> dict:
        """Receive a message from the message broker."""
        token = await self.auth.obtain_token()
        headers = token.header
        url = f"{self.broker_url}/{endpoint}{'\event' if event else ''}{'\all' if all else ''}"

        logger.trace(f"Sending request to {url}.")
        response = await self.client.get(url, headers=headers)

        if response.status_code != 200:
            raise S3IException(f"Failed to get message from {endpoint}.",
                               headers=response.headers,
                               status_code=response.status_code,
                               response=response.text)
        logger.success("Message received successfully.")

        return response.json()
