"""Best Time to Buy and Sell Stock  |  tier: core50, blind75, neetcode150  |  Sliding Window

Given daily prices, maximize profit from one buy then one later sell. If no
profit is possible, return 0.

Approach: track the minimum price seen so far (best buy day); at each day the
best profit is price - min_so_far. Keep the running maximum.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def max_profit(prices: list[int]) -> int:
    """Return the max profit from a single buy/sell, or 0."""
    min_price = float("inf")
    best = 0
    for price in prices:
        min_price = min(min_price, price)
        best = max(best, price - min_price)
    return best


if __name__ == "__main__":
    assert max_profit([7, 1, 5, 3, 6, 4]) == 5  # buy 1, sell 6
    assert max_profit([7, 6, 4, 3, 1]) == 0  # only losses
    assert max_profit([]) == 0
    print("ok")
