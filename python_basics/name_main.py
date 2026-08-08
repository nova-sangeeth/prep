"""Q16. What does `if __name__ == "__main__":` do?

Each module has __name__. Run directly -> "__main__". Imported -> module name.
The guard runs code only on direct execution, not on import. Lets a file be
both an importable library and a runnable script.
"""
from __future__ import annotations


def main() -> None:
    """Entry point that should run only when executed directly."""
    print(f"running as: {__name__}")
    print("app logic here")


if __name__ == "__main__":
    main()  # runs on `python 16_name_main.py`, not on import
