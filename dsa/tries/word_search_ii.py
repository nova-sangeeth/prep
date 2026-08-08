"""Word Search II  |  tier: neetcode150  |  Tries

Given a grid of letters and a word list, return all words that can be formed by
sequentially adjacent cells (no cell reused per word).

Approach: build a trie of the words, then DFS the grid following trie edges. The
trie prunes dead branches early (vs searching each word separately) and dedups
shared prefixes. Mark found words to avoid duplicates.
Time: O(cells * 4^maxlen) worst   Space: O(total chars)
"""
from __future__ import annotations


class TrieNode:
    """Trie node storing children and the complete word at its end."""

    def __init__(self) -> None:
        self.children: dict[str, TrieNode] = {}
        self.word: str | None = None


def find_words(board: list[list[str]], words: list[str]) -> list[str]:
    """Return all board-formable words from the list."""
    root = TrieNode()
    for word in words:
        node = root
        for char in word:
            node = node.children.setdefault(char, TrieNode())
        node.word = word

    rows, cols = len(board), len(board[0])
    found: list[str] = []

    def dfs(r: int, c: int, node: TrieNode) -> None:
        char = board[r][c]
        if char == "#" or char not in node.children:
            return
        nxt = node.children[char]
        if nxt.word is not None:
            found.append(nxt.word)
            nxt.word = None  # dedupe
        board[r][c] = "#"  # mark visited
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                dfs(nr, nc, nxt)
        board[r][c] = char  # restore

    for r in range(rows):
        for c in range(cols):
            dfs(r, c, root)
    return found


if __name__ == "__main__":
    board = [
        ["o", "a", "a", "n"],
        ["e", "t", "a", "e"],
        ["i", "h", "k", "r"],
        ["i", "f", "l", "v"],
    ]
    assert sorted(find_words(board, ["oath", "pea", "eat", "rain"])) == ["eat", "oath"]
    print("ok")
