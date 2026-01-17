Confirmed. Here's the final data model and I'll start writing code.

## Final list schema

| List name | Type | Notes |
|---|---|---|
| `GRID` | mixed | 120,000 entries. `[0..39999]` = costume int, `[40000..119999]` = `""` |
| `USERS:USERNAME` | string | parallel index |
| `USERS:X` | int | parallel index |
| `USERS:Y` | int | parallel index |
| `ENEMIES:X` | int | parallel index |
| `ENEMIES:Y` | int | parallel index |
| `ENEMIES:TYPE` | int | 1=Bat, 2=Slime, 3=Spider, 4=Skeleton |
| `ACTIONS:ACTION` | string | parallel index |
| `ACTIONS:TIMESTAMP` | string | parallel index |
| `ACTIONS:USERNAME` | string | parallel index |

---

## Project structure

```
cave-mmo/
├── .github/
│   └── workflows/
│       └── tick.yml
├── config/
│   ├── tiles.json
│   ├── items.json
│   ├── creatures.json
│   ├── tiers.json
│   └── settings.json
├── state/
│   ├── world.json
│   ├── players.json
│   ├── entities.json
│   └── processed.json
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── scratch_api.py
│   ├── world_gen.py
│   ├── pathfinding.py
│   ├── los.py
│   ├── commands.py
│   ├── combat.py
│   ├── economy.py
│   └── tick.py
├── requirements.txt
└── README.md
```

---

## Code

### `requirements.txt`

```
scratchattach>=2.0
```

---

### `config/settings.json`

```json
{
  "project_id": 1266175173,
  "world_size": 200,
  "hub_center": [100, 100],
  "hub_radius": 5,
  "tp_max_path": 15,
  "tp_energy_per_step": 3,
  "scout_max_radius": 10,
  "flee_distance": 10,
  "disengage_distance": 40,
  "sector_size": 25,
  "sectors_per_axis": 8,
  "sectors_regen_per_day": 16,
  "regen_warning_hours": 24,
  "creature_respawn_minutes": 60,
  "max_actions_feed": 50,
  "rate_limit_seconds": 1.0
}
```

---

### `config/tiles.json`

```json
{
  "floor": [45, 56, 60, 61, 62],
  "wall": [51, 52, 54, 55, 58],
  "ore": {
    "25": {"name": "emerald_ore", "tier": 5, "yield": "emerald"},
    "26": {"name": "coal_ore", "tier": 1, "yield": "coal"},
    "27": {"name": "nether_quartz_ore", "tier": 4, "yield": "quartz"},
    "28": {"name": "copper_ore", "tier": 1, "yield": "copper"},
    "29": {"name": "deepslate_lapis_ore", "tier": 3, "yield": "lapis"},
    "30": {"name": "redstone_ore", "tier": 2, "yield": "redstone"},
    "31": {"name": "lapis_ore", "tier": 2, "yield": "lapis"},
    "32": {"name": "deepslate_diamond_ore", "tier": 5, "yield": "diamond"},
    "33": {"name": "nether_gold_ore", "tier": 4, "yield": "gold"},
    "34": {"name": "deepslate_emerald_ore", "tier": 5, "yield": "emerald"},
    "35": {"name": "iron_ore", "tier": 2, "yield": "iron"},
    "36": {"name": "deepslate_coal_ore", "tier": 2, "yield": "coal"},
    "37": {"name": "deepslate_redstone_ore", "tier": 3, "yield": "redstone"},
    "38": {"name": "deepslate_iron_ore", "tier": 3, "yield": "iron"},
    "39": {"name": "deepslate_gold_ore", "tier": 4, "yield": "gold"},
    "40": {"name": "deepslate_copper_ore", "tier": 2, "yield": "copper"},
    "41": {"name": "diamond_ore", "tier": 4, "yield": "diamond"},
    "42": {"name": "gold_ore", "tier": 3, "yield": "gold"}
  },
  "hazard": [64],
  "primary_floor": 56,
  "primary_wall": 54
}
```

---

### `config/tiers.json`

```json
{
  "tiers": [
    {"tier": 1, "min_dist": 0, "max_dist": 25},
    {"tier": 2, "min_dist": 26, "max_dist": 50},
    {"tier": 3, "min_dist": 51, "max_dist": 80},
    {"tier": 4, "min_dist": 81, "max_dist": 120},
    {"tier": 5, "min_dist": 121, "max_dist": 999}
  ],
  "harvest_cooldowns_minutes": {
    "1": 360,
    "2": 180,
    "3": 90,
    "4": 45,
    "5": 20
  },
  "cooldown_multiplier_per_level_diff": 1.5
}
```

---

### `config/creatures.json`

```json
{
  "types": {
    "1": {
      "name": "Bat",
      "hp": 10,
      "damage": 2,
      "speed": 2,
      "tier": 1,
      "alert_chance_base": 0.3,
      "drops": {"coal": 1}
    },
    "2": {
      "name": "Slime",
      "hp": 25,
      "damage": 5,
      "speed": 1,
      "tier": 2,
      "alert_chance_base": 0.2,
      "drops": {"slime": 2, "copper": 1}
    },
    "3": {
      "name": "Spider",
      "hp": 40,
      "damage": 8,
      "speed": 3,
      "tier": 3,
      "alert_chance_base": 0.25,
      "drops": {"string": 2, "iron": 1}
    },
    "4": {
      "name": "Skeleton",
      "hp": 60,
      "damage": 12,
      "speed": 2,
      "tier": 4,
      "alert_chance_base": 0.15,
      "drops": {"bone": 3, "gold": 1}
    }
  }
}
```

