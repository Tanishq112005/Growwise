"""
Authentication and password security utilities using bcrypt.
"""

from typing import Optional
import bcrypt


def hash_password(password: str) -> str:
    """
    Securely hashes a plain-text password using bcrypt.

    Args:
        password: Plain-text password string.

    Returns:
        UTF-8 encoded string containing the bcrypt hash.
    """
    if not password:
        raise ValueError("Password cannot be empty.")
    salt = bcrypt.gensalt(rounds=12)
    hashed_bytes = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password: str, hashed_password: Optional[str]) -> bool:
    """
    Verifies a plain-text password against a bcrypt hash.

    Args:
        plain_password: Plain-text password provided by the user.
        hashed_password: Stored bcrypt hash string.

    Returns:
        True if password matches, False otherwise.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False
