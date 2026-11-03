from collections import deque


def shortest_path(grid, start, goal):
    """grid: strings, with # for a wall. Returns the number of moves, or None."""
    dist = {start: 0}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        if (r, c) == goal:
            return dist[goal]
        for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if (0 <= nr < len(grid) and 0 <= nc < len(grid[0])
                    and grid[nr][nc] != "#" and (nr, nc) not in dist):
                dist[nr, nc] = dist[r, c] + 1  # marked when pushed, not when popped
                queue.append((nr, nc))
    return None
