"""Defines the Broker class for interacting with the S3I Broker."""

from dataclasses import dataclass
from typing import Optional

import httpx

from . import auth, exceptions, s3i_logger

logger = s3i_logger.getChild("broker")

DEFAULT_BROKER_URL = "https://broker.s3i.vswf.dev"


@dataclass
class Thing:
    """Represents an entity with unique credentials for communication with the S3I Broker.

    Attributes:
        id (str): Unique identifier for the Thing.
        secret (str): Secret key for authentication.
        message_queue (Optional[str]): URL of the message queue for the Thing.
        event_queue (Optional[str]): URL of the event queue for the Thing.
    """

    id: str
    secret: str
    message_queue: Optional[str] = None
    event_queue: Optional[str] = None

    def __post_init__(self):
        """Initializes default values for message_queue and event_queue if they are not provided.

        Logs warnings if default values are generated.
        """
        if self.message_queue is None:
            self.message_queue = f"s3ibs://{self.id}"
            logger.warning(f"No message queue provided. Generated default message queue: {self.message_queue}")

        if self.event_queue is None:
            self.event_queue = f"s3ib://{self.id}/event"
            logger.warning(f"No event queue provided. Generated default event queue: {self.event_queue}")


class Broker:
    """A client for interacting with the S3I Broker, supporting message sending and receiving.

    Attributes:
        broker_url (str): The URL of the broker.
        client (httpx.Client): The HTTP client used for making requests.
        external_client (bool): Whether the client was provided externally.
        auth (auth.ClientAuthenticator): Authenticator for managing client credentials.
        message_queue (str): The message queue URL.
        event_queue (str): The event queue URL.
    """

    def __init__(
        self,
        self_thing: Thing,
        client: httpx.Client = None,
        broker_url: str = DEFAULT_BROKER_URL,
    ):
        """Initializes the Broker with authentication and connection settings.

        Args:
            self_thing (Thing): The entity (Thing) that interacts with the broker.
            client (httpx.Client, optional): An HTTP client. Defaults to creating a new client.
            broker_url (str): URL of the broker. Defaults to DEFAULT_BROKER_URL.
        """
        self.broker_url = broker_url
        self.client = client or httpx.Client()
        self.external_client = client is None
        self.auth = auth.ClientAuthenticator(self_thing.id, self_thing.secret, self.client)
        self.message_queue = self_thing.message_queue
        self.event_queue = self_thing.event_queue

    def __del__(self):
        """Closes the HTTP client if it was not provided externally."""
        if not self.external_client:
            self.client.close()

    def send(self, endpoint: str, message: dict) -> tuple[int, str]:
        """Send a message to the message broker.

        Args:
            endpoint (str): The endpoint to send the message to.
            message (dict): The message to send.

        Returns:
            tuple[int, str]: The status code and response text.

        Raises:
            exceptions.S3IException: If the message sending fails.
        """
        token = self.auth.obtain_token()
        headers = {"Content-Type": "application/json"} | token.header
        url = f"{self.broker_url}/{endpoint}"

        logger.trace(f"Sending request to {url}.")
        response = self.client.post(url, headers=headers, json=message)

        if response.status_code != 201:
            raise exceptions.S3IException(
                f"Failed to send message to {endpoint}.",
                headers=response.headers,
                body=message,
                status_code=response.status_code,
                response=response.text,
            )
        logger.success("Message sent successfully.")

        return response.status_code, response.text

    def receive(self, event: bool = False, all: bool = False) -> tuple[int, str] | None:
        """Receive a message from the message broker.

        Args:
            event (bool, optional): Whether to receive an event message. Defaults to False.
            all (bool, optional): Whether to retrieve all available messages. Defaults to False.

        Returns:
            tuple[int, str]: The status code and response text if a message is received.
            None: If no message is available.

        Raises:
            exceptions.S3IException: If the message retrieval fails.
        """
        endpoint = self.event_queue if event else self.message_queue
        token = self.auth.obtain_token()
        headers = token.header
        url = f"{self.broker_url}/{endpoint}{'/all' if all else ''}"

        logger.trace(f"Sending request to {url}.")
        response = self.client.get(url, headers=headers)

        if response.status_code != 200:
            raise exceptions.S3IException(
                f"Failed to get message from {endpoint}.",
                headers=response.headers,
                status_code=response.status_code,
                response=response.text,
            )
        logger.success("Message received successfully.")

        if response.text == "":
            logger.trace("No message received.")
            return None

        return response.status_code, response.text
