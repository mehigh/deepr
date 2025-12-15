from cryptography.fernet import Fernet
import base64
import hashlib
import os

CODEBASE_SECRET = os.getenv("CODEBASE_SECRET", "default-secret")

def _get_fernet_key(user_id: int) -> bytes:
    """Derives a Fernet key from the codebase secret and user ID."""
    key_material = f"{CODEBASE_SECRET}:{user_id}".encode()
    # Fernet requires a 32-byte URL-safe base64-encoded key
    hasher = hashlib.sha256()
    hasher.update(key_material)
    return base64.urlsafe_b64encode(hasher.digest())

def encrypt_key(api_key: str, user_id: int) -> str:
    key = _get_fernet_key(user_id)
    f = Fernet(key)
    return f.encrypt(api_key.encode()).decode()

def decrypt_key(encrypted_key: str, user_id: int) -> str:
    key = _get_fernet_key(user_id)
    f = Fernet(key)
    return f.decrypt(encrypted_key.encode()).decode()
