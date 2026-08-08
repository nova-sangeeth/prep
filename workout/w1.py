def two_sum(nums: list[int], target: int) -> list[int]:
    """
    Two sum, return the value instead of the index
    """
    store = {}
    for num in nums:
        remaining = target - num
        if remaining in store:
            return [remaining, num]
        else:
            store[num] = remaining

def longest_common_prefix_zip(strs):
    if not strs:
        return ""
        
    prefix = []
    # Zip groups characters index by index across all words
    for chars in zip(*strs):
        # If the set size is 1, all words share this character
        if len(set(chars)) == 1:
            print(chars)
            print(chars[0])
            prefix.append(chars[0])
        else:
            break
            
    return "".join(prefix)



if __name__ == "__main__":
    # result = two_sum(nums=[1, 2, 3, 4, 5, 6, 7, 8], target=11)
    # print(result)  # output: [5, 5]
    res = longest_common_prefix_zip(strs=["google", "goo", "go"])
    print(res)