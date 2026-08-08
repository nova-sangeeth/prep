"""Implement Trie (Prefix Tree)  |  tier: core50, blind75, neetcode150  |  Tries

Support insert(word), search(word), and startsWith(prefix).

Approach: a tree where each node has children keyed by character and an
end-of-word flag. Each operation walks one node per character.
Time: O(len) per op   Space: O(total chars inserted)
"""
from __future__ import annotations


class TrieNode:
    """A single trie node: child links + end-of-word marker."""

    def __init__(self) -> None:
        self.children: dict[str, TrieNode] = {}
        self.is_word = False


class Trie:
    """Prefix tree over lowercase words."""

    def __init__(self) -> None:
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        """Add a word to the trie."""
        node = self.root
        for char in word:
            node = node.children.setdefault(char, TrieNode())
        node.is_word = True

    def search(self, word: str) -> bool:
        """Return True if the exact word was inserted."""
        node = self._walk(word)
        return node is not None and node.is_word

    def starts_with(self, prefix: str) -> bool:
        """Return True if any inserted word has this prefix."""
        return self._walk(prefix) is not None

    def _walk(self, key: str) -> TrieNode | None:
        node = self.root
        for char in key:
            if char not in node.children:
                return None
            node = node.children[char]
        return node


if __name__ == "__main__":
    trie = Trie()
    trie.insert("apple")
    assert trie.search("apple") is True
    assert trie.search("app") is False
    assert trie.starts_with("app") is True
    trie.insert("app")
    assert trie.search("app") is True
    print("ok")
