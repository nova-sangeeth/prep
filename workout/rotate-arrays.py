from typing import List


class Solution:
    # def rotate(self, nums: List[int], k: int) -> None:
    #     def reverse(i: int, j: int):
    #         while i < j:
    #             nums[i] = nums[j]
    #             nums[j] = nums[i]
    #             i = i + 1
    #             j = j - 1

    #     n = len(nums)
    #     k %= n
    #     reverse(0, n - 1)
    #     reverse(0, k - 1)
    #     reverse(k, n - 1)

    # def rotate_inplace(self, nums: List, k: int) -> None:
    #     l = len(nums)
    #     nums.reverse()
    #     n1 = nums[0:k][::-1]
    #     n2 = n1 + nums[k:l][::-1]

    #     print(n2)
    #     # nums[k : len(nums) - 1].reverse()

    def reverse_arr(self, nums: List[int]) -> None:

        def rev(i: int, j: int) -> None:
            while i < j:
                nums[i], nums[j] = nums[j], nums[i]

                i = i + 1
                j = j - 1

        total_len = len(nums)
        print(total_len)
        k = 3 % len(nums)
        rev(i=0, j=total_len - 1)
        # rev(i=0, j=k - 1)
        # rev(i=k, j=total_len - 1)
        print(nums)


if __name__ == "__main__":
    r_arr = Solution().reverse_arr(nums=[1, 2, 3, 4, 5, 6, 7, 8])