---

### `config/items.json`

```json
{
  "resources": {
    "coal": {"tier": 1, "stack": 10, "base_price": 5},
    "copper": {"tier": 1, "stack": 10, "base_price": 8},
    "iron": {"tier": 2, "stack": 10, "base_price": 15},
    "redstone": {"tier": 2, "stack": 10, "base_price": 12},
    "lapis": {"tier": 2, "stack": 10, "base_price": 14},
    "gold": {"tier": 3, "stack": 10, "base_price": 30},
    "quartz": {"tier": 4, "stack": 10, "base_price": 50},
    "diamond": {"tier": 5, "stack": 10, "base_price": 100},
    "emerald": {"tier": 5, "stack": 10, "base_price": 120},
    "slime": {"tier": 2, "stack": 10, "base_price": 10},
    "string": {"tier": 3, "stack": 10, "base_price": 8},
    "bone": {"tier": 4, "stack": 10, "base_price": 12}
  },
  "tools": {
    "wood_pickaxe": {"tier": 1, "durability": 50, "power": 1, "cost": {"coal": 5}},
    "stone_pickaxe": {"tier": 2, "durability": 100, "power": 2, "cost": {"iron": 3}},
    "iron_pickaxe": {"tier": 3, "durability": 200, "power": 3, "cost": {"iron": 10, "coal": 5}}
  },
  "weapons": {
    "wood_sword": {"tier": 1, "durability": 40, "damage": 5, "cost": {"coal": 3}},
    "stone_sword": {"tier": 2, "durability": 80, "damage": 10, "cost": {"iron": 2}},
    "iron_sword": {"tier": 3, "durability": 150, "damage": 18, "cost": {"iron": 8, "coal": 3}}
  },
  "consumables": {
    "health_potion": {"heal": 30, "stack": 5, "cost": {"redstone": 3, "slime": 1}},
    "energy_potion": {"energy": 50, "stack": 5, "cost": {"lapis": 2, "coal": 2}}
  }
}
```

---

### `src/scratch_api.py`

```python
"""
Scratch API wrapper using scratchattach.
Handles reading comments, posting replies, and updating project lists.
"""

import time
import json
import scratchattach as sa
from typing import Optional

class ScratchAPI:
    def __init__(self, session_id: str, project_id: int, rate_limit: float = 1.0):
        self.session = sa.login_by_id(session_id)
        self.project = self.session.connect_project(project_id)
        self.project_id = project_id
        self.rate_limit = rate_limit
        self.last_request_time = 0.0
        self._list_id_cache: dict[str, str] = {}
    
    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limit."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request_time = time.time()
    
    def get_comments(self, limit: int = 40, offset: int = 0) -> list:
        """Fetch project comments."""
        self._wait_for_rate_limit()
        try:
            comments = self.project.comments(limit=limit, offset=offset)
            return comments
        except Exception as e:
            print(f"Error fetching comments: {e}")
            return []
    
    def reply_to_comment(self, comment_id: str, content: str) -> bool:
        """Reply to a specific comment."""
        self._wait_for_rate_limit()
        try:
            comment = self.project.comment_by_id(comment_id)
            if comment:
                comment.reply(content)
                return True
        except Exception as e:
            print(f"Error replying to comment {comment_id}: {e}")
        return False
    
    def get_project_json(self) -> Optional[dict]:
        """Download and return the project JSON."""
        self._wait_for_rate_limit()
        try:
            return self.project.raw_json()
        except Exception as e:
            print(f"Error getting project JSON: {e}")
            return None
    
    def _build_list_id_cache(self, project_json: dict):
        """Build a mapping of list names to their IDs."""
        self._list_id_cache = {}
        for target in project_json.get("targets", []):
            if target.get("isStage", False):
                lists = target.get("lists", {})
                for list_id, list_data in lists.items():
                    if isinstance(list_data, list) and len(list_data) >= 1:
                        list_name = list_data[0]
                        self._list_id_cache[list_name] = list_id
                break
    
    def update_lists(self, list_updates: dict[str, list]) -> bool:
        """
        Update multiple lists in the project.
        
        Args:
            list_updates: Dict mapping list names to their new contents.
                         e.g., {"GRID": [...], "USERS:X": [...]}
        
        Returns:
            True if successful, False otherwise.
        """
        project_json = self.get_project_json()
        if not project_json:
            return False
        
        # Build cache if needed
        if not self._list_id_cache:
            self._build_list_id_cache(project_json)
        
        # Find stage target and update lists
        for target in project_json.get("targets", []):
            if target.get("isStage", False):
                lists = target.get("lists", {})
                
                for list_name, new_contents in list_updates.items():
                    list_id = self._list_id_cache.get(list_name)
                    if list_id and list_id in lists:
                        # lists[list_id] = [name, [values...]]
                        lists[list_id][1] = new_contents
                    else:
                        print(f"Warning: List '{list_name}' not found in project")
                
                break
        
        # Upload modified JSON
        self._wait_for_rate_limit()
        try:
            self.project.set_json(project_json)
            return True
        except Exception as e:
            print(f"Error uploading project JSON: {e}")
            return False
```

