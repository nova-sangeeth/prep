"""Design Add and Search Words  |  tier: blind75, neetcode150  |  Tries

Support addWord(word) and search(word) where '.' in a search matches any single
character.

Approach: a trie. Search is a DFS; on a '.', recurse into every child, otherwise
follow the single matching child.
Time: add O(len); search O(len) typical, O(26^len) worst with many dots
Space: O(total chars)
"""
from __future__ import annotations


class TrieNode:
    """Trie node with children and end-of-word flag."""

    def __init__(self) -> None:
        self.children: dict[str, TrieNode] = {}
        self.is_word = False


class WordDictionary:
    """Word store supporting '.' wildcard search."""

    def __init__(self) -> None:
        self.root = TrieNode()

    def add_word(self, word: str) -> None:
        """Insert a word."""
        node = self.root
        for char in word:
            node = node.children.setdefault(char, TrieNode())
        node.is_word = True

    def search(self, word: str) -> bool:
        """Return True if word matches a stored word ('.' = any char)."""

        def dfs(node: TrieNode, i: int) -> bool:
            if i == len(word):
                return node.is_word
            char = word[i]
            if char == ".":
                return any(dfs(child, i + 1) for child in node.children.values())
            return char in node.children and dfs(node.children[char], i + 1)

        return dfs(self.root, 0)


if __name__ == "__main__":
    wd = WordDictionary()
    for word in ["bad", "dad", "mad"]:
        wd.add_word(word)
    assert wd.search("pad") is False
    assert wd.search("bad") is True
    assert wd.search(".ad") is True
    assert wd.search("b..") is True
    print("ok")
