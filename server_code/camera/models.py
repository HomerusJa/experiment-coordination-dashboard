"""Defines the models used in the interaction with the camera."""

from typing import Literal

from pydantic import Base64Bytes, BaseModel


class ImageValue(BaseModel):
    """The value the camera sends containing the image and some metadata. Used in getValueReplies and in events."""

    type: Literal["b64 jpeg"]
    path: str
    takenAt: int
    image: Base64Bytes
