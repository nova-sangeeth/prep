"""Coin Change II  |  tier: neetcode150  |  2-D DP

Return the number of distinct combinations of coins that sum to amount (unlimited
coins; order does not matter).

Approach: dp[sub_amount] = ways to make sub_amount. Iterate coins in the OUTER
loop so each combination is counted once (order-independent); for each coin add
dp[sub_amount - coin].
Time: O(amount * coins)   Space: O(amount)
"""
from __future__ import annotations


def change(amount: int, coins: list[int]) -> int:
    """Return the number of coin combinations summing to amount."""
    dp = [0] * (amount + 1)
    dp[0] = 1  # one way to make 0: use nothing
    for coin in coins:  # coin outer -> combinations, not perms
        for sub_amount in range(coin, amount + 1):
            dp[sub_amount] += dp[sub_amount - coin]
    return dp[amount]


if __name__ == "__main__":
    assert change(5, [1, 2, 5]) == 4  # 5; 2+2+1; 2+1+1+1; 1x5
    assert change(3, [2]) == 0
    assert change(10, [10]) == 1
    print("ok")
