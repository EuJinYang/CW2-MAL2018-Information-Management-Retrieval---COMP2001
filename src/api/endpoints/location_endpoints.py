"""
Location management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from typing import List, Optional
import logging

from src.api.auth import get_current_user, get_optional_user
from src.models.location import Country, City, Location
from src.models.user import User
from src.database.connection import get_db_connection

logger = logging.getLogger(__name__)
router = APIRouter()

# Make all GET endpoints public
@router.get("/countries", response_model=List[dict])
async def get_countries(
    name: Optional[str] = Query(None, description="Filter by country name"),
):
    """
    Get all countries with optional filtering - PUBLIC ENDPOINT
    """
    try:
        db = get_db_connection()
        
        query = "SELECT CountryID, CountryName FROM CW2.Country"
        params = []
        
        if name:
            query += " WHERE CountryName LIKE ?"
            params.append(f"%{name}%")
        
        query += " ORDER BY CountryName"
        
        countries = db.execute_query(query, tuple(params) if params else None)
        return countries
        
    except Exception as e:
        logger.error(f"Error getting countries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving countries"
        )

@router.get("/countries/{country_id}/cities", response_model=List[dict])
async def get_cities_by_country(
    country_id: int,
    name: Optional[str] = Query(None, description="Filter by city name"),
):
    """
    Get cities for a specific country - PUBLIC ENDPOINT
    """
    try:
        db = get_db_connection()
        
        # Verify country exists
        country = db.execute_query(
            "SELECT CountryID FROM CW2.Country WHERE CountryID = ?",
            (country_id,)
        )
        
        if not country:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Country with ID {country_id} not found"
            )
        
        query = """
        SELECT CityID, CityName, CountryID 
        FROM CW2.City 
        WHERE CountryID = ?
        """
        params = [country_id]
        
        if name:
            query += " AND CityName LIKE ?"
            params.append(f"%{name}%")
        
        query += " ORDER BY CityName"
        
        cities = db.execute_query(query, tuple(params))
        return cities
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cities for country {country_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving cities"
        )

@router.get("/locations", response_model=List[dict])
async def get_locations(
    city_id: Optional[int] = Query(None, description="Filter by city"),
    country_id: Optional[int] = Query(None, description="Filter by country"),
    name: Optional[str] = Query(None, description="Filter by location name"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Get all locations with filtering - PUBLIC ENDPOINT
    """
    try:
        db = get_db_connection()
        
        query = """
        SELECT 
            l.LocationID, l.LocationName, l.Coordinates,
            l.CityID, l.CountryID,
            c.CityName, co.CountryName
        FROM CW2.Location l
        LEFT JOIN CW2.City c ON l.CityID = c.CityID
        LEFT JOIN CW2.Country co ON l.CountryID = co.CountryID
        WHERE 1=1
        """
        
        params = []
        
        if city_id:
            query += " AND l.CityID = ?"
            params.append(city_id)
        
        if country_id:
            query += " AND l.CountryID = ?"
            params.append(country_id)
        
        if name:
            query += " AND l.LocationName LIKE ?"
            params.append(f"%{name}%")
        
        query += " ORDER BY l.LocationName OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, limit])
        
        locations = db.execute_query(query, tuple(params))
        return locations
        
    except Exception as e:
        logger.error(f"Error getting locations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving locations"
        )

@router.get("/locations/{location_id}", response_model=dict)
async def get_location(
    location_id: int,
):
    """
    Get location by ID - PUBLIC ENDPOINT
    """
    try:
        db = get_db_connection()
        
        query = """
        SELECT 
            l.LocationID, l.LocationName, l.Coordinates,
            l.CityID, l.CountryID,
            c.CityName, co.CountryName
        FROM CW2.Location l
        LEFT JOIN CW2.City c ON l.CityID = c.CityID
        LEFT JOIN CW2.Country co ON l.CountryID = co.CountryID
        WHERE l.LocationID = ?
        """
        
        results = db.execute_query(query, (location_id,))
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Location with ID {location_id} not found"
            )
        
        return results[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting location {location_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving location"
        )

# POST endpoint remains protected (requires auth)
@router.post("/locations", status_code=status.HTTP_201_CREATED)
async def create_location(
    location_data: dict = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new location (admin only)
    """
    import traceback
    
    try:
        logger.info(f"Creating location for user {current_user.user_id}")
        logger.info(f"Location data: {location_data}")
        
        # Check if user is admin
        if current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Validate required fields
        required_fields = ["location_name"]
        for field in required_fields:
            if field not in location_data or not location_data[field]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Validate coordinates if provided
        if "coordinates" in location_data and location_data["coordinates"]:
            coords = location_data["coordinates"]
            # Simple validation - should be "lat,lon"
            try:
                lat, lon = map(float, coords.split(","))
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    raise ValueError("Invalid coordinate range")
            except Exception as e:
                logger.error(f"Invalid coordinates format: {coords}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid coordinates format. Use 'latitude,longitude' with valid numbers"
                )
        
        # Validate city_id and country_id exist if provided
        db = get_db_connection()
        
        if "city_id" in location_data and location_data["city_id"]:
            city = db.execute_query(
                "SELECT CityID FROM CW2.City WHERE CityID = ?",
                (location_data["city_id"],)
            )
            if not city:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"City with ID {location_data['city_id']} not found"
                )
        
        if "country_id" in location_data and location_data["country_id"]:
            country = db.execute_query(
                "SELECT CountryID FROM CW2.Country WHERE CountryID = ?",
                (location_data["country_id"],)
            )
            if not country:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Country with ID {location_data['country_id']} not found"
                )
        
        # Insert into database
        query = """
        INSERT INTO CW2.Location (LocationName, CityID, CountryID, Coordinates)
        OUTPUT INSERTED.LocationID
        VALUES (?, ?, ?, ?)
        """
        
        params = (
            location_data["location_name"],
            location_data.get("city_id"),
            location_data.get("country_id"),
            location_data.get("coordinates")
        )
        
        try:
            result = db.execute_update(query, params)
            location_id = result if result else 0
            
            logger.info(f"Location created with ID: {location_id}")
            
            # Log the action
            db.log_trail_action(
                trail_id=None,
                user_id=current_user.user_id,
                action="CREATE_LOCATION",
                details=f"Created location: {location_data['location_name']} (ID: {location_id})"
            )
            
            # Get the created location
            created_location = db.execute_query(
                """
                SELECT 
                    l.LocationID, l.LocationName, l.Coordinates,
                    l.CityID, l.CountryID,
                    c.CityName, co.CountryName
                FROM CW2.Location l
                LEFT JOIN CW2.City c ON l.CityID = c.CityID
                LEFT JOIN CW2.Country co ON l.CountryID = co.CountryID
                WHERE l.LocationID = ?
                """,
                (location_id,)
            )
            
            response_data = {
                "location_id": location_id,
                "message": "Location created successfully",
                "location": created_location[0] if created_location else None
            }
            
            return response_data
            
        except Exception as db_error:
            logger.error(f"Database error creating location: {db_error}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Check for duplicate location
            duplicate_check = db.execute_query(
                "SELECT LocationID FROM CW2.Location WHERE LocationName = ?",
                (location_data["location_name"],)
            )
            
            if duplicate_check:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Location with name '{location_data['location_name']}' already exists"
                )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating location in database"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating location: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating location"
        )