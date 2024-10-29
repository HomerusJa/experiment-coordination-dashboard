"""Define the background task to fetch messages from the S3I message broker."""

import anvil.server

from ..camera.models import ImageValue
from ..s3i import global_broker as broker
from ..s3i.message_models import S3IMessage
from . import bg_logger

logger = bg_logger.getChild("fetch_messages")


def is_image_message(message: S3IMessage) -> bool:
    """Check if the message is an image message."""
    return message.root.messageType == "getValueReply" and message.root.value.get("type") == "b64 jpeg"


def handle_single_message(response_text: str):
    """Handle a single message."""
    message = S3IMessage.model_validate_json(response_text)

    if is_image_message(message):
        value = ImageValue.model_validate(message.root.value)  # noqa: F841
        # TODO: Save the image to the database


@anvil.server.background_task
def fetch_s3i_messages():
    """Fetch messages from the S3I message broker a single time and do the appropriate tasks."""
    # Currently just fetching a single message at a time, because a message can be pretty big.
    exceptions = []

    while (result := broker.receive()) is not None:
        try:
            _, response_text = result
            handle_single_message(response_text)
        except Exception as e:
            exceptions.append(e)

    if exceptions:
        raise ExceptionGroup("Exceptions occurred while handling messages.", exceptions)


@anvil.server.callable
def launch_fetch_s3i_messages():
    """Launch the background task to fetch messages from the S3I message broker."""
    anvil.server.launch_background_task("fetch_s3i_messages")
