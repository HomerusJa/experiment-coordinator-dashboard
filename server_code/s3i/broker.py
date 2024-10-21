from dataclasses import dataclass
from typing import Optional

import httpx
from loguru import logger

from . import auth
from . import exceptions

DEFAULT_BROKER_URL = "https://broker.s3i.vswf.dev"


@dataclass
class Thing:
    id: str
    secret: str

    message_queue: Optional[str] = None
    event_queue: Optional[str] = None

    def __post_init__(self):
        # Find default message and event queues
        if self.message_queue is None:
            self.message_queue = f"s3ibs://{self.id}"
            logger.warning(
                f"No message queue provided. Generated default message queue: {self.message_queue}"
            )

        if self.event_queue is None:
            self.event_queue = f"s3ib://{self.id}/event"
            logger.warning(
                f"No event queue provided. Generated default event queue: {self.event_queue}"
            )


class Broker:
    def __init__(
        self,
        self_thing: Thing,
        client: httpx.AsyncClient = None,
        broker_url: str = DEFAULT_BROKER_URL,
    ):
        self.broker_url = broker_url
        self.client = client or httpx.AsyncClient()
        self.external_client = client is None
        self.auth = auth.ClientAuthenticator(
            self_thing.id, self_thing.secret, self.client
        )
        self.message_queue = self_thing.message_queue
        self.event_queue = self_thing.event_queue

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
            raise exceptions.S3IException(
                f"Failed to send message to {endpoint}.",
                headers=response.headers,
                body=message,
                status_code=response.status_code,
                response=response.text,
            )
        logger.success("Message sent successfully.")

    async def receive(self, event: bool = False, all: bool = False) -> dict:
        """Receive a message from the message broker."""
        endpoint = self.event_queue if event else self.message_queue
        token = await self.auth.obtain_token()
        headers = token.header
        url = f"{self.broker_url}/{endpoint}{'\all' if all else ''}"

        logger.trace(f"Sending request to {url}.")
        response = await self.client.get(url, headers=headers)

        if response.status_code != 200:
            raise exceptions.S3IException(
                f"Failed to get message from {endpoint}.",
                headers=response.headers,
                status_code=response.status_code,
                response=response.text,
            )
        logger.success("Message received successfully.")

        return response.json()
