"""Design Twitter  |  tier: neetcode150  |  Heap

Support postTweet, getNewsFeed (10 most recent tweets from the user and everyone
they follow), follow, and unfollow.

Approach: per-user tweet lists with a global timestamp for ordering. getNewsFeed
merges the relevant users' recent tweets with a max-heap keyed by timestamp,
pulling the 10 newest.
Time: getNewsFeed O(f + 10 log f)   Space: O(total tweets + follows)
"""
from __future__ import annotations

import heapq
from collections import defaultdict


class Twitter:
    """Minimal Twitter feed backed by per-user tweet logs."""

    def __init__(self) -> None:
        self._time = 0
        self._tweets: defaultdict[int, list[tuple[int, int]]] = defaultdict(list)
        self._following: defaultdict[int, set[int]] = defaultdict(set)

    def post_tweet(self, user_id: int, tweet_id: int) -> None:
        """Record a tweet with a monotonically increasing timestamp."""
        self._tweets[user_id].append((self._time, tweet_id))
        self._time += 1

    def get_news_feed(self, user_id: int) -> list[int]:
        """Return the 10 most recent tweet ids from self + followees."""
        users = self._following[user_id] | {user_id}
        heap: list[tuple[int, int]] = []
        for uid in users:
            for ts, tid in self._tweets[uid][-10:]:
                heap.append((ts, tid))
        return [tid for _, tid in heapq.nlargest(10, heap)]

    def follow(self, follower_id: int, followee_id: int) -> None:
        """follower starts following followee."""
        self._following[follower_id].add(followee_id)

    def unfollow(self, follower_id: int, followee_id: int) -> None:
        """follower stops following followee."""
        self._following[follower_id].discard(followee_id)


if __name__ == "__main__":
    tw = Twitter()
    tw.post_tweet(1, 5)
    assert tw.get_news_feed(1) == [5]
    tw.follow(1, 2)
    tw.post_tweet(2, 6)
    assert tw.get_news_feed(1) == [6, 5]
    tw.unfollow(1, 2)
    assert tw.get_news_feed(1) == [5]
    print("ok")
