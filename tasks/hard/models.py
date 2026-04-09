# models.py — This file is correct. Do NOT edit.

class User:
    """Represents an application user."""

    def __init__(self, user_id: int, name: str, email: str, role: str = "viewer"):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.role = role

    def is_admin(self) -> bool:
        return self.role == "admin"

    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
        }


class Permission:
    """Represents a permission grant."""

    def __init__(self, resource: str, level: str = "read"):
        self.resource = resource
        self.level = level  # "read", "write", "admin"

    LEVEL_HIERARCHY = {"read": 1, "write": 2, "admin": 3}

    def grants_access(self, required_level: str) -> bool:
        own = self.LEVEL_HIERARCHY.get(self.level, 0)
        req = self.LEVEL_HIERARCHY.get(required_level, 0)
        return own >= req
