"""
Seed database with sample data for TrailService (CW2 Schema)
This script populates the CW2 schema with test data for development and demonstration.
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
            ("Australia",),
            ("Canada",),
            ("Germany",)
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
            ("Sydney", 3),    # Australia
            ("Toronto", 4),   # Canada
            ("Berlin", 5)     # Germany
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
            ("Dartmoor National Park", 1, 1, "50.5700,-3.9200"),
            ("Sydney Harbour", 4, 3, "-33.8568,151.2153"),
            ("Rocky Mountains", None, 4, "51.1784,-115.5708"),
            ("Black Forest", 6, 5, "48.3325,8.1667")
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
                "INSERT INTO CW2.[User] (Username, Email, Role) VALUES (?, ?, ?)",
                user
            )
        
        # 5. Insert Features
        print("Inserting features...")
        features = [
            ("Waterfall", "Trail passes by or includes a waterfall"),
            ("Forest", "Mainly through wooded areas"),
            ("River View", "Scenic views of rivers or streams"),
            ("Mountain View", "Panoramic mountain vistas"),
            ("Wildlife", "Good spot for animal watching"),
            ("Picnic Area", "Designated picnic spots"),
            ("Parking", "Available parking at trailhead"),
            ("Toilets", "Public toilets available"),
            ("Camping", "Camping facilities available"),
            ("Historic Site", "Historical landmarks along trail")
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
            EstTimeMin, EstTimeMax, RouteType, Description, UserID, IsPublic
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        trail1_values = (
            "Plymbridge Circular Walk",
            1,  # Plymbridge Woods
            "Easy",
            3.5,
            120,
            90,
            120,
            "Loop",
            "A beautiful circular walk through Plymbridge Woods along the River Plym. Perfect for families and casual walkers. The trail offers stunning river views and passes through ancient woodland.",
            1,  # Ada Lovelace (admin)
            1
        )
        trail1_id = db.execute_update(trail1_query, trail1_values)
        print(f"      Created trail #{trail1_id}: Plymbridge Circular Walk")
        
        # Trail 2: Dartmoor Challenge
        trail2_values = (
            "Dartmoor Challenge Route",
            3,  # Dartmoor National Park
            "Hard",
            15.8,
            650,
            300,
            420,
            "Point-to-point",
            "A challenging hike across Dartmoor National Park with breathtaking moorland views. Not for beginners - proper hiking gear and navigation skills required.",
            2,  # Tim Berners-Lee
            1
        )
        trail2_id = db.execute_update(trail1_query, trail2_values)
        print(f"      Created trail #{trail2_id}: Dartmoor Challenge Route")
        
        # Trail 3: Central Park Stroll
        trail3_values = (
            "Central Park Stroll",
            2,  # Central Park
            "Easy",
            2.1,
            25,
            45,
            60,
            "Out & back",
            "A gentle stroll through New York's Central Park. Perfect for a quick escape from the city bustle. Family and wheelchair friendly.",
            3,  # Ada Lovelace (user)
            1
        )
        trail3_id = db.execute_update(trail1_query, trail3_values)
        print(f"      Created trail #{trail3_id}: Central Park Stroll")
        
        # Trail 4: Private Test Trail
        trail4_values = (
            "Private Test Trail",
            5,  # Rocky Mountains
            "Moderate",
            8.5,
            320,
            180,
            240,
            "Loop",
            "A private trail for testing purposes only. Not visible to public users.",
            4,  # William Frost
            0   # IsPublic = False
        )
        trail4_id = db.execute_update(trail1_query, trail4_values)
        print(f"      Created trail #{trail4_id}: Private Test Trail (hidden)")
        
        # 7. Add Trail Points
        print("Adding trail points...")
        
        # Points for Trail 1
        trail1_points = [
            (trail1_id, 1, 50.3964, -4.0916, "Trail Start - Plymbridge Car Park", 50.0),
            (trail1_id, 2, 50.3972, -4.0923, "River Viewpoint - Great photo spot", 48.5),
            (trail1_id, 3, 50.3985, -4.0938, "Woodland Section - Ancient trees", 52.0),
            (trail1_id, 4, 50.3991, -4.0952, "Highest Point - View over valley", 55.5),
            (trail1_id, 5, 50.3964, -4.0916, "Trail End - Return to car park", 50.0)
        ]
        
        # Points for Trail 2
        trail2_points = [
            (trail2_id, 1, 50.5700, -3.9200, "Start - Princetown", 450.0),
            (trail2_id, 2, 50.5750, -3.9150, "Great Mis Tor", 520.0),
            (trail2_id, 3, 50.5800, -3.9100, "North Hessary Tor", 510.0),
            (trail2_id, 4, 50.5850, -3.9050, "Finish - Postbridge", 440.0)
        ]
        
        all_points = trail1_points + trail2_points
        for point in all_points:
            db.execute_update(
                "INSERT INTO CW2.Trail_Point (TrailID, PointOrder, Latitude, Longitude, Description, Elevation) VALUES (?, ?, ?, ?, ?, ?)",
                point
            )
        print(f"Added {len(all_points)} trail points")
        
        # 8. Link Features to Trails
        print("Linking features to trails...")
        
        # Trail 1 features
        trail1_features = [
            (trail1_id, 2, 1),  # Forest
            (trail1_id, 3, 1),  # River View
            (trail1_id, 6, 1),  # Picnic Area
            (trail1_id, 7, 1),  # Parking
            (trail1_id, 8, 1)   # Toilets
        ]
        
        # Trail 2 features
        trail2_features = [
            (trail2_id, 4, 2),  # Mountain View
            (trail2_id, 5, 2),  # Wildlife
            (trail2_id, 9, 2)   # Camping
        ]
        
        # Trail 3 features
        trail3_features = [
            (trail3_id, 2, 3),  # Forest
            (trail3_id, 6, 3),  # Picnic Area
            (trail3_id, 7, 3),  # Parking
            (trail3_id, 8, 3),  # Toilets
            (trail3_id, 10, 3)  # Historic Site
        ]
        
        all_features = trail1_features + trail2_features + trail3_features
        for feature in all_features:
            db.execute_update(
                "INSERT INTO CW2.Trail_Feature (TrailID, FeatureID, AddedBy) VALUES (?, ?, ?)",
                feature
            )
        print(f"Added {len(all_features)} feature links")
        
        # 9. Add Reviews
        print("Adding reviews...")
        
        reviews = [
            (trail1_id, 3, 5, "Beautiful walk! Perfect for a sunny afternoon. The river views are stunning. Family-friendly and well-maintained."),
            (trail1_id, 4, 4, "Great trail for beginners. Would be 5 stars if there were more signposts."),
            (trail2_id, 1, 5, "Challenging but rewarding! The moorland views are incredible. Make sure to bring a map and compass."),
            (trail2_id, 5, 3, "Very difficult trail. Not for casual hikers. Views were amazing though."),
            (trail3_id, 2, 4, "Perfect escape in the middle of the city. Busy on weekends but worth it.")
        ]
        
        for review in reviews:
            db.execute_update(
                "INSERT INTO CW2.Review (TrailID, UserID, Rating, ReviewText) VALUES (?, ?, ?, ?)",
                review
            )
        print(f"Added {len(reviews)} reviews")
        
        # 10. Add Weather Data
        print("Adding weather data...")
        
        weather_data = [
            (trail1_id, 15.5, "Partly Cloudy", "2023-11-25"),
            (trail2_id, 12.0, "Sunny", "2023-11-25"),
            (trail3_id, 18.0, "Clear", "2023-11-25")
        ]
        
        for weather in weather_data:
            db.execute_update(
                "INSERT INTO CW2.Weather (TrailID, Temperature, Condition, ForecastDate) VALUES (?, ?, ?, ?)",
                weather
            )
        print("Added weather forecasts")
        
        # 11. Add Photos
        print("Adding sample photos...")
        
        photos = [
            (trail1_id, 3, "https://www.exploredevon.info/wp-content/uploads/2014/05/Plym-Bridge-Chris-Downer-geograph.org_.uk_.jpg", "River view from the trail", 1),
            (trail1_id, 4, "https://eu-assets.simpleview-europe.com/plymouth2016/imageresizer/?image=%2Fdmsimgs%2Fimage00008_621582239.jpeg&action=ProductDetailNew", "Ancient oak tree", 1),
            (trail2_id, 1, "https://www.sykescottages.co.uk/inspiration/wp-content/uploads/Hound-Tor-1.jpg", "Moorland panorama", 1),
            (trail3_id, 2, "https://d2wsrtli9cxkek.cloudfront.net/media/images/locations/TheLake-20190908.jpg?auto=compress%2Cformat&crop=focalpoint&fit=crop&fp-x=0.5583&fp-y=0.6018&h=1151.1627906977&q=80&w=2475&s=e1abae18259cb8603efdc29ad7fb4556", "Central Park lake", 1)
        ]
        
        for photo in photos:
            db.execute_update(
                "INSERT INTO CW2.Photo (TrailID, UserID, PhotoURL, Caption, IsApproved) VALUES (?, ?, ?, ?, ?)",
                photo
            )
        print(f"Added {len(photos)} photos")
        
        # 12. Add User Activity Logs
        print("Adding user activity logs...")
        
        activities = [
            (1, "LOGIN", "User logged into the system"),
            (2, "TRAIL_CREATE", "Created new trail"),
            (3, "REVIEW_POST", "Posted a trail review"),
            (4, "PHOTO_UPLOAD", "Uploaded trail photo")
        ]
        
        for activity in activities:
            db.execute_update(
                "INSERT INTO CW2.User_Activity (UserID, ActivityType, Details) VALUES (?, ?, ?)",
                activity
            )
        print("Added user activity logs")
        
        # 13. Verify Data
        print("\nDatabase seeded successfully!")
        print("\nVerification Summary:")
        
        # Count records
        tables_to_check = [
            "Country", "City", "Location", "[User]", "Trail", 
            "Trail_Point", "Feature", "Trail_Feature", 
            "Review", "Photo", "Weather", "User_Activity"
        ]
        
        for table in tables_to_check:
            try:
                result = db.execute_query(f"SELECT COUNT(*) as count FROM CW2.{table}")
                count = result[0]['count'] if result else 0
                print(f"   {table}: {count} records")
            except:
                print(f"   {table}: Error counting")
        
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
        print("   • 3 Public trails, 1 Private trail")
        print("   • 6 Users (2 admins, 4 regular users)")
        print("   • 5 Locations with coordinates")
        print("   • 10 Trail features")
        print("   • Multiple reviews, photos, and weather entries")
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