---

### `src/world_gen.py`

```python
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
```

---

### `src/pathfinding.py`

```python
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
```

---

### `src/los.py`

```python
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
```

---

### `src/commands.py`

```python
"""
Command parser and handlers for all player commands.
"""

import json
import re
import math
import random
from typing import Optional, Callable
from datetime import datetime

from src.pathfinding import bfs_shortest_path, path_distance, is_walkable, load_tile_config
from src.los import scout_area, get_visible_tiles_in_radius

def load_settings() -> dict:
    with open("config/settings.json", "r") as f:
        return json.load(f)

def load_players() -> dict:
    try:
        with open("state/players.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_players(players: dict):
    with open("state/players.json", "w") as f:
        json.dump(players, f, indent=2)

def load_entities() -> dict:
    try:
        with open("state/entities.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"creatures": [], "next_id": 1}

def save_entities(entities: dict):
    with open("state/entities.json", "w") as f:
        json.dump(entities, f, indent=2)

class CommandHandler:
    def __init__(self, world_state: dict, grid: list[list[int]]):
        self.world_state = world_state
        self.grid = grid
        self.settings = load_settings()
        self.tiles_config = load_tile_config()
        self.players = load_players()
        self.entities = load_entities()
        self.responses = []  # List of (comment_id, response_text)
    
    def handle_command(self, username: str, comment_id: str, text: str) -> Optional[str]:
        """
        Parse and handle a command from a user comment.
        Returns response text, or None if not a command.
        """
        text = text.strip().lower()
        
        if not text.startswith("!"):
            return None
        
        parts = text.split()
        cmd = parts[0]
        args = parts[1:]
        
        handlers = {
            "!start": self.cmd_start,
            "!help": self.cmd_help,
            "!status": self.cmd_status,
            "!tp": self.cmd_tp,
            "!look": self.cmd_look,
            "!scout": self.cmd_scout,
            "!mine": self.cmd_mine,
            "!attack": self.cmd_attack,
            "!flee": self.cmd_flee,
            "!respawn": self.cmd_respawn,
        }
        
        handler = handlers.get(cmd)
        if handler:
            return handler(username, args)
        else:
            return f"Unknown command: {cmd}. Use !help for available commands."
    
    def get_player(self, username: str) -> Optional[dict]:
        """Get player data, or None if not registered."""
        return self.players.get(username)
    
    def create_player(self, username: str) -> dict:
        """Create a new player at hub center."""
        hub = self.settings["hub_center"]
        player = {
            "x": hub[0],
            "y": hub[1],
            "hp": 100,
            "max_hp": 100,
            "energy": 100,
            "max_energy": 100,
            "xp": 0,
            "level": 1,
            "coins": 0,
            "inventory": {},  # item_name: quantity
            "equipment": {
                "weapon": None,
                "tool": None,
                "armor": None
            },
            "cooldowns": {},  # tier harvest cooldowns
            "engaged_with": None,  # creature id if in combat
            "dead": False
        }
        self.players[username] = player
        save_players(self.players)
        return player
    
    def cmd_start(self, username: str, args: list) -> str:
        """Register a new player."""
        if username in self.players:
            return f"Welcome back, {username}! You're already registered. Use !status to see your info."
        
        player = self.create_player(username)
        hub = self.settings["hub_center"]
        return f"Welcome to The Living Cave, {username}! You start at the hub ({hub[0]}, {hub[1]}). Use !help for commands."
    
    def cmd_help(self, username: str, args: list) -> str:
        """Show available commands."""
        return (
            "Commands: !start, !status, !tp x y, !look, !scout r, "
            "!mine, !attack, !flee, !respawn center/station. "
            "Move with !tp (max 15 steps, costs energy). Scout reveals ores/enemies."
        )
    
    def cmd_status(self, username: str, args: list) -> str:
        """Show player status."""
        player = self.get_player(username)
        if not player:
            return "You haven't started yet! Use !start to begin."
        
        inv_summary = ", ".join([f"{k}:{v}" for k, v in player["inventory"].items()][:5])
        if not inv_summary:
            inv_summary = "empty"
        
        status = (
            f"[{username}] Pos: ({player['x']}, {player['y']}) | "
            f"HP: {player['hp']}/{player['max_hp']} | "
            f"Energy: {player['energy']}/{player['max_energy']} | "
            f"Level: {player['level']} | Coins: {player['coins']} | "
            f"Inv: {inv_summary}"
        )
        
        if player.get("engaged_with"):
            status += " | IN COMBAT"
        if player.get("dead"):
            status += " | DEAD (use !respawn)"
        
        return status
    
    def cmd_tp(self, username: str, args: list) -> str:
        """Teleport to a position (maze pathfinding)."""
        player = self.get_player(username)
        if not player:
            return "Use !start first."
        
        if player.get("dead"):
            return "You are dead. Use !respawn center or !respawn station."
        
        if len(args) < 2:
            return "Usage: !tp x y"
        
        try:
            tx, ty = int(args[0]), int(args[1])
        except ValueError:
            return "Invalid coordinates. Usage: !tp x y"
        
        size = self.settings["world_size"]
        if not (0 <= tx < size and 0 <= ty < size):
            return f"Coordinates out of bounds. World is {size}x{size}."
        
        start = (player["x"], player["y"])
        end = (tx, ty)
        
        # Check if target is walkable
        if not is_walkable(self.grid[ty][tx], self.tiles_config):
            return f"Cannot teleport to ({tx}, {ty}) - not walkable."
        
        # Find path
        max_path = self.settings["tp_max_path"]
        path = bfs_shortest_path(self.grid, start, end, self.tiles_config, max_path)
        
        if path is None:
            return f"No valid path to ({tx}, {ty}) within {max_path} steps."
        
        path_len = len(path) - 1
        
        # Check engaged combat restriction
        if player.get("engaged_with"):
            creature = self.get_creature_by_id(player["engaged_with"])
            if creature:
                old_dist = path_distance(self.grid, start, (creature["x"], creature["y"]), self.tiles_config)
                new_dist = path_distance(self.grid, end, (creature["x"], creature["y"]), self.tiles_config)
                
                if new_dist is not None and old_dist is not None:
                    if new_dist > old_dist:
                        return f"In combat! Can only move closer to enemy. Use !flee to escape."
        
        # Check energy cost
        energy_cost = path_len * self.settings["tp_energy_per_step"]
        if player["energy"] < energy_cost:
            return f"Not enough energy. Need {energy_cost}, have {player['energy']}."
        
        # Execute teleport
        player["x"] = tx
        player["y"] = ty
        player["energy"] -= energy_cost
        
        # Process creature movement if engaged
        combat_msg = ""
        if player.get("engaged_with"):
            combat_msg = self.process_creature_chase(username, player)
        
        save_players(self.players)
        
        result = f"Teleported to ({tx}, {ty}). Energy: {player['energy']}/{player['max_energy']}."
        if combat_msg:
            result += " " + combat_msg
        
        return result
    
    def cmd_look(self, username: str, args: list) -> str:
        """Describe the current tile and immediate surroundings."""
        player = self.get_player(username)
        if not player:
            return "Use !start first."
        
        x, y = player["x"], player["y"]
        tile = self.grid[y][x]
        
        # Get tile info
        tile_name = "floor"
        if str(tile) in self.tiles_config["ore"]:
            ore_info = self.tiles_config["ore"][str(tile)]
            tile_name = ore_info["name"]
        elif tile in self.tiles_config["hazard"]:
            tile_name = "hazard (magma)"
        
        # Check for nearby creatures (if scouted)
        nearby_creatures = []
        for creature in self.entities.get("creatures", []):
            dist = abs(creature["x"] - x) + abs(creature["y"] - y)
            if dist <= 5:
                key = f"{creature['x']},{creature['y']}"
                if key in self.world_state.get("scouted", {}):
                    nearby_creatures.append(f"{creature['type_name']} at ({creature['x']},{creature['y']})")
        
        result = f"You are at ({x}, {y}) on {tile_name}."
        if nearby_creatures:
            result += f" Nearby: {', '.join(nearby_creatures)}."
        
        return result
    
    def cmd_scout(self, username: str, args: list) -> str:
        """Scout an area around current position."""
        player = self.get_player(username)
        if not player:
            return "Use !start first."
        
        if player.get("dead"):
            return "You are dead. Use !respawn."
        
        radius = self.settings["scout_max_radius"]
        if args:
            try:
                radius = min(int(args[0]), self.settings["scout_max_radius"])
            except ValueError:
                pass
        
        if radius < 1:
            radius = 1
        
        pos = (player["x"], player["y"])
        newly_scouted, energy_cost = scout_area(
            self.grid, self.world_state, pos, radius, username
        )
        
        if player["energy"] < energy_cost:
            return f"Not enough energy. Need {energy_cost}, have {player['energy']}."
        
        player["energy"] -= energy_cost
        
        # Check for creatures and alert chance
        alert_msg = ""
        creatures_found = []
        for creature in self.entities.get("creatures", []):
            cpos = (creature["x"], creature["y"])
            if cpos in [(t[0], t[1]) for t in newly_scouted]:
                creatures_found.append(creature)
        
        if creatures_found and not player.get("engaged_with"):
            # Roll for alert (only one creature can be alerted)
            for creature in creatures_found:
                dist = math.sqrt((creature["x"] - pos[0])**2 + (creature["y"] - pos[1])**2)
                # Alert chance higher when closer
                alert_chance = max(0.1, 0.5 - (dist / radius) * 0.3)
                
                if random.random() < alert_chance:
                    player["engaged_with"] = creature["id"]
                    creature["chasing"] = username
                    alert_msg = f" ALERT! {creature['type_name']} noticed you!"
                    break
        
        # Count ores found
        ores_found = 0
        for (tx, ty) in newly_scouted:
            if str(self.grid[ty][tx]) in self.tiles_config["ore"]:
                ores_found += 1
        
        save_players(self.players)
        save_entities(self.entities)
        
        return (
            f"Scouted {len(newly_scouted)} tiles (radius {radius}). "
            f"Found {ores_found} ore(s), {len(creatures_found)} creature(s). "
            f"Energy: {player['energy']}/{player['max_energy']}.{alert_msg}"
        )
    
    def cmd_mine(self, username: str, args: list) -> str:
        """Mine ore at current position."""
        player = self.get_player(username)
        if not player:
            return "Use !start first."
        
        if player.get("dead"):
            return "You are dead. Use !respawn."
        
        x, y = player["x"], player["y"]
        tile = self.grid[y][x]
        
        tile_str = str(tile)
        if tile_str not in self.tiles_config["ore"]:
            return "No ore here to mine."
        
        ore_info = self.tiles_config["ore"][tile_str]
        ore_name = ore_info["yield"]
        ore_tier = ore_info["tier"]
        
        # Check harvest cooldown
        cooldown_key = f"tier_{ore_tier}"
        if cooldown_key in player.get("cooldowns", {}):
            remaining = player["cooldowns"][cooldown_key]
            if remaining > 0:
                return f"Tier {ore_tier} harvest on cooldown. {remaining} minutes remaining."
        
        # Mine the ore
        if ore_name not in player["inventory"]:
            player["inventory"][ore_name] = 0
        player["inventory"][ore_name] += 1
        
        # Replace ore with floor
        self.grid[y][x] = self.tiles_config["primary_floor"]
        
        # Apply cooldown based on player level vs tier
        with open("config/tiers.json", "r") as f:
            tiers_config = json.load(f)
        
        base_cooldown = tiers_config["harvest_cooldowns_minutes"].get(str(ore_tier), 30)
        level_diff = max(0, player["level"] - ore_tier)
        multiplier = tiers_config["cooldown_multiplier_per_level_diff"] ** level_diff
        final_cooldown = int(base_cooldown * multiplier)
        
        if "cooldowns" not in player:
            player["cooldowns"] = {}
        player["cooldowns"][cooldown_key] = final_cooldown
        
        # XP gain
        player["xp"] += ore_tier * 5
        self.check_level_up(player)
        
        # Check for creature alert from mining noise
        alert_msg = ""
        if not player.get("engaged_with"):
            for creature in self.entities.get("creatures", []):
                dist = abs(creature["x"] - x) + abs(creature["y"] - y)
                if dist <= 5:
                    if random.random() < 0.3:
                        player["engaged_with"] = creature["id"]
                        creature["chasing"] = username
                        alert_msg = f" Mining noise alerted a {creature['type_name']}!"
                        break
        
        save_players(self.players)
        save_entities(self.entities)
        
        return f"Mined 1 {ore_name}! Inventory: {player['inventory'].get(ore_name, 0)}.{alert_msg}"
    
    def cmd_attack(self, username: str, args: list) -> str:
        """Attack an engaged creature or nearby creature."""
        player = self.get_player(username)
        if not player:
            return "Use !start first."
        
        if player.get("dead"):
            return "You are dead. Use !respawn."
        
        creature = None
        
        if player.get("engaged_with"):
            creature = self.get_creature_by_id(player["engaged_with"])
        else:
            # Look for creature within 3 tiles
            x, y = player["x"], player["y"]
            for c in self.entities.get("creatures", []):
                dist = abs(c["x"] - x) + abs(c["y"] - y)
                if dist <= 3:
                    creature = c
                    player["engaged_with"] = c["id"]
                    c["chasing"] = username
                    break
        
        if not creature:
            return "No creature to attack. Scout to find enemies or get within 3 tiles."
        
        # Calculate damage
        base_damage = 5
        weapon = player["equipment"].get("weapon")
        if weapon:
            with open("config/items.json", "r") as f:
                items = json.load(f)
            if weapon in items.get("weapons", {}):
                base_damage = items["weapons"][weapon]["damage"]
        
        creature["hp"] -= base_damage
        
        result = f"You hit {creature['type_name']} for {base_damage} damage! "
        
        if creature["hp"] <= 0:
            # Creature dies
            result += f"{creature['type_name']} defeated! "
            
            # Drop loot
            with open("config/creatures.json", "r") as f:
                creatures_config = json.load(f)
            
            ctype = str(creature["type"])
            drops = creatures_config["types"].get(ctype, {}).get("drops", {})
            for item, qty in drops.items():
                if item not in player["inventory"]:
                    player["inventory"][item] = 0
                player["inventory"][item] += qty
                result += f"+{qty} {item} "
            
            # XP
            player["xp"] += creature.get("tier", 1) * 10
            self.check_level_up(player)
            
            # Remove creature
            player["engaged_with"] = None
            self.entities["creatures"] = [
                c for c in self.entities["creatures"] if c["id"] != creature["id"]
            ]
        else:
            # Creature counterattacks
            with open("config/creatures.json", "r") as f:
                creatures_config = json.load(f)
            
            ctype = str(creature["type"])
            c_damage = creatures_config["types"].get(ctype, {}).get("damage", 5)
            player["hp"] -= c_damage
            result += f"{creature['type_name']} hits you for {c_damage}! HP: {player['hp']}/{player['max_hp']}"
            
            if player["hp"] <= 0:
                player["dead"] = True
                player["engaged_with"] = None
                result += " YOU DIED! Use !respawn center or !respawn station."
        
        save_players(self.players)
        save_entities(self.entities)
        
        return result
    
    def cmd_flee(self, username: str, args: list) -> str:
        """Attempt to flee from combat."""
        player = self.get_player(username)
        if not player:
            return "Use !start first."
        
        if not player.get("engaged_with"):
            return "You're not in combat."
        
        creature = self.get_creature_by_id(player["engaged_with"])
        if not creature:
            player["engaged_with"] = None
            save_players(self.players)
            return "The creature is gone. You're safe."
        
        # Find position 10 steps away from creature
        flee_distance = self.settings["flee_distance"]
        cx, cy = creature["x"], creature["y"]
        px, py = player["x"], player["y"]
        
        # Direction away from creature
        dx = px - cx
        dy = py - cy
        
        # Normalize and scale
        dist = max(1, math.sqrt(dx*dx + dy*dy))
        dx = int((dx / dist) * flee_distance)
        dy = int((dy / dist) * flee_distance)
        
        target_x = px + dx
        target_y = py + dy
        
        # Clamp to world bounds
        size = self.settings["world_size"]
        target_x = max(0, min(size - 1, target_x))
        target_y = max(0, min(size - 1, target_y))
        
        # Find nearest valid tile to target
        best_pos = None
        for r in range(20):
            for ddx in range(-r, r + 1):
                for ddy in range(-r, r + 1):
                    if abs(ddx) != r and abs(ddy) != r:
                        continue
                    nx, ny = target_x + ddx, target_y + ddy
                    if 0 <= nx < size and 0 <= ny < size:
                        if is_walkable(self.grid[ny][nx], self.tiles_config):
                            best_pos = (nx, ny)
                            break
                if best_pos:
                    break
            if best_pos:
                break
        
        if not best_pos:
            return "Nowhere to flee! Fight or die."
        
        player["x"], player["y"] = best_pos
        
        # Check if disengaged
        new_dist = path_distance(
            self.grid, best_pos, (cx, cy), self.tiles_config
        )
        
        disengage = self.settings["disengage_distance"]
        if new_dist and new_dist >= disengage:
            player["engaged_with"] = None
            creature["chasing"] = None
            result = f"You fled and escaped! Now at safety."
        else:
            result = f"You fled but {creature['type_name']} is still chasing! Distance: {new_dist}"
        
        save_players(self.players)
        save_entities(self.entities)
        
        return result
    
    def cmd_respawn(self, username: str, args: list) -> str:
        """Respawn after death."""
        player = self.get_player(username)
        if not player:
            return "Use !start first."
        
        if not player.get("dead"):
            return "You're not dead!"
        
        if not args:
            return "Usage: !respawn center (keep items) or !respawn station (lose half items, closer spawn)"
        
        choice = args[0].lower()
        
        if choice == "center":
            hub = self.settings["hub_center"]
            player["x"] = hub[0]
            player["y"] = hub[1]
            player["hp"] = player["max_hp"]
            player["energy"] = player["max_energy"]
            player["dead"] = False
            player["engaged_with"] = None
            
            save_players(self.players)
            return f"Respawned at hub ({hub[0]}, {hub[1]}). All items intact."
        
        elif choice == "station":
            # TODO: Find nearest recharge station
            # For now, spawn near death location with penalty
            hub = self.settings["hub_center"]
            player["x"] = hub[0]
            player["y"] = hub[1]
            
            # Lose half of stacked items
            for item in list(player["inventory"].keys()):
                player["inventory"][item] = player["inventory"][item] // 2
                if player["inventory"][item] <= 0:
                    del player["inventory"][item]
            
            player["hp"] = player["max_hp"]
            player["energy"] = player["max_energy"]
            player["dead"] = False
            player["engaged_with"] = None
            
            save_players(self.players)
            return f"Respawned at hub (no stations built yet). Lost half your items."
        
        else:
            return "Usage: !respawn center or !respawn station"
    
    def get_creature_by_id(self, creature_id: int) -> Optional[dict]:
        """Find a creature by ID."""
        for c in self.entities.get("creatures", []):
            if c["id"] == creature_id:
                return c
        return None
    
    def process_creature_chase(self, username: str, player: dict) -> str:
        """Process creature movement when player takes an action."""
        if not player.get("engaged_with"):
            return ""
        
        creature = self.get_creature_by_id(player["engaged_with"])
        if not creature:
            player["engaged_with"] = None
            return ""
        
        # Creature moves toward player
        with open("config/creatures.json", "r") as f:
            creatures_config = json.load(f)
        
        ctype = str(creature["type"])
        speed = creatures_config["types"].get(ctype, {}).get("speed", 1)
        
        # Simple movement: move `speed` steps toward player
        px, py = player["x"], player["y"]
        cx, cy = creature["x"], creature["y"]
        
        for _ in range(speed):
            dx = 0 if px == cx else (1 if px > cx else -1)
            dy = 0 if py == cy else (1 if py > cy else -1)
            
            # Prefer moving in the direction with greater difference
            if abs(px - cx) > abs(py - cy):
                new_x, new_y = cx + dx, cy
            else:
                new_x, new_y = cx, cy + dy
            
            if is_walkable(self.grid[new_y][new_x], self.tiles_config):
                cx, cy = new_x, new_y
        
        creature["x"], creature["y"] = cx, cy
        
        # Check if caught player
        if cx == px and cy == py:
            return f"{creature['type_name']} caught up to you!"
        
        dist = abs(px - cx) + abs(py - cy)
        return f"{creature['type_name']} closing in... Distance: {dist}"
    
    def check_level_up(self, player: dict):
        """Check and apply level ups."""
        xp_per_level = 100
        new_level = 1 + player["xp"] // xp_per_level
        if new_level > player["level"]:
            player["level"] = new_level
            player["max_hp"] += 10
            player["max_energy"] += 10
    
    def save_all(self):
        """Save all state."""
        save_players(self.players)
        save_entities(self.entities)
```

