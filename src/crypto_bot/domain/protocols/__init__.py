"""
Protocols for type safety and structural subtyping.

This module provides Protocol definitions that enable structural typing
for improved type safety without requiring explicit inheritance.
"""

from typing import Protocol
from uuid import UUID


class HasId(Protocol):
    """
    Protocol for entities that have an ID field.

    This protocol enables structural subtyping, allowing any class
    with an 'id' attribute of type UUID to satisfy this protocol.

    Example:
        Any SQLAlchemy model with `id: Mapped[UUID]` automatically
        satisfies this protocol without explicit inheritance.

    This is used in BaseRepository to enforce type safety without
    the need for unsafe casts like `cast(Any, entity).id`.
    """

    id: UUID
