"""Word Ladder  |  tier: neetcode150  |  Graphs

Return the length of the shortest transformation sequence from beginWord to
endWord, changing one letter at a time, with each intermediate in wordList.
0 if impossible.

Approach: BFS over words (shortest path = fewest steps). Generate neighbors via
wildcard patterns ("h*t") grouping words that differ by one letter, so each
word's neighbors are found in O(L) instead of scanning the whole list.
Time: O(N * L^2)   Space: O(N * L)
"""
from __future__ import annotations

from collections import defaultdict, deque


def ladder_length(begin_word: str, end_word: str, word_list: list[str]) -> int:
    """Return the shortest transformation length, or 0."""
    words = set(word_list)
    if end_word not in words:
        return 0

    patterns: defaultdict[str, list[str]] = defaultdict(list)
    for word in words | {begin_word}:
        for i in range(len(word)):
            patterns[word[:i] + "*" + word[i + 1 :]].append(word)

    queue: deque[tuple[str, int]] = deque([(begin_word, 1)])
    seen = {begin_word}
    while queue:
        word, steps = queue.popleft()
        if word == end_word:
            return steps
        for i in range(len(word)):
            for neighbor in patterns[word[:i] + "*" + word[i + 1 :]]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append((neighbor, steps + 1))
    return 0


if __name__ == "__main__":
    assert ladder_length("hit", "cog", ["hot", "dot", "dog", "lot", "log", "cog"]) == 5
    assert ladder_length("hit", "cog", ["hot", "dot", "dog", "lot", "log"]) == 0
    print("ok")
