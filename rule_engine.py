import re
from typing import List, Tuple, Optional
from .storage import Storage

class RuleEngine:
    def __init__(self, storage: Storage):
        self.storage = storage
        self.rules = storage.read_rules()
    
    def reload(self):
        self.rules = self.storage.read_rules()
    
    def add_rule(self, pattern: str, category: str):
        self.rules.append({"pattern": pattern, "category": category})
        self.storage.write_rules(self.rules)
    
    def delete_rules_by_category(self, category: str):
        self.rules = [r for r in self.rules if r['category'] != category]
        self.storage.write_rules(self.rules)
    
    def match(self, text: str) -> List[Tuple[str, str]]:
        results = []
        for rule in self.rules:
            try:
                match = re.search(rule['pattern'], text, re.IGNORECASE)
                if match:
                    value = match.group(1) if match.groups() else match.group(0)
                    results.append((rule['category'], value.strip()))
            except re.error:
                continue
        return results
