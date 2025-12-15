from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

@dataclass
class BaseModel(ABC):
    """Base class for all data models"""
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        pass
    
    @abstractmethod
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Populate model from dictionary"""
        pass
    
    def validate(self) -> bool:
        """Validate model data"""
        return True