"""Q22. instance vs class vs static methods.

Instance method : first arg self -> instance + class state.
@classmethod    : first arg cls  -> class state (good for alt constructors).
@staticmethod   : no implicit arg -> utility grouped under the class.
"""
from __future__ import annotations


class Pizza:
    """Pizza with size, plus class- and static-method examples."""

    size_default = "medium"
    valid_sizes = {"small", "medium", "large"}

    def __init__(self, size: str) -> None:
        self.size = size

    def describe(self) -> str:
        """Instance method: uses self."""
        return f"{self.size} pizza"

    @classmethod
    def default(cls) -> "Pizza":
        """Class method as an alternative constructor (uses cls)."""
        return cls(cls.size_default)

    @staticmethod
    def is_valid_size(size: str) -> bool:
        """Static helper: no instance/class state needed."""
        return size in Pizza.valid_sizes


if __name__ == "__main__":
    print(Pizza("large").describe())
    print(Pizza.default().describe())
    print(Pizza.is_valid_size("xl"))
