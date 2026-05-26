from dataclasses import dataclass
import time
import secrets
import hashlib

def login(username: str, password: str) -> bool:
    if not username or not password:
        return False
    return username == "demo" and password == "password"

'''

These are lines to intentionally modify the auth-related path.

This is so the PR risk scorer will flag it.

'''

@dataclass
class User:
    username: str
    password_hash: str
    is_admin: bool = False
    failed_login_attempts: int = 0
    locked_until: float = 0.0

USERS: dict[str, User] = {}

def delete_user(username: str) -> bool:
    if username not in USERS:
        return False

    del USERS[username]
    return True

def reset_failed_logins(user: User) -> None:
    user.failed_login_attempts = 0
    user.locked_until = 0.0

def record_failed_login(user: User) -> None:
    user.failed_login_attempts += 1

    if user.failed_login_attempts >= 3:
        user.locked_until = time.time() + 60

def is_locked(user: User) -> bool:
    return time.time() < user.locked_until

def list_users() -> list[str]:
    return sorted(USERS.keys())

def hash_password(password: str, salt: str) -> str:
    data = f"{salt}:{password}".encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def create_user(username: str, password: str, is_admin: bool = False) -> User:
    if not username:
        raise ValueError("username is required")

    if len(password) < 8:
        raise ValueError("password must be at least 8 characters")

    salt = secrets.token_hex(8)
    password_hash = f"{salt}${hash_password(password, salt)}"

    user = User(
        username=username,
        password_hash=password_hash,
        is_admin=is_admin,
    )

    USERS[username] = user
    return user


def verify_password(stored_password_hash: str, password: str) -> bool:
    try:
        salt, expected_hash = stored_password_hash.split("$", 1)
    except ValueError:
        return False

    actual_hash = hash_password(password, salt)
    return secrets.compare_digest(actual_hash, expected_hash)

def require_admin(username: str) -> bool:
    user = USERS.get(username)

    if user is None:
        return False

    return user.is_admin


'''



Intentionally adding many lines



PR risk scorer should say there is a moderate change size



'''