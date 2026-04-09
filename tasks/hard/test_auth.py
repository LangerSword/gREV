import pytest
from models import User, Permission
from auth import authenticate, check_permission, create_session, get_session, revoke_session


# ── Fixture ──────────────────────────────────────────────────

@pytest.fixture
def admin_user():
    return User(user_id=1, name="Alice", email="alice@corp.com", role="admin")

@pytest.fixture
def viewer_user():
    return User(user_id=2, name="Bob", email="bob@corp.com", role="viewer")

@pytest.fixture
def write_perm():
    return Permission(resource="documents", level="write")

@pytest.fixture
def read_perm():
    return Permission(resource="reports", level="read")


# ── authenticate tests ───────────────────────────────────────

def test_auth_correct_password(viewer_user):
    assert authenticate(viewer_user, "secret_2") is True

def test_auth_wrong_password(viewer_user):
    assert authenticate(viewer_user, "wrong") is False

def test_auth_admin(admin_user):
    assert authenticate(admin_user, "secret_1") is True


# ── check_permission tests ───────────────────────────────────

def test_admin_always_has_permission(admin_user, write_perm):
    assert check_permission(admin_user, write_perm, "admin") is True

def test_viewer_read_access(viewer_user, read_perm):
    assert check_permission(viewer_user, read_perm, "read") is True

def test_viewer_no_write_access(viewer_user, read_perm):
    assert check_permission(viewer_user, read_perm, "write") is False

def test_write_perm_grants_read(viewer_user, write_perm):
    assert check_permission(viewer_user, write_perm, "read") is True


# ── session management tests ─────────────────────────────────

def test_create_session_returns_token(viewer_user):
    token = create_session(viewer_user)
    assert token is not None
    assert isinstance(token, str)

def test_session_contains_user_id(viewer_user):
    token = create_session(viewer_user)
    session = get_session(token)
    assert session is not None
    assert session["user_id"] == 2

def test_session_contains_role(admin_user):
    token = create_session(admin_user)
    session = get_session(token)
    assert session["role"] == "admin"

def test_revoke_session(viewer_user):
    token = create_session(viewer_user)
    assert revoke_session(token) is True
    assert get_session(token) is None

def test_revoke_nonexistent_session():
    assert revoke_session("fake_token") is False

def test_get_nonexistent_session():
    assert get_session("no_such_token") is None
