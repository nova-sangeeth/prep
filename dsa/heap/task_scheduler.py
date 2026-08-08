"""Task Scheduler  |  tier: neetcode150  |  Heap

Given task labels and a cooldown (same task must be >= cooldown slots apart),
return the minimum number of CPU intervals (including idles) to finish all tasks.

Approach: the most frequent task dictates the skeleton. With max_freq copies and
gaps of size cooldown, the frame is (max_freq - 1) * (cooldown + 1) + (count of
tasks tied at max_freq). The answer is max(total_tasks, that frame) -- if there
are enough distinct tasks, no idling is needed.
Time: O(n)   Space: O(1)  (26 labels)
"""
from __future__ import annotations

from collections import Counter


def least_interval(tasks: list[str], cooldown: int) -> int:
    """Return the minimum number of intervals to run all tasks."""
    counts = Counter(tasks)
    max_freq = max(counts.values())
    num_max = sum(1 for count in counts.values() if count == max_freq)
    frame = (max_freq - 1) * (cooldown + 1) + num_max
    return max(len(tasks), frame)


if __name__ == "__main__":
    assert least_interval(["A", "A", "A", "B", "B", "B"], 2) == 8
    assert least_interval(["A", "A", "A", "B", "B", "B"], 0) == 6
    assert least_interval(["A", "B", "C", "D"], 2) == 4
    print("ok")
