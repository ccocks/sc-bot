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
        self.session = sa.login("scratchcord_bot", session_id)
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
