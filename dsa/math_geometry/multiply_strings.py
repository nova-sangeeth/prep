"""Multiply Strings  |  tier: neetcode150  |  Math & Geometry

Multiply two non-negative integers given as strings, without using built-in big
integer conversion.

Approach: schoolbook multiplication. digit i times digit j contributes to result
positions i+j and i+j+1. Accumulate into an array, then handle carries and strip
leading zeros.
Time: O(m * n)   Space: O(m + n)
"""
from __future__ import annotations


def multiply(num1: str, num2: str) -> str:
    """Return the product of two non-negative integer strings."""
    if num1 == "0" or num2 == "0":
        return "0"
    m, n = len(num1), len(num2)
    product = [0] * (m + n)
    for i in range(m - 1, -1, -1):
        for j in range(n - 1, -1, -1):
            mul = (ord(num1[i]) - 48) * (ord(num2[j]) - 48)
            low = i + j + 1
            total = mul + product[low]
            product[low] = total % 10
            product[low - 1] += total // 10  # carry up

    result = "".join(map(str, product)).lstrip("0")
    return result or "0"


if __name__ == "__main__":
    assert multiply("2", "3") == "6"
    assert multiply("123", "456") == "56088"
    assert multiply("0", "52") == "0"
    print("ok")
