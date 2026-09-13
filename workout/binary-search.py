def binary_search(nums: list[int], target: int) -> int:
    """
    Binary Search
    """

    left = 0
    right = len(nums) -1 
    print(left, right)
    while left < right:
        mid = (left + right) // 2
        print(mid)
        if nums[mid] == target:
            return mid

        if mid <= target:

            left = mid + 1
        else:
            right = mid - 1

    return -1



nums = [1,2,3,4,5,6,7,8,9,10]

result = binary_search(nums=nums, target=3)
print(result)