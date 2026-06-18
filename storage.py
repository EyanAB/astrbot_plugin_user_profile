import json
from pathlib import Path
from typing import Dict, Any, Optional
import threading

class Storage:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _get_profile_path(self, user_id: str, group_id: Optional[str]) -> Path:
        if group_id is None:
            filename = f"private_{user_id}.json"
        else:
            filename = f"{user_id}_{group_id}.json"
        return self.data_dir / "profiles" / filename

    def read_profile(self, user_id: str, group_id: Optional[str]) -> Dict:
        path = self._get_profile_path(user_id, group_id)
        with self._lock:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {
                    "user_id": user_id,
                    "group_id": group_id,
                    "last_update": 0,
                    "categories": {}
                }

    def write_profile(self, user_id: str, group_id: Optional[str], data: Dict):
        path = self._get_profile_path(user_id, group_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            tmp = path.with_suffix('.tmp')
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            tmp.replace(path)

    def read_global_categories(self) -> list:
        path = self.data_dir / "global_categories.json"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def write_global_categories(self, categories: list):
        path = self.data_dir / "global_categories.json"
        with self._lock:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(categories, f, ensure_ascii=False, indent=2)

    def read_rules(self) -> list:
        path = self.data_dir / "rules.json"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def write_rules(self, rules: list):
        path = self.data_dir / "rules.json"
        with self._lock:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(rules, f, ensure_ascii=False, indent=2)

    def read_admins(self) -> list:
        path = self.data_dir / "admins.json"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def write_admins(self, admins: list):
        path = self.data_dir / "admins.json"
        with self._lock:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(admins, f, ensure_ascii=False, indent=2)