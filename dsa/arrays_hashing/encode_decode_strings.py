"""Encode and Decode Strings  |  tier: blind75, neetcode150  |  Arrays & Hashing

Design encode(list[str]) -> str and decode(str) -> list[str] so any list of
strings round-trips, even with delimiters or empty strings inside.

Approach: length-prefix each string as "<len>#<string>". The decoder reads the
length up to '#', then slices exactly that many chars -> content is never
confused with a delimiter.
Time: O(total chars)   Space: O(total chars)
"""
from __future__ import annotations


def encode(strs: list[str]) -> str:
    """Serialize a list of strings to a single string."""
    return "".join(f"{len(string)}#{string}" for string in strs)


def decode(data: str) -> list[str]:
    """Reverse of encode: parse length prefixes to recover the list."""
    result: list[str] = []
    i = 0
    while i < len(data):
        j = i
        while data[j] != "#":
            j += 1
        length = int(data[i:j])
        start = j + 1
        result.append(data[start : start + length])
        i = start + length
    return result


if __name__ == "__main__":
    cases = [["hello", "world"], ["", "*hfh"], ["a#b", "3#x", ""], []]
    for case in cases:
        assert decode(encode(case)) == case
    print("ok")
