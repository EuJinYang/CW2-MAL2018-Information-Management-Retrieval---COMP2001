# CW2 MAL2018 Information Management Retrieval - COMP2001
MAL2018 Information Management &amp; Retrieval - COMP2001 Assessment 2 [Trail Micro-Service]

## Quick Start Guide

### Prerequisites
- Python 3.9+
- SQL Server access (localhost)
- ODBC Driver 17 for SQL Server
- External Authenticator API access
- Azure Data Studio

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
   Swagger Documentation: http://localhost:5000/docs

   FastAPI Documentation: http://localhost:5000/redocs
