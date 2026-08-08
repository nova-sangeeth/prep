"""Meeting Rooms II  |  tier: blind75, neetcode150  |  Intervals

Return the minimum number of meeting rooms required so no meetings overlap in a
room.

Approach: separate and sort start and end times. Sweep: each start needs a room;
if a meeting has already ended (end <= current start), reuse its room. Track the
peak concurrent meetings.
Time: O(n log n)   Space: O(n)
"""
from __future__ import annotations


def min_meeting_rooms(intervals: list[list[int]]) -> int:
    """Return the minimum number of rooms needed."""
    starts = sorted(interval[0] for interval in intervals)
    ends = sorted(interval[1] for interval in intervals)
    rooms = 0
    peak = 0
    end_idx = 0
    for start in starts:
        while end_idx < len(ends) and ends[end_idx] <= start:
            rooms -= 1  # a meeting freed a room
            end_idx += 1
        rooms += 1
        peak = max(peak, rooms)
    return peak


if __name__ == "__main__":
    assert min_meeting_rooms([[0, 30], [5, 10], [15, 20]]) == 2
    assert min_meeting_rooms([[7, 10], [2, 4]]) == 1
    assert min_meeting_rooms([]) == 0
    print("ok")
