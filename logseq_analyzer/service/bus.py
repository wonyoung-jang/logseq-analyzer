"""Message bus for decoupled communication between components."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass(slots=True)
class MessageBus:
    """A simple message bus for decoupled communication between components."""

    subscribers: dict[str, list[Callable]]
