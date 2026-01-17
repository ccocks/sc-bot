"""
Pathfinding: BFS shortest path through walkable tiles.
Used for !tp validation and distance calculations.
"""

from collections import deque
import json
from typing import Optional

def load_tile_config() -> dict:
    with open("config/tiles.json", "r") as f:
        return json.load(f)

def is_walkable(tile: int, tiles_config: dict) -> bool:
    """Check if a tile is walkable."""
    if tile in tiles_config["floor"]:
        return True
    if str(tile) in tiles_config["ore"]:
        return True
    if tile in tiles_config.get("hazard", []):
        return True  # Walkable but harmful
    return False

def bfs_shortest_path(
    grid: list[list[int]],
    start: tuple[int, int],
    end: tuple[int, int],
    tiles_config: Optional[dict] = None,
    max_steps: Optional[int] = None
) -> Optional[list[tuple[int, int]]]:
    """
    Find shortest path from start to end using BFS.
    
    Args:
        grid: 2D world grid
        start: (x, y) starting position
        end: (x, y) target position
        tiles_config: Tile configuration dict
        max_steps: Maximum path length allowed (None = unlimited)
    
    Returns:
        List of (x, y) positions from start to end (inclusive), or None if no path.
    """
    if tiles_config is None:
        tiles_config = load_tile_config()
    
    size = len(grid)
    sx, sy = start
    ex, ey = end
    
    # Bounds check
    if not (0 <= sx < size and 0 <= sy < size):
        return None
    if not (0 <= ex < size and 0 <= ey < size):
        return None
    
    # Check if end is walkable
    if not is_walkable(grid[ey][ex], tiles_config):
        return None
    
    # BFS
    queue = deque([(sx, sy, [(sx, sy)])])
    visited = {(sx, sy)}
    
    while queue:
        x, y, path = queue.popleft()
        
        if (x, y) == (ex, ey):
            return path
        
        # Check max steps
        if max_steps is not None and len(path) > max_steps:
            continue
        
        # Explore neighbors (4-directional)
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            
            if 0 <= nx < size and 0 <= ny < size:
                if (nx, ny) not in visited:
                    if is_walkable(grid[ny][nx], tiles_config):
                        visited.add((nx, ny))
                        queue.append((nx, ny, path + [(nx, ny)]))
    
    return None

def path_distance(
    grid: list[list[int]],
    start: tuple[int, int],
    end: tuple[int, int],
    tiles_config: Optional[dict] = None
) -> Optional[int]:
    """
    Get shortest path distance between two points.
    Returns number of steps, or None if no path exists.
    """
    path = bfs_shortest_path(grid, start, end, tiles_config)
    if path is None:
        return None
    return len(path) - 1  # -1 because path includes start

def find_nearest_valid_tile(
    grid: list[list[int]],
    start: tuple[int, int],
    exclude_sector: Optional[tuple[int, int, int, int]] = None,
    tiles_config: Optional[dict] = None
) -> Optional[tuple[int, int]]:
    """
    Spiral search outward from start to find first valid walkable tile.
    Used for ejection when sector regenerates.
    
    Args:
        grid: 2D world grid
        start: (x, y) starting position
        exclude_sector: (min_x, min_y, max_x, max_y) bounds to exclude
        tiles_config: Tile configuration dict
    
    Returns:
        (x, y) of nearest valid tile, or None if none found.
    """
    if tiles_config is None:
        tiles_config = load_tile_config()
    
    size = len(grid)
    sx, sy = start
    
    # Spiral outward
    for radius in range(0, size):
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if abs(dx) != radius and abs(dy) != radius:
                    continue  # Only check perimeter
                
                nx, ny = sx + dx, sy + dy
                
                if not (0 <= nx < size and 0 <= ny < size):
                    continue
                
                # Check if in excluded sector
                if exclude_sector:
                    min_x, min_y, max_x, max_y = exclude_sector
                    if min_x <= nx <= max_x and min_y <= ny <= max_y:
                        continue
                
                if is_walkable(grid[ny][nx], tiles_config):
                    return (nx, ny)
    
    return None
