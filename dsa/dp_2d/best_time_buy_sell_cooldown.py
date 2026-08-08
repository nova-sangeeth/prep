"""Best Time to Buy/Sell Stock with Cooldown  |  tier: neetcode150  |  2-D DP

Maximize profit with unlimited transactions, but after selling you must cool down
one day before buying again.

Approach: state machine over three states per day: hold (own a share), sold (just
sold, cooling down), rest (idle, free to buy). Transition each day and roll the
values.
Time: O(n)   Space: O(1)
"""
from __future__ import annotations


def max_profit(prices: list[int]) -> int:
    """Return the max profit with a one-day cooldown after each sale."""
    hold = float("-inf")  # best profit while holding a share
    sold = 0  # best profit having just sold today
    rest = 0  # best profit idle (can buy)
    for price in prices:
        prev_sold = sold
        sold = hold + price  # sell today
        hold = max(hold, rest - price)  # keep holding or buy from rest
        rest = max(rest, prev_sold)  # stay idle or finish cooldown
    return int(max(sold, rest))


if __name__ == "__main__":
    assert max_profit([1, 2, 3, 0, 2]) == 3  # buy,sell,cooldown,buy,sell
    assert max_profit([1]) == 0
    assert max_profit([2, 1]) == 0
    print("ok")
