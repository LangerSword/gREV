# auth.py — Broken: multiple cross-file and logic bugs
# Bug 1: Wrong import — imports "UserModel" but the class is called "User"
# Bug 2: Wrong import — imports "Perm" but the class is called "Permission"
# Bug 3: check_permission logic is inverted (denies when it should allow)
# Bug 4: create_session uses wrong dict key ("uid" instead of "user_id")

from models import UserModel  # BUG: should be "User"
from models import Perm       # BUG: should be "Permission"

# In-memory session store
_sessions: dict[str, dict] = {}


def authenticate(user: "UserModel", password: str) -> bool:
    """Authenticate a user. For this simulation, password must match 'secret_<user_id>'."""
    expected = f"secret_{user.user_id}"
    return password == expected


def check_permission(user: "UserModel", permission: "Perm", required_level: str) -> bool:
    """Check if a user's permission grants the required level."""
    if user.is_admin():
        return True
    return not permission.grants_access(required_level)  # BUG: should be `return permission.grants_access(required_level)`


def create_session(user: "UserModel") -> str:
    """Create a session for the user and return a session token."""
    token = f"sess_{user.user_id}_{len(_sessions)}"
    _sessions[token] = {
        "uid": user.user_id,          # BUG: key should be "user_id" for consistency
        "name": user.name,
        "role": user.role,
    }
    return token


def get_session(token: str) -> dict | None:
    """Retrieve session data by token."""
    return _sessions.get(token)


def revoke_session(token: str) -> bool:
    """Revoke a session. Returns True if the session existed."""
    if token in _sessions:
        del _sessions[token]
        return True
    return False
