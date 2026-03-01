from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Trading212APIError(Exception):
    """Structured API error raised for non-success HTTP responses."""

    status_code: int
    method: str
    url: str
    payload: Any | None = None

    def __str__(self) -> str:
        details = ""
        if self.payload is not None:
            try:
                details = f" payload={json.dumps(self.payload, ensure_ascii=True)}"
            except Exception:
                details = f" payload={self.payload!r}"
        return f"Trading212 API error {self.status_code} on {self.method} {self.url}.{details}"


@dataclass(slots=True)
class ResourceNotFoundError(Exception):
    """Raised when a local resource projection cannot find an entity."""

    resource: str
    identifier: str

    def __str__(self) -> str:
        return f"{self.resource} '{self.identifier}' was not found."
