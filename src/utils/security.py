"""
Security utilities for TrailService
"""
import hashlib
import hmac
import base64
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Note: Actual password hashing is handled by external Authenticator API
# These utilities are for internal security needs

def generate_api_key(length: int = 32) -> str:
    """
    Generate a secure API key
    """
    alphabet = string.ascii_letters + string.digits
    api_key = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # Add timestamp prefix for identification
    timestamp = datetime.now().strftime("%Y%m%d")
    return f"ts_{timestamp}_{api_key}"

def validate_api_key(api_key: str) -> Tuple[bool, str]:
    """
    Validate API key format
    Returns: (is_valid, message)
    """
    if not api_key.startswith("ts_"):
        return False, "Invalid API key format"
    
    parts = api_key.split("_")
    if len(parts) != 3:
        return False, "Invalid API key format"
    
    # Check timestamp (not older than 1 year)
    try:
        key_date = datetime.strptime(parts[1], "%Y%m%d")
        if (datetime.now() - key_date).days > 365:
            return False, "API key expired"
    except ValueError:
        return False, "Invalid timestamp in API key"
    
    return True, "Valid API key"

def hash_password(password: str) -> str:
    """
    Hash password using SHA-256 (for internal use only)
    Note: External Authenticator API handles actual authentication
    """
    salt = secrets.token_hex(16)
    hash_obj = hashlib.sha256()
    hash_obj.update(f"{salt}{password}".encode('utf-8'))
    hashed = hash_obj.hexdigest()
    return f"{salt}${hashed}"

def verify_password(stored_hash: str, password: str) -> bool:
    """
    Verify password against stored hash
    """
    try:
        salt, expected_hash = stored_hash.split('$')
        hash_obj = hashlib.sha256()
        hash_obj.update(f"{salt}{password}".encode('utf-8'))
        return hash_obj.hexdigest() == expected_hash
    except:
        return False

def encrypt_data(data: str, key: str) -> str:
    """
    Simple encryption for sensitive data
    """
    # This is a simple XOR-based encryption for demonstration
    # In production, will use libraries such as cryptography.fernet
    encrypted = []
    for i, char in enumerate(data):
        key_char = key[i % len(key)]
        encrypted_char = chr(ord(char) ^ ord(key_char))
        encrypted.append(encrypted_char)
    
    encrypted_str = ''.join(encrypted)
    return base64.b64encode(encrypted_str.encode()).decode()

def decrypt_data(encrypted_data: str, key: str) -> str:
    """
    Decrypt data
    """
    try:
        decoded = base64.b64decode(encrypted_data).decode()
        decrypted = []
        for i, char in enumerate(decoded):
            key_char = key[i % len(key)]
            decrypted_char = chr(ord(char) ^ ord(key_char))
            decrypted.append(decrypted_char)
        
        return ''.join(decrypted)
    except:
        return ""

def generate_csrf_token() -> str:
    """
    Generate CSRF token
    """
    return secrets.token_urlsafe(32)

def validate_csrf_token(token: str, stored_token: str) -> bool:
    """
    Validate CSRF token
    """
    return hmac.compare_digest(token, stored_token)

def sanitize_sql_input(input_str: str) -> str:
    """
    Basic SQL injection prevention
    """
    # Remove common SQL injection patterns
    dangerous_patterns = [
        "--", "/*", "*/", ";", "'", "\"", "union", "select", "insert",
        "update", "delete", "drop", "create", "alter", "exec", "xp_"
    ]
    
    sanitized = input_str.lower()
    for pattern in dangerous_patterns:
        sanitized = sanitized.replace(pattern, "")
    
    return sanitized

def log_security_event(event_type: str, details: str, user_id: Optional[int] = None):
    """
    Log security-related events
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "details": details,
        "user_id": user_id
    }
    
    logger.warning(f"SECURITY EVENT: {log_entry}")
    
    # In production, you would log to a security monitoring system
    return log_entry