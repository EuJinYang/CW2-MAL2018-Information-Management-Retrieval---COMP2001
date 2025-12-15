from .base import BaseModel
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class User(BaseModel):
    user_id: int = 0
    username: str = ""
    email: str = ""
    role: str = "user"
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    def get_id(self) -> int:
        """Get user ID"""
        return self.user_id
    
    def set_id(self, user_id: int) -> None:
        """Set user ID"""
        self.user_id = user_id
    
    def get_username(self) -> str:
        """Get username"""
        return self.username
    
    def set_username(self, username: str) -> None:
        """Set username"""
        self.username = username
    
    def get_email(self) -> str:
        """Get email"""
        return self.email
    
    def set_email(self, email: str) -> None:
        """Set email"""
        self.email = email
    
    def get_role(self) -> str:
        """Get user role"""
        return self.role
    
    def set_role(self, role: str) -> None:
        """Set user role"""
        valid_roles = ["admin", "user", "moderator"]
        if role in valid_roles:
            self.role = role
        else:
            raise ValueError(f"Role must be one of {valid_roles}")
    
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == "admin"
    
    def update_last_login(self) -> None:
        """Update last login timestamp"""
        self.last_login = datetime.now()
    
    def to_dict(self) -> dict:
        result = {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role
        }
        if self.created_at:
            result["created_at"] = self.created_at.isoformat()
        if self.last_login:
            result["last_login"] = self.last_login.isoformat()
        return result
    
    def from_dict(self, data: dict) -> 'User':
        self.user_id = data.get("user_id") or data.get("UserID") or 0
        self.username = data.get("username") or data.get("Username") or ""
        self.email = data.get("email") or data.get("Email") or ""
        self.role = data.get("role") or data.get("Role") or "user"
        
        if "created_at" in data and data["created_at"]:
            self.created_at = datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
        if "last_login" in data and data["last_login"]:
            self.last_login = datetime.fromisoformat(data["last_login"].replace('Z', '+00:00'))
        return self
    
    def validate(self) -> bool:
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(
            self.username.strip() and 
            self.email.strip() and 
            re.match(email_pattern, self.email)
        )