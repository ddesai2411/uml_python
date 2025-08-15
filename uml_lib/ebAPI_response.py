from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ResponseMeta:
    href: str
    offset: int
    limit: int
    size: int
    totalRecords: int


@dataclass(frozen=True)
class ebResponse:
    query: str
    meta: ResponseMeta
    records: Any