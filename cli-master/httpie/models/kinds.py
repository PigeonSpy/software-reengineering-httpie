from enum import Enum, auto
import requests
from typing import Union

RequestsMessage = Union[requests.PreparedRequest, requests.Response]

class RequestsMessageKind(Enum):
    REQUEST = auto()
    RESPONSE = auto()

def infer_requests_message_kind(message: RequestsMessage) -> RequestsMessageKind:
    if isinstance(message, requests.PreparedRequest):
        return RequestsMessageKind.REQUEST
    elif isinstance(message, requests.Response):
        return RequestsMessageKind.RESPONSE
    else:
        raise TypeError(f"Unexpected message type: {type(message).__name__}")
