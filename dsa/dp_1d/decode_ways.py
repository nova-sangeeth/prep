"""Decode Ways  |  tier: blind75, neetcode150  |  1-D DP

Digits map to letters: '1'->'A' ... '26'->'Z'. Return the number of ways to
decode the string. Leading '0' digits cannot start a valid code.

Approach: dp[i] = ways to decode the suffix from i. Add dp[i+1] if the single
digit is valid (not '0'), plus dp[i+2] if the two-digit number is 10..26. Roll
two variables.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def num_decodings(digits: str) -> int:
    """Return the number of ways to decode the digit string."""
    if not digits or digits[0] == "0":
        return 0
    two_ahead, one_ahead = 1, 1  # dp[i+2], dp[i+1]
    for i in range(len(digits) - 1, -1, -1):
        current = 0 if digits[i] == "0" else one_ahead
        if i + 1 < len(digits) and 10 <= int(digits[i : i + 2]) <= 26:
            current += two_ahead
        two_ahead, one_ahead = one_ahead, current
    return one_ahead


if __name__ == "__main__":
    assert num_decodings("12") == 2  # "AB", "L"
    assert num_decodings("226") == 3  # "BZ", "VF", "BBF"
    assert num_decodings("06") == 0
    print("ok")
