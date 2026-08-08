"""Course Schedule II  |  tier: neetcode150  |  Graphs

Return an order to take all courses given prerequisites, or [] if impossible.

Approach: Kahn's algorithm (BFS topological sort). Repeatedly take nodes with
in-degree 0, append to the order, and decrement neighbors. If the order covers
every course, it is valid; otherwise a cycle exists.
Time: O(V + E)   Space: O(V + E)
"""
from __future__ import annotations

from collections import defaultdict, deque


def find_order(num_courses: int, prerequisites: list[list[int]]) -> list[int]:
    """Return a valid course order, or [] if a cycle exists."""
    graph: defaultdict[int, list[int]] = defaultdict(list)
    indegree = [0] * num_courses
    for course, prereq in prerequisites:
        graph[prereq].append(course)
        indegree[course] += 1

    queue: deque[int] = deque(course for course in range(num_courses) if indegree[course] == 0)
    order: list[int] = []
    while queue:
        node = queue.popleft()
        order.append(node)
        for neighbor in graph[node]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)
    return order if len(order) == num_courses else []


if __name__ == "__main__":
    assert find_order(2, [[1, 0]]) == [0, 1]
    order = find_order(4, [[1, 0], [2, 0], [3, 1], [3, 2]])
    assert order[0] == 0 and order[-1] == 3 and len(order) == 4
    assert find_order(2, [[0, 1], [1, 0]]) == []
    print("ok")
