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
