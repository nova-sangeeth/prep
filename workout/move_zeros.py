nums = [1, 2, 3, 0, 4, 5, 6, 7, 0, 8, 0, 9]

def main(nums):
    position = 0
    for num in nums:
        if num != 0:
            nums[position] = num
            position += 1
            # print(position)

    while position < len(nums):
        nums[position] = 0
        position += 1
    return nums

result = main(nums=nums)
print(result)
