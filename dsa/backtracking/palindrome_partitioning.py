"""Palindrome Partitioning  |  tier: neetcode150  |  Backtracking

Partition a string so every substring is a palindrome; return all such
partitionings.

Approach: backtracking over cut positions. For each prefix that is a palindrome,
fix it as the next part and recurse on the remainder.
Time: O(n * 2^n)   Space: O(n)
"""
from __future__ import annotations


def partition(text: str) -> list[list[str]]:
    """Return all palindrome partitionings of text."""
    result: list[list[str]] = []
    current: list[str] = []

    def is_palindrome(sub: str) -> bool:
        return sub == sub[::-1]

    def backtrack(start: int) -> None:
        if start == len(text):
            result.append(current[:])
            return
        for end in range(start + 1, len(text) + 1):
            prefix = text[start:end]
            if is_palindrome(prefix):
                current.append(prefix)
                backtrack(end)
                current.pop()

    backtrack(0)
    return result


if __name__ == "__main__":
    assert sorted(partition("aab")) == sorted([["a", "a", "b"], ["aa", "b"]])
    assert partition("a") == [["a"]]
    print("ok")
