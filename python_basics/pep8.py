"""Q10. What is PEP 8?

Official Python style guide. Key points:
- 4-space indent, no tabs; line length ~79 (teams often 88-120).
- snake_case functions/vars, PascalCase classes, UPPER_CASE constants.
- 2 blank lines between top-level defs, 1 between methods.
- Imports grouped (stdlib, third-party, local) at top, one per line.
- Spaces around operators: x = a + b.
Enforce with: black, ruff, flake8, pylint.
"""
from __future__ import annotations

MAX_RETRIES: int = 3  # UPPER_CASE constant


class OrderProcessor:  # PascalCase class
    """Minimal example following PEP 8 naming and spacing."""

    def __init__(self, order_id: int) -> None:
        self.order_id = order_id  # snake_case attribute

    def total_with_tax(self, subtotal: float, tax_rate: float) -> float:
        """Return subtotal plus tax (spaces around operators)."""
        return subtotal + subtotal * tax_rate


if __name__ == "__main__":
    proc = OrderProcessor(order_id=1)
    print(proc.total_with_tax(100.0, 0.18))
