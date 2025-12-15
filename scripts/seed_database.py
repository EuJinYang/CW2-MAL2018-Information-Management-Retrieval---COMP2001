"""
Seed database with sample data for TrailService (CW2 Schema)
This script populates the CW2 schema with test data matching the SQL schema.
"""
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.database.connection import get_db_connection

def seed_database():
    """Seed the CW2 schema with sample data"""
    print("=" * 60)
    print("TRAILSERVICE DATABASE SEEDING")
    print("=" * 60)
    
    db = get_db_connection()
    
    try:
        # Test connection first
        print("Testing database connection...")
        if not db.test_connection():
            print("Database connection failed!")
            return False
        print("Database connection successful")
        
        # Clear existing data in reverse dependency order
        print("\nClearing existing data...")
        clear_tables = [
            "Trail_Log", "User_Activity", "Review", "Photo", "Weather",
            "Trail_Feature", "Trail_Point", "Trail", 
            "Feature", "Location", "City", "Country", "[User]"
        ]
        
        for table in clear_tables:
            try:
                db.execute_update(f"DELETE FROM CW2.{table}")
                print(f"Cleared CW2.{table}")
            except Exception as e:
                print(f"Could not clear {table}: {e}")
        
        # Reset identity columns
        reset_identity_tables = [
            "Trail_Log", "User_Activity", "Review", "Photo", "Weather",
            "Trail_Feature", "Trail_Point", "Trail", 
            "Feature", "Location", "City", "Country", "[User]"
        ]
        
        for table in reset_identity_tables:
            try:
                db.execute_update(f"DBCC CHECKIDENT ('CW2.{table}', RESEED, 0)")
            except:
                pass  # Some tables might not have identity columns
        
        print("\nSeeding new data...")
        
        # 1. Insert Countries
        print("Inserting countries...")
        countries = [
            ("United Kingdom",),
            ("United States",),
            ("Australia",)
        ]
        for country in countries:
            db.execute_update(
                "INSERT INTO CW2.Country (CountryName) VALUES (?)",
                country
            )
        
        # 2. Insert Cities
        print("Inserting cities...")
        cities = [
            ("Plymouth", 1),  # UK
            ("London", 1),    # UK
            ("New York", 2),  # US
            ("Sydney", 3)     # Australia
        ]
        for city in cities:
            db.execute_update(
                "INSERT INTO CW2.City (CityName, CountryID) VALUES (?, ?)",
                city
            )
        
        # 3. Insert Locations
        print("Inserting locations...")
        locations = [
            ("Plymbridge Woods", 1, 1, "50.3964,-4.0916"),
            ("Central Park", 3, 2, "40.7851,-73.9683"),
            ("Dartmoor National Park", 1, 1, "50.5700,-3.9200")
        ]
        for location in locations:
            db.execute_update(
                "INSERT INTO CW2.Location (LocationName, CityID, CountryID, Coordinates) VALUES (?, ?, ?, ?)",
                location
            )
        
        # 4. Insert Users (Matching external Authenticator API)
        print("Inserting users...")
        users = [
            ("Ada Lovelace", "grace@plymouth.ac.uk", "admin"),
            ("Tim Berners-Lee", "tim@plymouth.ac.uk", "admin"),
            ("Ada Lovelace", "ada@plymouth.ac.uk", "user"),
            ("William Frost", "frost@tsc.com", "user")
        ]
        for user in users:
            db.execute_update(
                "INSERT INTO CW2.[User] (Username, Email, Role, CreatedAt) VALUES (?, ?, ?, ?)",
                (*user, datetime.now())
            )
        
        # 5. Insert Features
        print("Inserting features...")
        features = [
            ("Waterfall", "Trail passes by or includes a waterfall", None),
            ("Forest", "Mainly through wooded areas", None),
            ("River View", "Scenic views of rivers or streams", None),
            ("Mountain View", "Panoramic mountain vistas", None),
            ("Wildlife", "Good spot for animal watching", None),
            ("Picnic Area", "Designated picnic spots", None),
            ("Parking", "Available parking at trailhead", None),
            ("Toilets", "Public toilets available", None)
        ]
        for feature in features:
            db.execute_update(
                "INSERT INTO CW2.Feature (FeatureName, Description, IconURL) VALUES (?, ?, ?)",
                feature
            )
        
        # 6. Create Sample Trails
        print("Creating sample trails...")
        
        # Trail 1: Plymbridge Circular Walk
        trail1_query = """
        INSERT INTO CW2.Trail (
            TrailName, LocationID, Difficulty, Length, ElevationGain,
            EstTimeMin, EstTimeMax, RouteType, Description, UserID, IsPublic,
            CreatedAt, UpdatedAt
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        current_time = datetime.now()
        trail1_values = (
            "Plymbridge Circular Walk",
            1,  # Plymbridge Woods
            "Easy",
            3.5,
            120,
            90,
            120,
            "Loop",
            "A beautiful circular walk through Plymbridge Woods along the River Plym. Perfect for families and casual walkers.",
            1,  # Ada Lovelace (admin)
            1,  # IsPublic
            current_time,
            current_time
        )
        trail1_id = db.execute_update(trail1_query, trail1_values)
        print(f"  Created trail #{trail1_id}: Plymbridge Circular Walk")
        
        # Get the TrailID we just inserted
        if not trail1_id:
            # If execute_update doesn't return ID, fetch it
            result = db.execute_query("SELECT MAX(TrailID) as max_id FROM CW2.Trail")
            trail1_id = result[0]['max_id'] if result else 1
        
        # 7. Add Trail Points for the trail
        print("Adding trail points...")
        trail_points = [
            (trail1_id, 1, 50.3964, -4.0916, "Trail Start - Plymbridge Car Park", None, current_time),
            (trail1_id, 2, 50.3972, -4.0923, "River Viewpoint - Great photo spot", None, current_time),
            (trail1_id, 3, 50.3985, -4.0938, "Woodland Section - Ancient trees", None, current_time),
            (trail1_id, 4, 50.3991, -4.0952, "Highest Point - View over valley", None, current_time),
            (trail1_id, 5, 50.3964, -4.0916, "Trail End - Return to car park", None, current_time)
        ]
        
        for point in trail_points:
            db.execute_update(
                "INSERT INTO CW2.Trail_Point (TrailID, PointOrder, Latitude, Longitude, Description, Elevation, CreatedAt) VALUES (?, ?, ?, ?, ?, ?, ?)",
                point
            )
        
        # 8. Link Features to Trail
        print("Linking features to trails...")
        trail_features = [
            (trail1_id, 2, 1, current_time),  # Forest
            (trail1_id, 3, 1, current_time),  # River View
            (trail1_id, 6, 1, current_time),  # Picnic Area
            (trail1_id, 7, 1, current_time)   # Parking
        ]
        
        for feature in trail_features:
            db.execute_update(
                "INSERT INTO CW2.Trail_Feature (TrailID, FeatureID, AddedBy, AddedAt) VALUES (?, ?, ?, ?)",
                feature
            )
        
        # 9. Add a Review
        print("Adding reviews...")
        review_values = (
            trail1_id,
            3,  # UserID: Ada Lovelace (user)
            5,
            "Beautiful walk! Perfect for a sunny afternoon. The river views are stunning.",
            current_time,
            0
        )
        db.execute_update(
            "INSERT INTO CW2.Review (TrailID, UserID, Rating, ReviewText, DateReviewed, IsHelpful) VALUES (?, ?, ?, ?, ?, ?)",
            review_values
        )
        
        # 10. Add Weather Data
        print("Adding weather data...")
        weather_values = (
            trail1_id,
            15.5,
            "Partly Cloudy",
            current_time,
            current_time.date()
        )
        db.execute_update(
            "INSERT INTO CW2.Weather (TrailID, Temperature, Condition, RecordedAt, ForecastDate) VALUES (?, ?, ?, ?, ?)",
            weather_values
        )
        
        # 11. Verify Data
        print("\nDatabase seeded successfully!")
        print("\nVerification Summary:")
        
        # Count records
        tables_to_check = [
            "Country", "City", "Location", "[User]", "Trail", 
            "Trail_Point", "Feature", "Trail_Feature", 
            "Review", "Weather"
        ]
        
        for table in tables_to_check:
            try:
                result = db.execute_query(f"SELECT COUNT(*) as count FROM CW2.{table}")
                count = result[0]['count'] if result else 0
                print(f"   {table}: {count} records")
            except Exception as e:
                print(f"   {table}: Error - {e}")
        
        # Test views
        print("\nTesting views:")
        try:
            public_trails = db.execute_query("SELECT TOP 3 * FROM CW2.Public_Trails_View")
            print(f"   Public_Trails_View: {len(public_trails)} trails visible")
            
            trail_details = db.execute_query("SELECT TOP 1 * FROM CW2.Trail_Details_View")
            if trail_details:
                print(f"   Trail_Details_View: First trail '{trail_details[0]['TrailName']}'")
        except Exception as e:
            print(f"   Views test failed: {e}")
        
        # Test triggers (check if logs were created)
        print("\nTesting triggers:")
        try:
            logs = db.execute_query("SELECT COUNT(*) as count FROM CW2.Trail_Log")
            log_count = logs[0]['count'] if logs else 0
            print(f"   Trail_Log: {log_count} trail actions logged")
        except:
            print("   Trail_Log: Error checking")
        
        print("\n" + "=" * 60)
        print("SEEDING COMPLETE!")
        print("=" * 60)
        print("\nSample Data Summary:")
        print("   • 1 Trail with complete data")
        print("   • 4 Users (2 admins, 2 regular users)")
        print("   • 3 Locations with coordinates")
        print("   • 8 Trail features")
        print("   • 5 Trail points")
        print("   • 1 Review")
        print("   • 1 Weather forecast")
        print("\nReady to start the API with: python run.py")
        
        return True
        
    except Exception as e:
        print(f"\nError during seeding: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = seed_database()
    if success:
        print("\nAll done! The database is ready for use.")
        print("\nNext steps:")
        print("   1. Start the API: python run.py")
        print("   2. Access Swagger UI: http://localhost:5000/docs")
        print("   3. Test endpoints with the sample data")
    else:
        print("\nSeeding failed. Please check the error messages above.")
        sys.exit(1)