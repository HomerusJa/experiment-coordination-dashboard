"""Define global variables for the S3I module."""

import anvil.secrets
import httpx

from .. import logs
from . import broker

__all__ = ["global_client", "global_broker", "s3i_logger"]

s3i_logger = logs.get_logger("s3i")

global_client = httpx.Client()
_self_thing = broker.Thing(
    id=anvil.secrets.get_secret("s3i_id"),
    secret=anvil.secrets.get_secret("s3i_secret"),
    message_queue=anvil.secrets.get_secret("s3i_message_queue"),
    event_queue=anvil.secrets.get_secret("s3i_event_queue"),
)
global_broker = broker.Broker(_self_thing, client=global_client)
