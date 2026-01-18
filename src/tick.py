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
