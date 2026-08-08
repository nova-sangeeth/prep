"""Palindromic Substrings  |  tier: blind75, neetcode150  |  1-D DP

Count how many substrings are palindromes (different positions count separately).

Approach: expand around each of the 2n-1 centers, counting every palindrome found
while expanding outward.
Time: O(n^2)   Space: O(1)
"""
from __future__ import annotations


def count_substrings(text: str) -> int:
    """Return the number of palindromic substrings."""
    total = 0

    def expand(left: int, right: int) -> int:
        count = 0
        while left >= 0 and right < len(text) and text[left] == text[right]:
            count += 1
            left -= 1
            right += 1
        return count

    for i in range(len(text)):
        total += expand(i, i)  # odd-length centers
        total += expand(i, i + 1)  # even-length centers
    return total


if __name__ == "__main__":
    assert count_substrings("abc") == 3  # a, b, c
    assert count_substrings("aaa") == 6  # a,a,a, aa,aa, aaa
    print("ok")
