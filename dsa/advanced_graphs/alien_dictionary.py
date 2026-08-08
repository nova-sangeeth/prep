"""Alien Dictionary  |  tier: blind75, neetcode150  |  Advanced Graphs

Given words sorted by the rules of an alien language, return any valid ordering
of its letters, or "" if the ordering is invalid.

Approach: build a graph of letter precedences from each adjacent word pair (first
differing char gives an edge). Topologically sort the letters; a cycle or a
prefix-violation (longer word before its prefix) means no valid order.
Time: O(total chars)   Space: O(unique letters)
"""
from __future__ import annotations

from collections import defaultdict, deque


def alien_order(words: list[str]) -> str:
    """Return a valid letter ordering for the alien language, or ''."""
    graph: defaultdict[str, set[str]] = defaultdict(set)
    indegree = {ch: 0 for word in words for ch in word}

    for first, second in zip(words, words[1:]):
        min_len = min(len(first), len(second))
        if first[:min_len] == second[:min_len] and len(first) > len(second):
            return ""  # prefix appears after longer word
        for char_first, char_second in zip(first, second):
            if char_first != char_second:
                if char_second not in graph[char_first]:
                    graph[char_first].add(char_second)
                    indegree[char_second] += 1
                break

    queue: deque[str] = deque(ch for ch in indegree if indegree[ch] == 0)
    order: list[str] = []
    while queue:
        ch = queue.popleft()
        order.append(ch)
        for nxt in graph[ch]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
    return "".join(order) if len(order) == len(indegree) else ""


if __name__ == "__main__":
    assert alien_order(["wrt", "wrf", "er", "ett", "rftt"]) == "wertf"
    assert alien_order(["z", "x"]) == "zx"
    assert alien_order(["abc", "ab"]) == ""  # invalid: prefix after word
    print("ok")
