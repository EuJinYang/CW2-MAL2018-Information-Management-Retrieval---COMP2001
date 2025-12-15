from .base import BaseModel
from dataclasses import dataclass
from typing import Optional

@dataclass
class Feature(BaseModel):
    feature_id: int = 0
    feature_name: str = ""
    description: Optional[str] = None
    icon_url: Optional[str] = None
    
    def get_id(self) -> int:
        return self.feature_id
    
    def get_name(self) -> str:
        return self.feature_name
    
    def set_name(self, name: str) -> None:
        self.feature_name = name
    
    def get_description(self) -> Optional[str]:
        return self.description
    
    def set_description(self, description: str) -> None:
        self.description = description
    
    def get_icon_url(self) -> Optional[str]:
        return self.icon_url
    
    def set_icon_url(self, url: str) -> None:
        self.icon_url = url
    
    def to_dict(self) -> dict:
        result = {
            "feature_id": self.feature_id,
            "feature_name": self.feature_name
        }
        if self.description:
            result["description"] = self.description
        if self.icon_url:
            result["icon_url"] = self.icon_url
        return result
    
    def from_dict(self, data: dict) -> 'Feature':
        self.feature_id = data.get("feature_id", 0)
        self.feature_name = data.get("feature_name", "")
        self.description = data.get("description")
        self.icon_url = data.get("icon_url")
        return self
    
    def validate(self) -> bool:
        return bool(self.feature_name.strip())