\# TrailService API Guide



\## Overview

TrailService is a RESTful microservice for managing hiking trails as part of a wellbeing application. It provides CRUD operations for trails, users, and locations.



\## Base URL

http://localhost:5000/



\## Authentication

All endpoints (except public ones) require JWT authentication via the external Authenticator API.



\### Getting a Token

1\. Register/login via the Authenticator API

2\. Use the returned JWT token in the Authorization header



\### Using the Token

Authorization: Bearer {your\_jwt\_token}



\## Endpoints



\### Public Endpoints

\- `GET /` - API information

\- `GET /health` - Health check

\- `GET /api/v1/trails` - Get public trails

\- `GET /api/v1/trails/{id}` - Get trail details (if public)

\- `GET /api/v1/locations` - Get locations

\- `GET /api/v1/countries` - Get countries



\### Protected Endpoints

\- `POST /api/v1/trails` - Create trail

\- `PUT /api/v1/trails/{id}` - Update trail

\- `DELETE /api/v1/trails/{id}` - Delete trail

\- `GET /api/v1/users/me` - Get current user profile

\- `POST /api/v1/trails/{id}/points` - Add trail point



\### Admin Endpoints

\- `GET /api/v1/users` - Get all users

\- `PUT /api/v1/users/{id}/role` - Update user role



\## Data Models



\### Trail

```json

{

&nbsp; "trail\_id": 1,

&nbsp; "trail\_name": "Plymbridge Circular Walk",

&nbsp; "difficulty": "Easy",

&nbsp; "length": 3.5,

&nbsp; "elevation\_gain": 120,

&nbsp; "route\_type": "Loop",

&nbsp; "description": "A beautiful walk...",

&nbsp; "user\_id": 1,

&nbsp; "is\_public": true,

&nbsp; "created\_at": "2023-12-01T10:30:00",

&nbsp; "updated\_at": "2023-12-01T10:30:00"

}

