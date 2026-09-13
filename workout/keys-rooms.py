def canVisitAllRooms(rooms: list[list[int]]) -> bool:
    visited = set()
    stack = [0]

    while stack:
        current_room = stack.pop(0)

        for key in rooms[current_room]:
            if key not in visited:
                visited.add(key)
                print(visited)
                stack.append(key)
                print(stack)

    return len(visited) == len(rooms)


if __name__ == "__main__":
    rooms = [[1, 3], [3, 0, 1], [2], [0]]
    result = canVisitAllRooms(rooms=rooms)
    print(result)
