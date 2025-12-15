"""
Database connection and query management for SQL Server
"""
import pyodbc
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """SQL Server database connection manager"""
    
    def __init__(self):
        self.connection_string = None
        self.connection = None
        self.cursor = None
        self.setup_connection()
    
    def setup_connection(self):
        """Setup database connection string"""
        # Using specified SQL Server
        server = "localhost"
        database = "TrailDB"
        username = "SA"
        password = "C0mp2001!"
        
        self.connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"TrustServerCertificate=yes;"
        )
    
    def connect(self):
        """Establish database connection"""
        try:
            if not self.connection:
                self.connection = pyodbc.connect(self.connection_string)
                self.cursor = self.connection.cursor()
                logger.info("Database connection established")
        except pyodbc.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def disconnect(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None
            logger.info("Database connection closed")
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database cursor"""
        self.connect()
        try:
            yield self.cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            raise e
        finally:
            self.disconnect()
    
    def test_connection(self):
        """Test database connection"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                return result[0] == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a SELECT query and return results"""
        try:
            with self.get_cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                
                # Get column names
                columns = [column[0] for column in cursor.description]
                
                # Fetch all rows and convert to dict
                results = []
                for row in cursor.fetchall():
                    row_dict = {}
                    for i, col in enumerate(columns):
                        row_dict[col] = row[i]
                    results.append(row_dict)
                
                return results
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            raise
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows"""
        try:
            with self.get_cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
            
                # Get the number of affected rows
                affected_rows = cursor.rowcount

                # For INSERT, get the last inserted ID
                if query.strip().upper().startswith("INSERT"):
                    cursor.execute("SELECT SCOPE_IDENTITY()")
                    last_id = cursor.fetchone()[0]
                    return last_id if last_id else affected_rows
            
                return affected_rows
        except Exception as e:
            logger.error(f"Update execution error: {e}")
        raise
    
    # ========== USER QUERIES ==========
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        query = """
        SELECT UserID, Username, Email, Role, CreatedAt, LastLogin
        FROM CW2.[User]
        WHERE UserID = ?
        """
        results = self.execute_query(query, (user_id,))
        return results[0] if results else None
    
    def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        query = """
        SELECT UserID, Username, Email, Role, CreatedAt, LastLogin
        FROM CW2.[User]
        WHERE Email = ?
        """
        results = self.execute_query(query, (email,))
        return results[0] if results else None
    
    def create_user(self, user_data: Dict) -> int:
        """Create a new user"""
        query = """
        INSERT INTO CW2.[User] (Username, Email, Role, CreatedAt)
        VALUES (?, ?, ?, ?)
        """
        params = (
            user_data.get("username"),
            user_data.get("email"),
            user_data.get("role", "user"),
            self.get_current_timestamp()
        )
        return self.execute_update(query, params)
    
    def update_user_last_login(self, user_id: int) -> bool:
        """Update user's last login timestamp"""
        query = """
        UPDATE CW2.[User]
        SET LastLogin = ?
        WHERE UserID = ?
        """
        try:
            self.execute_update(query, (self.get_current_timestamp(), user_id))
            return True
        except:
            return False
    
    # ========== TRAIL QUERIES ==========
    
    def get_trails(self, filters: Dict = None, limit: int = 20, offset: int = 0) -> List[Dict]:
        """Get trails with optional filters"""
        base_query = """
        SELECT t.TrailID, t.TrailName, t.LocationID, t.Difficulty, t.Length,
            t.ElevationGain, t.EstTimeMin, t.EstTimeMax, t.RouteType,
            t.Description, t.UserID, t.IsPublic, t.CreatedAt, t.UpdatedAt,
            u.Username, l.LocationName
        FROM CW2.Trail t
        LEFT JOIN CW2.[User] u ON t.UserID = u.UserID
        LEFT JOIN CW2.Location l ON t.LocationID = l.LocationID
        WHERE 1=1
        """
    
        params = []
    
        # Apply filters
        if filters:
            current_user_id = filters.get("current_user_id")
        
            # Authorization logic
            if current_user_id:
                # Authenticated users: show public trails OR their own private trails
                base_query += " AND (t.IsPublic = 1 OR (t.IsPublic = 0 AND t.UserID = ?))"
                params.append(current_user_id)
            else:
                # Public users: only show public trails
                base_query += " AND t.IsPublic = 1"
                params.append(True)
        
            if filters.get("difficulty"):
                base_query += " AND t.Difficulty = ?"
                params.append(filters["difficulty"])
        
            if filters.get("min_length"):
                base_query += " AND t.Length >= ?"
                params.append(filters["min_length"])
        
            if filters.get("max_length"):
                base_query += " AND t.Length <= ?"
                params.append(filters["max_length"])
        
            if filters.get("location_id"):
                base_query += " AND t.LocationID = ?"
                params.append(filters["location_id"])
    
        else:
            # No filters provided, default to public trails only
            base_query += " AND t.IsPublic = 1"
            params.append(True)
    
        # Add ordering and pagination
        base_query += " ORDER BY t.CreatedAt DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, limit])
    
        return self.execute_query(base_query, tuple(params))

    def count_trails(self, filters: Dict = None) -> int:
        """Count trails with optional filters"""
        base_query = "SELECT COUNT(*) FROM CW2.Trail t WHERE 1=1"
        params = []
    
        if filters:
            current_user_id = filters.get("current_user_id")
        
            # Authorization logic
            if current_user_id:
                # Authenticated users: show public trails OR their own private trails
                base_query += " AND (t.IsPublic = 1 OR (t.IsPublic = 0 AND t.UserID = ?))"
                params.append(current_user_id)
            else:
                # Public users: only show public trails
                base_query += " AND t.IsPublic = ?"
                params.append(True)
        
            if filters.get("difficulty"):
                base_query += " AND t.Difficulty = ?"
                params.append(filters["difficulty"])
        
            if filters.get("min_length"):
                base_query += " AND t.Length >= ?"
                params.append(filters["min_length"])
        
            if filters.get("max_length"):
                base_query += " AND t.Length <= ?"
                params.append(filters["max_length"])
        
            if filters.get("location_id"):
                base_query += " AND t.LocationID = ?"
                params.append(filters["location_id"])
    
        else:
            # No filters provided, default to public trails only
            base_query += " AND t.IsPublic = ?"
            params.append(True)
    
        results = self.execute_query(base_query, tuple(params))
        return results[0][list(results[0].keys())[0]] if results else 0
    
    def get_trail_by_id(self, trail_id: int) -> Optional[Dict]:
        """Get trail by ID"""
        query = """
        SELECT 
            t.TrailID, t.TrailName, t.LocationID, t.Difficulty, t.Length,
            t.ElevationGain, t.EstTimeMin, t.EstTimeMax, t.RouteType,
            t.Description, t.UserID, t.IsPublic, t.CreatedAt, t.UpdatedAt,
            u.Username, l.LocationName
        FROM CW2.Trail t
        LEFT JOIN CW2.[User] u ON t.UserID = u.UserID
        LEFT JOIN CW2.Location l ON t.LocationID = l.LocationID
        WHERE t.TrailID = ?
        """
        results = self.execute_query(query, (trail_id,))
    
        if results:
            # Convert SQL Server BIT to Python boolean
            trail_data = results[0]
            if 'IsPublic' in trail_data:
                # Handle BIT field (0/1 or True/False)
                is_public = trail_data['IsPublic']
                if isinstance(is_public, (int, float)):
                    trail_data['IsPublic'] = bool(is_public)
                elif isinstance(is_public, bool):
                    trail_data['IsPublic'] = is_public
                else:
                    # Try to convert string
                    trail_data['IsPublic'] = str(is_public).lower() in ('true', '1', 't', 'yes')
            return trail_data
    
        return None
    
    def create_trail(self, trail_data: Dict) -> int:
        """Create a new trail"""
        try:
            query = """
            INSERT INTO CW2.Trail (
                TrailName, LocationID, Difficulty, Length, ElevationGain,
                EstTimeMin, EstTimeMax, RouteType, Description, UserID,
                IsPublic, CreatedAt, UpdatedAt
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            SELECT SCOPE_IDENTITY() as trail_id;
            """
        
            # Handle timestamps
            created_at = trail_data.get("created_at")
            updated_at = trail_data.get("updated_at")
        
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            elif created_at is None:
                created_at = self.get_current_timestamp()
        
            if isinstance(updated_at, str):
                updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            elif updated_at is None:
                updated_at = self.get_current_timestamp()
        
            params = (
                trail_data.get("trail_name"),
                trail_data.get("location_id"),
                trail_data.get("difficulty"),
                trail_data.get("length"),
                trail_data.get("elevation_gain"),
                trail_data.get("est_time_min"),
                trail_data.get("est_time_max"),
                trail_data.get("route_type"),
                trail_data.get("description"),
                trail_data.get("user_id"),
                trail_data.get("is_public", True),
                created_at,
                updated_at
            )
            return self.execute_update(query, params)
        
        except Exception as e:
            logger.error(f"Error in create_trail: {e}")
            raise
    
    def update_trail(self, trail_id: int, trail_data: Dict) -> bool:
        """Update an existing trail"""
        # Build dynamic UPDATE query
        set_clauses = []
        params = []
        
        for field, value in trail_data.items():
            if field != "trail_id" and value is not None:
                set_clauses.append(f"{self._map_field_name(field)} = ?")
                params.append(value)
        
        if not set_clauses:
            return False
        
        query = f"UPDATE CW2.Trail SET {', '.join(set_clauses)} WHERE TrailID = ?"
        params.append(trail_id)
        
        try:
            self.execute_update(query, tuple(params))
            return True
        except:
            return False
    
    def delete_trail(self, trail_id: int) -> bool:
        """Delete a trail"""
        query = "DELETE FROM CW2.Trail WHERE TrailID = ?"
        try:
            self.execute_update(query, (trail_id,))
            return True
        except:
            return False
    
    # ========== TRAIL POINTS QUERIES ==========
    
    def get_trail_points(self, trail_id: int) -> List[Dict]:
        """Get all points for a trail"""
        query = """
        SELECT PointID, TrailID, PointOrder, Latitude, Longitude,
               Description, Elevation, CreatedAt
        FROM CW2.Trail_Point
        WHERE TrailID = ?
        ORDER BY PointOrder
        """
        return self.execute_query(query, (trail_id,))
    
    def create_trail_point(self, point_data: Dict) -> int:
        """Create a new trail point"""
        query = """
        INSERT INTO CW2.Trail_Point (
            TrailID, PointOrder, Latitude, Longitude,
            Description, Elevation, CreatedAt
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        # Handle timestamp
        created_at = point_data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        elif created_at is None:
            created_at = self.get_current_timestamp()
        
        params = (
            point_data.get("trail_id"),
            point_data.get("point_order"),
            point_data.get("latitude"),
            point_data.get("longitude"),
            point_data.get("description"),
            point_data.get("elevation"),
            created_at
        )
        return self.execute_update(query, params)
    
    # ========== FEATURE QUERIES ==========
    
    def get_trail_features(self, trail_id: int) -> List[Dict]:
        """Get all features for a trail"""
        query = """
        SELECT f.FeatureID, f.FeatureName, f.Description, f.IconURL
        FROM CW2.Feature f
        INNER JOIN CW2.Trail_Feature tf ON f.FeatureID = tf.FeatureID
        WHERE tf.TrailID = ?
        """
        return self.execute_query(query, (trail_id,))
    
    def add_trail_feature(self, trail_id: int, feature_id: int, user_id: int) -> bool:
        """Add a feature to a trail"""
        query = """
        INSERT INTO CW2.Trail_Feature (TrailID, FeatureID, AddedBy, AddedAt)
        VALUES (?, ?, ?, ?)
        """
        try:
            self.execute_update(query, (trail_id, feature_id, user_id, self.get_current_timestamp()))
            return True
        except:
            return False
    
    # ========== LOCATION QUERIES ==========
    
    def get_location_by_id(self, location_id: int) -> Optional[Dict]:
        """Get location by ID"""
        query = """
        SELECT l.*, c.CityName, co.CountryName
        FROM CW2.Location l
        LEFT JOIN CW2.City c ON l.CityID = c.CityID
        LEFT JOIN CW2.Country co ON l.CountryID = co.CountryID
        WHERE l.LocationID = ?
        """
        results = self.execute_query(query, (location_id,))
        return results[0] if results else None
    
    # ========== REVIEW QUERIES ==========
    
    def get_trail_review_summary(self, trail_id: int) -> Dict:
        """Get review summary for a trail"""
        query = """
        SELECT 
            COUNT(*) as total_reviews,
            AVG(CAST(Rating as FLOAT)) as average_rating,
            SUM(CASE WHEN Rating = 5 THEN 1 ELSE 0 END) as five_star,
            SUM(CASE WHEN Rating = 4 THEN 1 ELSE 0 END) as four_star,
            SUM(CASE WHEN Rating = 3 THEN 1 ELSE 0 END) as three_star,
            SUM(CASE WHEN Rating = 2 THEN 1 ELSE 0 END) as two_star,
            SUM(CASE WHEN Rating = 1 THEN 1 ELSE 0 END) as one_star
        FROM CW2.Review
        WHERE TrailID = ?
        """
        results = self.execute_query(query, (trail_id,))
        return results[0] if results else {}
    
    # ========== AUDIT LOG QUERIES ==========
    
    def log_trail_action(self, trail_id: int, user_id: int, action: str, details: str) -> int:
        """Log a trail action to audit log"""
        query = """
        INSERT INTO CW2.Trail_Log (TrailID, UserID, Action, ActionDate, Details)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (
            trail_id,
            user_id,
            action,
            self.get_current_timestamp(),
            details[:500]  # Truncate to 500 chars
        )
        return self.execute_update(query, params)
    
    # ========== TRANSACTION MANAGEMENT ==========
    
    def begin_transaction(self):
        """Begin a database transaction"""
        self.connect()
        self.connection.autocommit = False
    
    def commit_transaction(self):
        """Commit the current transaction"""
        if self.connection:
            self.connection.commit()
            self.connection.autocommit = True
            self.disconnect()
    
    def rollback_transaction(self):
        """Rollback the current transaction"""
        if self.connection:
            self.connection.rollback()
            self.connection.autocommit = True
            self.disconnect()
    
    # ========== UTILITY METHODS ==========
    
    def get_current_timestamp(self):
        """Get current timestamp for database operations"""
        return datetime.now()
    
    def _map_field_name(self, field_name: str) -> str:
        """Map Python field names to database column names"""
        mapping = {
            "trail_id": "TrailID",
            "trail_name": "TrailName",
            "location_id": "LocationID",
            "difficulty": "Difficulty",
            "length": "Length",
            "elevation_gain": "ElevationGain",
            "est_time_min": "EstTimeMin",
            "est_time_max": "EstTimeMax",
            "route_type": "RouteType",
            "description": "Description",
            "user_id": "UserID",
            "is_public": "IsPublic",
            "created_at": "CreatedAt",
            "updated_at": "UpdatedAt"
        }
        return mapping.get(field_name, field_name)

# Singleton database connection instance
_db_connection = None

def get_db_connection() -> DatabaseConnection:
    """Get singleton database connection instance"""
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection