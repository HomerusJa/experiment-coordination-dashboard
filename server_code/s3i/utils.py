"""Some utility functions related to s3i."""

import uuid


def generate_message_identifier() -> str:
    """Generate a random, unique message identifier."""
    return f"s3i:{str(uuid.uuid4())}"
