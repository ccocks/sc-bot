"""
Line of Sight calculations for scouting.
Uses Bresenham's line algorithm to check wall blocking.
"""

import json
import math
from typing import Optional

def load_tile_config() -> dict:
    with open("config/tiles.json", "r") as f:
        return json.load(f)

def is_wall(tile: int, tiles_config: dict) -> bool:
    """Check if a tile blocks line of sight."""
    return tile in tiles_config["wall"]

def bresenham_line(x0: int, y0: int, x1: int, y1: int) -> list[tuple[int, int]]:
    """
    Generate all grid cells along a line from (x0,y0) to (x1,y1).
    """
    points = []
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    
    x, y = x0, y0
    while True:
        points.append((x, y))
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
    
    return points

def has_line_of_sight(
    grid: list[list[int]],
    start: tuple[int, int],
    end: tuple[int, int],
    tiles_config: Optional[dict] = None
) -> bool:
    """
    Check if there's clear line of sight from start to end.
    Returns False if any wall tile blocks the path.
    """
    if tiles_config is None:
        tiles_config = load_tile_config()
    
    size = len(grid)
    line = bresenham_line(start[0], start[1], end[0], end[1])
    
    # Check all tiles along the line (except start and end)
    for x, y in line[1:-1]:
        if not (0 <= x < size and 0 <= y < size):
            return False
        if is_wall(grid[y][x], tiles_config):
            return False
    
    return True

def get_visible_tiles_in_radius(
    grid: list[list[int]],
    center: tuple[int, int],
    radius: int,
    tiles_config: Optional[dict] = None
) -> list[tuple[int, int]]:
    """
    Get all tiles within radius that have line of sight from center.
    Used for !scout command.
    """
    if tiles_config is None:
        tiles_config = load_tile_config()
    
    size = len(grid)
    cx, cy = center
    visible = []
    
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            # Check if within circle
            if dx*dx + dy*dy > radius*radius:
                continue
            
            tx, ty = cx + dx, cy + dy
            
            # Bounds check
            if not (0 <= tx < size and 0 <= ty < size):
                continue
            
            # Check line of sight
            if has_line_of_sight(grid, center, (tx, ty), tiles_config):
                visible.append((tx, ty))
    
    return visible

def scout_area(
    grid: list[list[int]],
    world_state: dict,
    player_pos: tuple[int, int],
    radius: int,
    player_name: str
) -> tuple[list[tuple[int, int]], int]:
    """
    Perform a scout action. Updates world_state scouted tiles.
    
    Returns:
        (list of newly scouted tiles, energy cost)
    """
    visible = get_visible_tiles_in_radius(grid, player_pos, radius)
    
    # Calculate energy cost: ceil(tiles_checked / 5)
    energy_cost = math.ceil(len(visible) / 5)
    
    # Update scouted tiles in world state
    if "scouted" not in world_state:
        world_state["scouted"] = {}
    
    newly_scouted = []
    for (tx, ty) in visible:
        key = f"{tx},{ty}"
        if key not in world_state["scouted"]:
            world_state["scouted"][key] = {
                "by": player_name,
                "at": None  # Will be set to timestamp
            }
            newly_scouted.append((tx, ty))
    
    return newly_scouted, energy_cost
