from .base import BaseModel
from dataclasses import dataclass
from typing import Optional

@dataclass
class Country(BaseModel):
    country_id: int = 0
    country_name: str = ""
    
    def to_dict(self) -> dict:
        return {
            "country_id": self.country_id,
            "country_name": self.country_name
        }
    
    def from_dict(self, data: dict) -> None:
        self.country_id = data.get("country_id", 0)
        self.country_name = data.get("country_name", "")
    
    def validate(self) -> bool:
        return bool(self.country_name.strip())

@dataclass
class City(BaseModel):
    city_id: int = 0
    city_name: str = ""
    country_id: int = 0
    country: Optional[Country] = None
    
    def to_dict(self) -> dict:
        result = {
            "city_id": self.city_id,
            "city_name": self.city_name,
            "country_id": self.country_id
        }
        if self.country:
            result["country"] = self.country.to_dict()
        return result
    
    def from_dict(self, data: dict) -> None:
        self.city_id = data.get("city_id", 0)
        self.city_name = data.get("city_name", "")
        self.country_id = data.get("country_id", 0)
        if "country" in data:
            self.country = Country().from_dict(data["country"])
    
    def validate(self) -> bool:
        return bool(self.city_name.strip() and self.country_id > 0)

@dataclass
class Location(BaseModel):
    location_id: int = 0
    location_name: str = ""
    city_id: Optional[int] = None
    country_id: Optional[int] = None
    coordinates: Optional[str] = None
    city: Optional[City] = None
    country: Optional[Country] = None
    
    def get_city(self) -> Optional[City]:
        """Get city object"""
        return self.city
    
    def set_city(self, city: City) -> None:
        """Set city object"""
        self.city = city
        self.city_id = city.city_id if city else None
    
    def get_country(self) -> Optional[Country]:
        """Get country object"""
        return self.country
    
    def set_country(self, country: Country) -> None:
        """Set country object"""
        self.country = country
        self.country_id = country.country_id if country else None
    
    def get_coordinates(self) -> tuple[float, float]:
        """Parse coordinates string to lat/long tuple"""
        if not self.coordinates:
            return (0.0, 0.0)
        try:
            lat, lon = map(float, self.coordinates.split(','))
            return (lat, lon)
        except:
            return (0.0, 0.0)
    
    def set_coordinates(self, lat: float, lon: float) -> None:
        """Set coordinates from lat/long"""
        self.coordinates = f"{lat},{lon}"
    
    def to_dict(self) -> dict:
        result = {
            "location_id": self.location_id,
            "location_name": self.location_name,
            "coordinates": self.coordinates
        }
        if self.city_id:
            result["city_id"] = self.city_id
        if self.country_id:
            result["country_id"] = self.country_id
        if self.city:
            result["city"] = self.city.to_dict()
        if self.country:
            result["country"] = self.country.to_dict()
        return result
    
    def from_dict(self, data: dict) -> 'Location':
        self.location_id = data.get("location_id", 0)
        self.location_name = data.get("location_name", "")
        self.coordinates = data.get("coordinates")
        self.city_id = data.get("city_id")
        self.country_id = data.get("country_id")
        if "city" in data:
            self.city = City().from_dict(data["city"])
        if "country" in data:
            self.country = Country().from_dict(data["country"])
        return self
    
    def validate(self) -> bool:
        return bool(self.location_name.strip())