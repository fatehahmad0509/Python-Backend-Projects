"""Password hashing utilities using bcrypt."""
import bcrypt

_BCRYPT_ROUNDS = 12


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt. Returns a utf-8 string."""
    salt = bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        # Never leak details about malformed hashes to the caller.
        return False
