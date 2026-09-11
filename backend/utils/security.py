import hashlib

def hash_token(token):
    """Securely hash a token using SHA-256"""
    if not token:
        return None
    return hashlib.sha256(token.encode()).hexdigest()
