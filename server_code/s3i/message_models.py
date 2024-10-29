"""Defines the different message models for the S3I Broker (Currently incomplete)."""

from typing import Any, Literal, Union

from pydantic import BaseModel, Field, RootModel


class S3IMessageBodyBase(BaseModel):
    """The base class for all S3I message bodies."""

    sender: str
    identifier: str
    receivers: list[str]
    messageType: str


class GetValueRequestBody(S3IMessageBodyBase):
    """The message body for requesting a value."""

    messageType: Literal["getValueRequest"]
    replyToEndpoint: str
    attributePath: str


class GetValueReplyBody(S3IMessageBodyBase):
    """The message body for replying to a value request."""

    messageType: Literal["getValueReply"]
    replyingToMessage: str
    value: dict[str, Any]


# TODO: Add the other message types here


class S3IMessage(RootModel):
    """The root model for all S3I messages."""

    root: Union[
        GetValueRequestBody,
        GetValueReplyBody,
        # Add the other message types here
    ] = Field(discriminator="messageType")
