import time
from typing import Optional, Dict, List, Tuple
from .storage import Storage

class ProfileManager:
    def __init__(self, storage: Storage, config: dict):
        self.storage = storage
        self.config = config
        self._last_inject = {}
    
    def _get_key(self, user_id: str, group_id: Optional[str]):
        return (user_id, group_id)
    
    def get_profile(self, user_id: str, group_id: Optional[str]) -> dict:
        return self.storage.read_profile(user_id, group_id)
    
    def save_profile(self, user_id: str, group_id: Optional[str], profile: dict):
        profile['last_update'] = int(time.time())
        self.storage.write_profile(user_id, group_id, profile)
    
    def set_tag(self, user_id: str, group_id: Optional[str], category: str, value: str, operator_id: Optional[str] = None) -> bool:
        max_len = self.config.get('value_max_len', 10)
        if len(value) > max_len:
            return False
        
        profile = self.get_profile(user_id, group_id)
        categories = profile.setdefault('categories', {})
        cat_data = categories.get(category)
        if cat_data is None:
            categories[category] = {
                "primary": value,
                "secondary": {},
                "backup": []
            }
        else:
            old_primary = cat_data.get('primary')
            if old_primary == value:
                pass
            else:
                if old_primary:
                    sec = cat_data.setdefault('secondary', {})
                    sec[old_primary] = sec.get(old_primary, 0) + 1
                cat_data['primary'] = value
        self.save_profile(user_id, group_id, profile)
        return True
    
    def add_secondary(self, user_id: str, group_id: Optional[str], category: str, value: str) -> bool:
        if not category or not value:
            return False
        max_len = self.config.get('value_max_len', 10)
        if len(value) > max_len:
            return False
        
        profile = self.get_profile(user_id, group_id)
        categories = profile.setdefault('categories', {})
        cat_data = categories.get(category)
        if cat_data is None:
            categories[category] = {
                "primary": value,
                "secondary": {},
                "backup": []
            }
            self.save_profile(user_id, group_id, profile)
            return True
        
        sec = cat_data.setdefault('secondary', {})
        sec[value] = sec.get(value, 0) + 1
        primary = cat_data.get('primary')
        if primary is None:
            cat_data['primary'] = value
            del sec[value]
            self.save_profile(user_id, group_id, profile)
            return True
        
        primary_freq = sec.get(primary, 0)
        base_freq = primary_freq if primary_freq > 0 else 1
        threshold = base_freq * self.config.get('freq_upgrade_ratio', 1.5)
        
        if sec.get(value, 0) > threshold:
            if primary_freq > 0:
                sec[primary] = primary_freq
            else:
                sec[primary] = 1
            cat_data['primary'] = value
            if value in sec:
                del sec[value]
            self.save_profile(user_id, group_id, profile)
            return True
        else:
            self.save_profile(user_id, group_id, profile)
            return True
    
    def get_primary(self, user_id: str, group_id: Optional[str], category: str) -> Optional[str]:
        profile = self.get_profile(user_id, group_id)
        return profile.get('categories', {}).get(category, {}).get('primary')
    
    def get_compact_profile(self, user_id: str, group_id: Optional[str]) -> str:
        profile = self.get_profile(user_id, group_id)
        categories = profile.get('categories', {})
        parts = []
        for cat, data in categories.items():
            primary = data.get('primary')
            if primary:
                parts.append(f"{cat}:{primary}")
        return "；".join(parts) if parts else ""
    
    def delete_category(self, user_id: str, group_id: Optional[str], category: str):
        profile = self.get_profile(user_id, group_id)
        if category in profile.get('categories', {}):
            del profile['categories'][category]
            self.save_profile(user_id, group_id, profile)
    
    def should_inject(self, user_id: str, group_id: Optional[str]) -> bool:
        key = self._get_key(user_id, group_id)
        last = self._last_inject.get(key, 0)
        cooldown = self.config.get('inject_cooldown', 600)
        return (time.time() - last) > cooldown
    
    def mark_injected(self, user_id: str, group_id: Optional[str]):
        key = self._get_key(user_id, group_id)
        self._last_inject[key] = time.time()