---
### `src/tick.py`

```python
"""
World tick processing: creature respawns, cooldown decrements, sector regen.
"""

import json
import random
from datetime import datetime, timedelta

def load_settings() -> dict:
    with open("config/settings.json", "r") as f:
        return json.load(f)

def load_creatures_config() -> dict:
    with open("config/creatures.json", "r") as f:
        return json.load(f)

def tick_cooldowns(players: dict):
    """Decrement all player cooldowns by 1 minute."""
    for username, player in players.items():
        if "cooldowns" not in player:
            continue
        
        for key in list(player["cooldowns"].keys()):
            player["cooldowns"][key] -= 1
            if player["cooldowns"][key] <= 0:
                del player["cooldowns"][key]

def tick_energy_regen(players: dict, amount: int = 2):
    """Regenerate player energy each tick."""
    for username, player in players.items():
        if player.get("dead"):
            continue
        player["energy"] = min(player["max_energy"], player["energy"] + amount)

def spawn_creatures(entities: dict, grid: list[list[int]], world_state: dict, count: int = 5):
    """Spawn new creatures if below threshold."""
    settings = load_settings()
    creatures_config = load_creatures_config()
    
    current_count = len(entities.get("creatures", []))
    max_creatures = 100  # Configurable
    
    if current_count >= max_creatures:
        return
    
    size = settings["world_size"]
    hub = settings["hub_center"]
    hub_radius = settings["hub_radius"]
    
    tiles_config_path = "config/tiles.json"
    with open(tiles_config_path, "r") as f:
        tiles = json.load(f)
    
    spawned = 0
    attempts = 0
    max_attempts = count * 10
    
    while spawned < count and attempts < max_attempts:
        attempts += 1
        
        x = random.randint(0, size - 1)
        y = random.randint(0, size - 1)
        
        # Not in hub
        if abs(x - hub[0]) <= hub_radius and abs(y - hub[1]) <= hub_radius:
            continue
        
        # Must be walkable
        tile = grid[y][x]
        if tile in tiles["wall"]:
            continue
        
        # Determine creature type based on distance
        dist = ((x - hub[0])**2 + (y - hub[1])**2) ** 0.5
        
        # Pick appropriate tier creature
        tier = 1
        if dist > 120:
            tier = 5
        elif dist > 80:
            tier = 4
        elif dist > 50:
            tier = 3
        elif dist > 25:
            tier = 2
        
        # Find creatures of appropriate tier
        valid_types = []
        for ctype, cdata in creatures_config["types"].items():
            if cdata["tier"] <= tier:
                valid_types.append(ctype)
        
        if not valid_types:
            continue
        
        chosen_type = random.choice(valid_types)
        cdata = creatures_config["types"][chosen_type]
        
        creature = {
            "id": entities.get("next_id", 1),
            "type": int(chosen_type),
            "type_name": cdata["name"],
            "x": x,
            "y": y,
            "hp": cdata["hp"],
            "max_hp": cdata["hp"],
            "tier": cdata["tier"],
            "chasing": None
        }
        
        if "creatures" not in entities:
            entities["creatures"] = []
        
        entities["creatures"].append(creature)
        entities["next_id"] = entities.get("next_id", 1) + 1
        spawned += 1

def process_tick(world_state: dict, grid: list[list[int]], players: dict, entities: dict):
    """Process one minute tick of the game world."""
    tick_cooldowns(players)
    tick_energy_regen(players)
    spawn_creatures(entities, grid, world_state, count=3)
    
    # TODO: Sector regeneration checks
    # TODO: Calamity progression
```

