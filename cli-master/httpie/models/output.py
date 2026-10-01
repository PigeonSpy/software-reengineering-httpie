from typing import NamedTuple
from urllib.parse import urlsplit
from .kinds import RequestsMessage, infer_requests_message_kind

from ..cli.constants import (
    OUT_REQ_BODY,
    OUT_REQ_HEAD,
    OUT_RESP_BODY,
    OUT_RESP_HEAD,
    OUT_RESP_META
)
from .kinds import RequestsMessageKind

OPTION_TO_PARAM = {
    RequestsMessageKind.REQUEST: {
        'headers': OUT_REQ_HEAD,
        'body': OUT_REQ_BODY,
    },
    RequestsMessageKind.RESPONSE: {
        'headers': OUT_RESP_HEAD,
        'body': OUT_RESP_BODY,
        'meta': OUT_RESP_META
    }
}


class OutputOptions(NamedTuple):
    kind: RequestsMessageKind
    headers: bool
    body: bool
    meta: bool = False

    def any(self):
        return (
            self.headers
            or self.body
            or self.meta
        )

    @classmethod
    def from_message(
        cls,
        message: RequestsMessage,
        raw_args: str = '',
        **kwargs
    ):
        kind = infer_requests_message_kind(message)

        options = {
            option: param in raw_args
            for option, param in OPTION_TO_PARAM[kind].items()
        }
        options.update(kwargs)

        return cls(
            kind=kind,
            **options
        )
