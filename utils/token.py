import secrets

def generate_secure_token(length: int = 32) -> str:
    """
    Generates a cryptographically secure, URL-safe text string.
    """
    return secrets.token_urlsafe(length)
