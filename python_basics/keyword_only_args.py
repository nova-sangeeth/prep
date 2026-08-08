"""Q27. Positional-only and keyword-only parameters.

In a signature:
    def f(pos_only, /, normal, *, kw_only)
- params before `/` are positional-only.
- params after `*` are keyword-only (must be passed by name).
Improves API clarity and prevents accidental positional misuse.
"""
from __future__ import annotations


def connect(host: str, /, port: int = 5432, *, timeout: float = 30.0) -> str:
    """host: positional-only; port: normal; timeout: keyword-only."""
    return f"{host}:{port} (timeout={timeout})"


if __name__ == "__main__":
    print(connect("db.local"))  # host positional
    print(connect("db.local", 6543, timeout=5.0))  # timeout by name

    try:
        connect("db.local", timeout=5, port=1)  # ok
        connect(host="db.local")  # TypeError: host is positional-only
    except TypeError as exc:
        print("error:", exc)
