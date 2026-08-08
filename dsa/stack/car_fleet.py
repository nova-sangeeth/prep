"""Car Fleet  |  tier: neetcode150  |  Stack

Cars head to a target at given positions and speeds. A faster car catching a
slower one forms a fleet moving at the slower speed (no passing). Return the
number of fleets that arrive.

Approach: sort cars by position descending (closest to target first). Compute
each car's arrival time = (target - pos) / speed. Scan: a car forms a new fleet
only if it arrives strictly later than the fleet ahead; otherwise it merges.
Time: O(n log n)   Space: O(n)
"""
from __future__ import annotations


def car_fleet(target: int, position: list[int], speed: list[int]) -> int:
    """Return the number of car fleets that reach the target."""
    cars = sorted(zip(position, speed), reverse=True)
    fleets = 0
    lead_time = 0.0
    for pos, spd in cars:
        time = (target - pos) / spd
        if time > lead_time:  # cannot catch the fleet ahead
            fleets += 1
            lead_time = time
    return fleets


if __name__ == "__main__":
    assert car_fleet(12, [10, 8, 0, 5, 3], [2, 4, 1, 1, 3]) == 3
    assert car_fleet(10, [3], [3]) == 1
    assert car_fleet(100, [0, 2, 4], [4, 2, 1]) == 1
    print("ok")
