# CW2 MAL2018 Information Management Retrieval - COMP2001
MAL2018 Information Management &amp; Retrieval - COMP2001 Assessment 2 [Trail Micro-Service]
<br> Author: Eu Jin Yang
<br> Programme of Study: BSc (Hons) Computer Science (Software Engineering)

## Quick Start Guide

### Prerequisites
- Python 3.9+
- SQL Server access (localhost)
- ODBC Driver 17 for SQL Server
- External Authenticator API access
- Docker Desktop
- Azure Data Studio
- FastAPI
- Swagger

### Installation & Running
1. **Clone and setup:**
   ```bash
   git clone https://github.com/yourusername/trail_service.git
   cd trail_service
   python -m venv venv
   venv\Scripts\activate  # Windows
   # OR: source venv/bin/activate  # Mac/Linux
   pip install -r requirements.txt

2. **Seed the database**
   ```bash
   python scripts/seed_database.py

3. **Run the API**
   ```bash
   python run.py

4. **Access the API**
   ```bash
   Template (Home Page): http://localhost:5000
   
   Swagger Documentation: http://localhost:5000/docs

   FastAPI Documentation: http://localhost:5000/redoc

5. **Sample Data**
   ```bash
   Create Trail (POST):
   {
   "trail_name": "Dartmoor Challenge Route",
   "difficulty": "Hard",
   "length": 15.8,
   "est_time_min": 300,
   "est_time_max": 420,
   "route_type": "Point-to-point",
   "user_id": 1,
   "is_public": true
   }

   Update Trail (PUT):
   {
   "trail_name": "Updated Trail Name",
   "location_id": 2,
   "difficulty": "Moderate",
   "length": 4.5,
   "elevation_gain": 150,
   "est_time_min": 100,
   "est_time_max": 150,
   "route_type": "Loop",
   "description": "Updated description of the trail.",
   "is_public": false
   }

   Delete Trali (DELETE): No JSON body needed

   Create Location (POST):
   {
   "location_name": "Plymbridge Woods",
   "city_id": 1,
   "country_id": 1,
   "coordinates": "50.3964,-4.0916"
   }

   Get Locations (GET): No JSON body needed

   Get Location by ID (GET): No JSON body needed

   Get Countries (GET): No JSON body needed

   Get Cities by Country (GET): No JSON body needed

   Get Users (GET): No JSON body needed

   Get User by ID (GET): No JSON body needed

   Update User Role (PUT):
   {
   "role": "admin"
   }

   Get User Trails (GET): No JSON body needed
