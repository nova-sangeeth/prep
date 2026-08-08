"""Letter Combinations of a Phone Number  |  tier: neetcode150  |  Backtracking

Given digits 2-9, return all letter combinations the number could spell (phone
keypad mapping).

Approach: backtracking. For each digit, try every mapped letter, building the
string position by position until all digits are consumed.
Time: O(4^n * n)   Space: O(n)
"""
from __future__ import annotations


def letter_combinations(digits: str) -> list[str]:
    """Return all keypad letter combinations for the digit string."""
    if not digits:
        return []
    keypad = {
        "2": "abc",
        "3": "def",
        "4": "ghi",
        "5": "jkl",
        "6": "mno",
        "7": "pqrs",
        "8": "tuv",
        "9": "wxyz",
    }
    result: list[str] = []
    current: list[str] = []

    def backtrack(i: int) -> None:
        if i == len(digits):
            result.append("".join(current))
            return
        for letter in keypad[digits[i]]:
            current.append(letter)
            backtrack(i + 1)
            current.pop()

    backtrack(0)
    return result


if __name__ == "__main__":
    assert sorted(letter_combinations("23")) == sorted(["ad", "ae", "af", "bd", "be", "bf", "cd", "ce", "cf"])
    assert letter_combinations("") == []
    assert letter_combinations("2") == ["a", "b", "c"]
    print("ok")