---

### `src/main.py`

```python
"""
Main entry point for the bot. Runs one iteration (called every minute by GitHub Actions).
"""

import os
import json
import time
from datetime import datetime

from src.scratch_api import ScratchAPI
from src.world_gen import generate_world, flatten_grid, load_world, save_world
from src.commands import CommandHandler, load_players, save_players, load_entities, save_entities
from src.tick import process_tick

def load_processed() -> set:
    """Load set of processed comment IDs."""
    try:
        with open("state/processed.json", "r") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_processed(processed: set):
    """Save processed comment IDs."""
    with open("state/processed.json", "w") as f:
        json.dump(list(processed), f)

def build_scratch_lists(world_state: dict, grid: list[list[int]], players: dict, entities: dict) -> dict:
    """Build all lists to sync to Scratch."""
    
    # GRID: flatten world (120,000 elements)
    flat_grid = flatten_grid(grid)
    
    # Users lists (parallel)
    usernames = []
    user_x = []
    user_y = []
    for username, player in players.items():
        usernames.append(username)
        user_x.append(player["x"])
        user_y.append(player["y"])
    
    # Enemies lists (parallel)
    enemy_x = []
    enemy_y = []
    enemy_type = []
    for creature in entities.get("creatures", []):
        # Only include if scouted
        key = f"{creature['x']},{creature['y']}"
        if key in world_state.get("scouted", {}):
            enemy_x.append(creature["x"])
            enemy_y.append(creature["y"])
            enemy_type.append(creature["type"])
    
    return {
        "GRID": flat_grid,
        "USERS:USERNAME": usernames,
        "USERS:X": user_x,
        "USERS:Y": user_y,
        "ENEMIES:X": enemy_x,
        "ENEMIES:Y": enemy_y,
        "ENEMIES:TYPE": enemy_type,
    }

def run_iteration():
    """Run one bot iteration."""
    # Load settings
    with open("config/settings.json", "r") as f:
        settings = json.load(f)
    
    project_id = settings["project_id"]
    session_id = os.environ.get("SCRATCH_SESSION_ID")
    
    if not session_id:
        print("ERROR: SCRATCH_SESSION_ID not set")
        return
    
    # Initialize API
    api = ScratchAPI(session_id, project_id, rate_limit=settings["rate_limit_seconds"])
    
    # Load or generate world
    world_data = load_world()
    if world_data is None:
        print("Generating new world...")
        grid = generate_world()
        world_data = {
            "grid": grid,
            "scouted": {},
            "sectors": {},
            "structures": [],
            "calamities": [],
            "bounties": []
        }
        save_world(grid)
    else:
        grid = world_data["grid"]
    
    # Load player/entity state
    players = load_players()
    entities = load_entities()
    
    # Process world tick
    process_tick(world_data, grid, players, entities)
    
    # Load processed comments
    processed = load_processed()
    
    # Fetch and process new comments
    comments = api.get_comments(limit=40)
    
    # Sort by datetime (oldest first)
    comments.sort(key=lambda c: c.datetime_created if c.datetime_created else "")
    
    handler = CommandHandler(world_data, grid)
    handler.players = players
    handler.entities = entities
    
    for comment in comments:
        if comment.id in processed:
            continue
        
        if not comment.content:
            processed.add(comment.id)
            continue
        
        # Only process top-level comments
        if comment.parent_id is not None:
            processed.add(comment.id)
            continue
        
        username = comment.author_name
        text = comment.content.strip()
        
        if text.startswith("!"):
            print(f"Processing command from {username}: {text}")
            response = handler.handle_command(username, comment.id, text)
            
            if response:
                success = api.reply_to_comment(comment.id, response)
                if not success:
                    print(f"Failed to reply to {comment.id}")
        
        processed.add(comment.id)
    
    # Save all state
    players = handler.players
    entities = handler.entities
    
    save_players(players)
    save_entities(entities)
    save_world(grid)
    save_processed(processed)
    
    # Build and sync Scratch lists
    lists_to_sync = build_scratch_lists(world_data, grid, players, entities)
    
    print(f"Syncing to Scratch: {len(lists_to_sync)} lists")
    success = api.update_lists(lists_to_sync)
    
    if success:
        print("Scratch sync complete")
    else:
        print("Scratch sync failed")

def main():
    """Main loop: run 60 iterations, one per minute."""
    print(f"Bot starting at {datetime.now()}")
    
    for i in range(60):
        print(f"\n--- Iteration {i+1}/60 at {datetime.now()} ---")
        try:
            run_iteration()
        except Exception as e:
            print(f"Error in iteration: {e}")
            import traceback
            traceback.print_exc()
        
        # Wait for next minute (minus processing time)
        if i < 59:
            time.sleep(55)  # ~55 seconds, allowing 5 seconds for processing

if __name__ == "__main__":
    main()
```

