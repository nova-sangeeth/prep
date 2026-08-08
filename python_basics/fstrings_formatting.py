"""Q35. String formatting (f-strings).

f-strings (3.6+) are the preferred way: inline expressions + format specs.
Older: str.format() and % formatting. f-strings are fastest and clearest.
"""
from __future__ import annotations

import math


def formatting_demo() -> None:
    """Common f-string format specifiers."""
    name, score = "Sam", 0.8567
    print(f"{name} scored {score:.1%}")  # Sam scored 85.7%
    print(f"pi = {math.pi:.3f}")  # pi = 3.142
    print(f"{42:05d}")  # 00042 (zero-pad)
    print(f"{1234567:,}")  # 1,234,567 (thousands)
    print(f"{'hi':>8}|")  # right-align width 8

    debug = 7
    print(f"{debug=}")  # debug=7  (self-documenting, 3.8+)


def old_styles() -> tuple[str, str]:
    """Equivalent str.format() and % formatting."""
    return "{} = {:.2f}".format("x", 3.14159), "%s = %.2f" % ("x", 3.14159)


if __name__ == "__main__":
    formatting_demo()
    print(old_styles())
