"""
World generation: 200x200 maze with varying complexity by distance from hub.
"""

import random
import json
from collections import deque
from typing import Optional

def load_tile_config() -> dict:
    with open("config/tiles.json", "r") as f:
        return json.load(f)

def load_settings() -> dict:
    with open("config/settings.json", "r") as f:
        return json.load(f)

def distance_from_hub(x: int, y: int, hub_center: tuple[int, int]) -> float:
    """Euclidean distance from hub center."""
    return ((x - hub_center[0])**2 + (y - hub_center[1])**2) ** 0.5

def get_complexity(dist: float, max_dist: float) -> float:
    """
    Returns complexity factor 0.0 (simple near hub) to 1.0 (complex at edges).
    """
    return min(1.0, dist / max_dist)

def generate_world(seed: Optional[int] = None) -> list[list[int]]:
    """
    Generate a 200x200 world grid.
    Returns 2D array where grid[y][x] = costume number.
    """
    if seed is not None:
        random.seed(seed)
    
    tiles = load_tile_config()
    settings = load_settings()
    
    size = settings["world_size"]
    hub_center = tuple(settings["hub_center"])
    hub_radius = settings["hub_radius"]
    
    floor_tile = tiles["primary_floor"]
    wall_tile = tiles["primary_wall"]
    
    # Initialize with walls
    grid = [[wall_tile for _ in range(size)] for _ in range(size)]
    
    # Carve out the hub area (always open floor)
    for y in range(hub_center[1] - hub_radius, hub_center[1] + hub_radius + 1):
        for x in range(hub_center[0] - hub_radius, hub_center[0] + hub_radius + 1):
            if 0 <= x < size and 0 <= y < size:
                grid[y][x] = floor_tile
    
    # Use recursive backtracker maze generation
    # Start from hub and carve outward
    visited = [[False] * size for _ in range(size)]
    
    # Mark hub as visited
    for y in range(hub_center[1] - hub_radius, hub_center[1] + hub_radius + 1):
        for x in range(hub_center[0] - hub_radius, hub_center[0] + hub_radius + 1):
            if 0 <= x < size and 0 <= y < size:
                visited[y][x] = True
    
    # Carve maze from multiple starting points around hub edge
    start_points = []
    for y in range(hub_center[1] - hub_radius - 1, hub_center[1] + hub_radius + 2):
        for x in range(hub_center[0] - hub_radius - 1, hub_center[0] + hub_radius + 2):
            if 0 <= x < size and 0 <= y < size:
                if not visited[y][x]:
                    # Check if adjacent to hub
                    for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ny, nx = y + dy, x + dx
                        if 0 <= nx < size and 0 <= ny < size and visited[ny][nx]:
                            start_points.append((x, y))
                            break
    
    # Shuffle and limit start points
    random.shuffle(start_points)
    start_points = start_points[:8]  # 8 main corridors from hub
    
    def carve_maze(start_x: int, start_y: int):
        """Recursive backtracker maze carving."""
        stack = [(start_x, start_y)]
        visited[start_y][start_x] = True
        grid[start_y][start_x] = floor_tile
        
        while stack:
            x, y = stack[-1]
            
            # Get unvisited neighbors (2 steps away for maze walls)
            neighbors = []
            for dy, dx in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < size and 0 <= ny < size and not visited[ny][nx]:
                    neighbors.append((nx, ny, dx // 2, dy // 2))
            
            if neighbors:
                # Choose based on complexity (prefer continuing straight when simple)
                dist = distance_from_hub(x, y, hub_center)
                complexity = get_complexity(dist, size * 0.7)
                
                if random.random() < complexity:
                    # High complexity: random choice
                    nx, ny, wx, wy = random.choice(neighbors)
                else:
                    # Low complexity: prefer continuing in same direction or random
                    nx, ny, wx, wy = random.choice(neighbors)
                
                # Carve wall between current and next
                grid[y + wy][x + wx] = floor_tile
                visited[y + wy][x + wx] = True
                
                # Carve next cell
                grid[ny][nx] = floor_tile
                visited[ny][nx] = True
                
                stack.append((nx, ny))
            else:
                stack.pop()
    
    # Carve from each start point
    for sx, sy in start_points:
        if not visited[sy][sx]:
            carve_maze(sx, sy)
    
    # Fill remaining unvisited areas with their own maze sections
    for y in range(1, size - 1, 2):
        for x in range(1, size - 1, 2):
            if not visited[y][x]:
                carve_maze(x, y)
    
    # Add extra loops based on complexity (reduce dead ends near hub)
    for y in range(1, size - 1):
        for x in range(1, size - 1):
            if grid[y][x] == wall_tile:
                dist = distance_from_hub(x, y, hub_center)
                complexity = get_complexity(dist, size * 0.7)
                
                # Count adjacent floors
                floor_neighbors = 0
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    if grid[y + dy][x + dx] == floor_tile:
                        floor_neighbors += 1
                
                # Add loops (remove walls) more often near hub
                if floor_neighbors >= 2:
                    loop_chance = 0.15 * (1 - complexity)
                    if random.random() < loop_chance:
                        grid[y][x] = floor_tile
    
    # Sprinkle ores based on tier/distance
    ore_tiles = tiles["ore"]
    for y in range(size):
        for x in range(size):
            if grid[y][x] == floor_tile:
                dist = distance_from_hub(x, y, hub_center)
                
                # Determine which tier ores can spawn here
                ore_chance = 0.03  # 3% base chance for ore
                if random.random() < ore_chance:
                    # Pick an ore appropriate for this distance
                    valid_ores = []
                    for ore_id, ore_data in ore_tiles.items():
                        ore_tier = ore_data["tier"]
                        # Tier 1: 0-25, Tier 2: 26-50, etc.
                        min_dist_for_tier = (ore_tier - 1) * 25
                        max_dist_for_tier = ore_tier * 40
                        if min_dist_for_tier <= dist <= max_dist_for_tier:
                            valid_ores.append(int(ore_id))
                    
                    if valid_ores:
                        grid[y][x] = random.choice(valid_ores)
    
    return grid

def flatten_grid(grid: list[list[int]]) -> list:
    """
    Flatten 2D grid to 1D for Scratch GRID list.
    Index 0 = (x=0, y=0), increases x first, then y.
    
    Returns list of 120,000 elements (3 layers).
    """
    size = len(grid)
    layer0 = []
    
    for y in range(size):
        for x in range(size):
            layer0.append(grid[y][x])
    
    # Pad with "" for layers 1 and 2
    blank_layers = [""] * (size * size * 2)
    
    return layer0 + blank_layers

def get_sector(x: int, y: int, sector_size: int = 25) -> tuple[int, int]:
    """Get sector coordinates for a world position."""
    return (x // sector_size, y // sector_size)

def get_sector_bounds(sx: int, sy: int, sector_size: int = 25) -> tuple[int, int, int, int]:
    """Get world coordinate bounds for a sector. Returns (min_x, min_y, max_x, max_y)."""
    min_x = sx * sector_size
    min_y = sy * sector_size
    max_x = min_x + sector_size - 1
    max_y = min_y + sector_size - 1
    return (min_x, min_y, max_x, max_y)

def save_world(grid: list[list[int]], filepath: str = "state/world.json"):
    """Save world state to file."""
    with open(filepath, "w") as f:
        json.dump({
            "grid": grid,
            "scouted": {},  # Will be populated as players scout
            "sectors": {},   # Sector metadata (regen timers, etc.)
            "structures": [],
            "calamities": [],
            "bounties": []
        }, f)

def load_world(filepath: str = "state/world.json") -> dict:
    """Load world state from file."""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
