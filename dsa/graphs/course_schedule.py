"""Course Schedule  |  tier: core50, blind75, neetcode150  |  Graphs

Given numCourses and prerequisite pairs [course, prereq] (prereq before course),
return True if all courses can be finished -- i.e. the dependency graph has no
cycle.

Approach: DFS cycle detection with three states (unvisited / in-progress /
done). Hitting an in-progress node means a back edge -> cycle.
Time: O(V + E)   Space: O(V + E)
"""
from __future__ import annotations

from collections import defaultdict


def can_finish(num_courses: int, prerequisites: list[list[int]]) -> bool:
    """Return True if the course dependency graph is acyclic."""
    graph: defaultdict[int, list[int]] = defaultdict(list)
    for course, prereq in prerequisites:
        graph[course].append(prereq)

    state = [0] * num_courses  # 0=unseen, 1=in-progress, 2=done

    def has_cycle(node: int) -> bool:
        if state[node] == 1:
            return True
        if state[node] == 2:
            return False
        state[node] = 1
        for neighbor in graph[node]:
            if has_cycle(neighbor):
                return True
        state[node] = 2
        return False

    return not any(has_cycle(course) for course in range(num_courses))


if __name__ == "__main__":
    assert can_finish(2, [[1, 0]]) is True
    assert can_finish(2, [[1, 0], [0, 1]]) is False
    assert can_finish(1, []) is True
    print("ok")
