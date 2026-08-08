# length = 10
# for i in range(length - 1, -1, -1):
#     print(i)


def search_arr(nums, k):
    l, r = 0, len(nums) - 1
    while l <= r:
        if nums[l] == k:
            print("found K from l")
            print(nums[l], l)
            break
        if nums[r] == k:
            print("found K from r")
            print(nums[r], r)
            break

        l = l + 1
        r = r - 1


def search_arr_bs(nums, k):

    l, r = 0, len(nums) - 1
    while l <= r:
        mid = (l + r) // 2
        if nums[mid] == k:
            return nums[mid]

        elif nums[mid] < k:
            l = mid + 1
        else:
            r = mid - 1
    return None


nums = [1, 2, 3, 4, 5, 7, 8, 9, 10]
# search_arr(nums=nums, k=10)
res = search_arr_bs(nums=nums, k=6)
print(res)
