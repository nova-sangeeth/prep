"""Coin Change  |  tier: core50, blind75, neetcode150  |  1-D DP

Return the fewest coins summing to amount, or -1 if impossible. Unlimited coins
of each denomination.

Approach: bottom-up DP. dp[current_amount] = min coins to make that amount. For
each amount, try each coin: dp[current_amount] = min(dp[current_amount],
dp[current_amount - coin] + 1).
Time: O(amount * coins)   Space: O(amount)
"""
from __future__ import annotations


def coin_change(coins: list[int], amount: int) -> int:
    """Return the minimum number of coins to make amount, or -1."""
    dp = [float("inf")] * (amount + 1)
    dp[0] = 0
    for current_amount in range(1, amount + 1):
        for coin in coins:
            if coin <= current_amount:
                dp[current_amount] = min(dp[current_amount], dp[current_amount - coin] + 1)
    return -1 if dp[amount] == float("inf") else int(dp[amount])


if __name__ == "__main__":
    assert coin_change([1, 2, 5], 11) == 3  # 5 + 5 + 1
    assert coin_change([2], 3) == -1
    assert coin_change([1], 0) == 0
    print("ok")
