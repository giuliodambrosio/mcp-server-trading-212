from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Registration:
    kind: str
    name: str
    meta: dict[str, Any] = field(default_factory=dict)
    fn: Callable[..., Any] | None = None


class FakeMCP:
    def __init__(self) -> None:
        self.resources: list[Registration] = []
        self.tools: list[Registration] = []

    def resource(self, uri: str, **kwargs: Any):
        def decorator(fn: Callable[..., Any]):
            self.resources.append(Registration(kind="resource", name=uri, meta=kwargs, fn=fn))
            return fn

        return decorator

    def tool(self, **kwargs: Any):
        def decorator(fn: Callable[..., Any]):
            self.tools.append(Registration(kind="tool", name=fn.__name__, meta=kwargs, fn=fn))
            return fn

        return decorator
