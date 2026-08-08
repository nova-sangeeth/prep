"""3Sum  |  tier: core50, blind75, neetcode150  |  Two Pointers

Return all unique triplets that sum to zero. No duplicate triplets.

Approach: sort, then fix each i and two-pointer scan the remainder for pairs
summing to -nums[i]. Skip duplicate anchors and duplicate pair values to keep
triplets unique. Early break once nums[i] > 0.
Time: O(n^2)   Space: O(1)  (excluding output / sort)
"""
from __future__ import annotations


def three_sum(nums: list[int]) -> list[list[int]]:
    """Return all unique zero-sum triplets."""
    nums.sort()
    result: list[list[int]] = []
    for i in range(len(nums)):
        if nums[i] > 0:
            break  # sorted: no zero-sum past here
        if i > 0 and nums[i] == nums[i - 1]:
            continue  # skip duplicate anchor
        left, right = i + 1, len(nums) - 1
        while left < right:
            total = nums[i] + nums[left] + nums[right]
            if total < 0:
                left += 1
            elif total > 0:
                right -= 1
            else:
                result.append([nums[i], nums[left], nums[right]])
                left += 1
                right -= 1
                while left < right and nums[left] == nums[left - 1]:
                    left += 1  # skip duplicate pair value
    return result


if __name__ == "__main__":
    assert three_sum([-1, 0, 1, 2, -1, -4]) == [[-1, -1, 2], [-1, 0, 1]]
    assert three_sum([0, 1, 1]) == []
    assert three_sum([0, 0, 0]) == [[0, 0, 0]]
    print("ok")
