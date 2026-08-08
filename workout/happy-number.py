# -*- coding: utf-8 -*-
"""
Happy Number
=====================================
"""

__author__ = "nova@gitaa.in"


def is_happy_num(value: int) -> bool:
    """
    Check happy number
    """
    seen = set()
    happy_num = str(value)

    while happy_num not in seen:
        seen.add(happy_num)
        sum = 0
        for num in happy_num:
            digit = int(num)
            sum += digit**2
            print(sum)

        if sum == 1:
            return True

        happy_num = str(sum)
    return False


def main():
    result = is_happy_num(value=91)
    if result:
        print("This is a happy num")
    else:
        print("This is not a happy num")


if __name__ == "__main__":
    main()
