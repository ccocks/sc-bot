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
