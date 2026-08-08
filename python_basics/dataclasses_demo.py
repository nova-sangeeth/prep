"""Q29. dataclasses.

@dataclass auto-generates __init__, __repr__, __eq__ from typed fields.
Less boilerplate than a plain class. Options: frozen (immutable/hashable),
order (comparison ops), field(default_factory=...) for mutable defaults.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Point:
    """Mutable record with two coordinates and an optional label."""

    x: int
    y: int
    tags: list[str] = field(default_factory=list)  # safe mutable default


@dataclass(frozen=True, order=True)
class Version:
    """Immutable + comparable/hashable value object."""

    major: int
    minor: int


if __name__ == "__main__":
    p = Point(1, 2)
    print(p)  # Point(x=1, y=2, tags=[]) -> auto __repr__
    print(p == Point(1, 2))  # True -> auto __eq__

    print(Version(1, 2) < Version(1, 5))  # True -> order=True
    print({Version(1, 0)})  # hashable -> frozen=True