---

### `.github/workflows/tick.yml`

```yaml
name: Cave MMO Bot

on:
  schedule:
    - cron: '0 * * * *'  # Every hour
  workflow_dispatch:  # Manual trigger

jobs:
  run-bot:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run bot
        env:
          SCRATCH_SESSION_ID: ${{ secrets.SCRATCH_SESSION_ID }}
        run: |
          python -m src.main
      
      - name: Commit state changes
        run: |
          git config --local user.email "bot@cave-mmo.local"
          git config --local user.name "Cave MMO Bot"
          git add state/
          git diff --staged --quiet || git commit -m "Bot state update $(date -u +%Y-%m-%dT%H:%M:%SZ)"
          git push
```

---

## What you need to do now

1. **Create these Scratch lists** (if not already):
   - `ENEMIES:X`
   - `ENEMIES:Y`
   - `ENEMIES:TYPE`
   - `USERS:X`
   - `USERS:Y`

2. **Add GitHub secret**: `SCRATCH_SESSION_ID` with your bot account's session ID

3. **Create initial state files** (or let bot generate them on first run):
   - `state/players.json` → `{}`
   - `state/entities.json` → `{"creatures": [], "next_id": 1}`
   - `state/processed.json` → `[]`

4. **Test locally** before deploying:
   ```bash
   export SCRATCH_SESSION_ID="your_session_id"
   python -m src.main
   ```

---

This is the complete v1 implementation. Want me to add anything else (trading, crafting stations, sector regeneration logic, calamities)?
