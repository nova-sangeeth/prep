"""Valid Palindrome  |  tier: core50, blind75, neetcode150  |  Two Pointers

Return True if the string reads the same forwards and backwards, considering
only alphanumeric characters and ignoring case.

Approach: two pointers from both ends move inward, skipping non-alphanumerics,
comparing lowercased chars. O(1) extra space (no cleaned copy).
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def is_palindrome(text: str) -> bool:
    """Return True if text is a palindrome over alphanumeric chars, case-insensitive."""
    left, right = 0, len(text) - 1
    while left < right:
        while left < right and not text[left].isalnum():
            left += 1
        while left < right and not text[right].isalnum():
            right -= 1
        if text[left].lower() != text[right].lower():
            return False
        left += 1
        right -= 1
    return True


if __name__ == "__main__":
    assert is_palindrome("A man, a plan, a canal: Panama") is True
    assert is_palindrome("race a car") is False
    assert is_palindrome(" ") is True
    print("ok")
