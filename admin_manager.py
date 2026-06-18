from .storage import Storage

class AdminManager:
    def __init__(self, storage: Storage, initial_admins: list):
        self.storage = storage
        self.admins = storage.read_admins()
        if not self.admins and initial_admins:
            self.admins = initial_admins
            self.storage.write_admins(self.admins)
    
    def is_admin(self, user_id: str) -> bool:
        return user_id in self.admins
    
    def add_admin(self, user_id: str) -> bool:
        if user_id not in self.admins:
            self.admins.append(user_id)
            self.storage.write_admins(self.admins)
            return True
        return False
    
    def remove_admin(self, user_id: str) -> bool:
        if user_id in self.admins:
            self.admins.remove(user_id)
            self.storage.write_admins(self.admins)
            return True
        return False
    
    def get_admins(self) -> list:
        return self.admins.copy()
