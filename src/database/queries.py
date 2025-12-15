"""
SQL queries for TrailService database operations
"""

# ========== USER QUERIES ==========
GET_USER_BY_ID = """
SELECT UserID, Username, Email, Role, CreatedAt, LastLogin
FROM CW2.[User]
WHERE UserID = ?
"""

GET_USER_BY_EMAIL = """
SELECT UserID, Username, Email, Role, CreatedAt, LastLogin
FROM CW2.[User]
WHERE Email = ?
"""

CREATE_USER = """
INSERT INTO CW2.[User] (Username, Email, Role, CreatedAt)
VALUES (?, ?, ?, ?)
"""

UPDATE_USER_LAST_LOGIN = """
UPDATE CW2.[User]
SET LastLogin = ?
WHERE UserID = ?
"""

# ========== TRAIL QUERIES ==========
GET_TRAIL_BY_ID = """
SELECT t.*, u.Username, l.LocationName
FROM CW2.Trail t
LEFT JOIN CW2.[User] u ON t.UserID = u.UserID
LEFT JOIN CW2.Location l ON t.LocationID = l.LocationID
WHERE t.TrailID = ?
"""

GET_PUBLIC_TRAILS = """
SELECT t.*, u.Username, l.LocationName
FROM CW2.Trail t
LEFT JOIN CW2.[User] u ON t.UserID = u.UserID
LEFT JOIN CW2.Location l ON t.LocationID = l.LocationID
WHERE t.IsPublic = 1
ORDER BY t.CreatedAt DESC
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
"""

CREATE_TRAIL = """
INSERT INTO CW2.Trail (
    TrailName, LocationID, Difficulty, Length, ElevationGain,
    EstTimeMin, EstTimeMax, RouteType, Description, UserID,
    IsPublic, CreatedAt, UpdatedAt
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

UPDATE_TRAIL = """
UPDATE CW2.Trail
SET 
    TrailName = ?,
    LocationID = ?,
    Difficulty = ?,
    Length = ?,
    ElevationGain = ?,
    EstTimeMin = ?,
    EstTimeMax = ?,
    RouteType = ?,
    Description = ?,
    IsPublic = ?,
    UpdatedAt = ?
WHERE TrailID = ?
"""

DELETE_TRAIL = """
DELETE FROM CW2.Trail WHERE TrailID = ?
"""

# ========== TRAIL POINTS QUERIES ==========
GET_TRAIL_POINTS = """
SELECT PointID, TrailID, PointOrder, Latitude, Longitude,
       Description, Elevation, CreatedAt
FROM CW2.Trail_Point
WHERE TrailID = ?
ORDER BY PointOrder
"""

CREATE_TRAIL_POINT = """
INSERT INTO CW2.Trail_Point (
    TrailID, PointOrder, Latitude, Longitude,
    Description, Elevation, CreatedAt
) VALUES (?, ?, ?, ?, ?, ?, ?)
"""

# ========== FEATURE QUERIES ==========
GET_TRAIL_FEATURES = """
SELECT f.FeatureID, f.FeatureName, f.Description, f.IconURL
FROM CW2.Feature f
INNER JOIN CW2.Trail_Feature tf ON f.FeatureID = tf.FeatureID
WHERE tf.TrailID = ?
"""

ADD_TRAIL_FEATURE = """
INSERT INTO CW2.Trail_Feature (TrailID, FeatureID, AddedBy, AddedAt)
VALUES (?, ?, ?, ?)
"""

# ========== LOCATION QUERIES ==========
GET_LOCATION_BY_ID = """
SELECT l.*, c.CityName, co.CountryName
FROM CW2.Location l
LEFT JOIN CW2.City c ON l.CityID = c.CityID
LEFT JOIN CW2.Country co ON l.CountryID = co.CountryID
WHERE l.LocationID = ?
"""

# ========== AUDIT LOG QUERIES ==========
LOG_TRAIL_ACTION = """
INSERT INTO CW2.Trail_Log (TrailID, UserID, Action, ActionDate, Details)
VALUES (?, ?, ?, ?, ?)
"""

# ========== VIEW QUERIES ==========
TRAIL_DETAILS_VIEW = """
SELECT * FROM CW2.Trail_Details_View
WHERE TrailID = ?
"""

PUBLIC_TRAILS_VIEW = """
SELECT * FROM CW2.Public_Trails_View
ORDER BY CreatedAt DESC
"""

# Store all queries in a dictionary for easy access
QUERIES = {
    "user": {
        "get_by_id": GET_USER_BY_ID,
        "get_by_email": GET_USER_BY_EMAIL,
        "create": CREATE_USER,
        "update_last_login": UPDATE_USER_LAST_LOGIN
    },
    "trail": {
        "get_by_id": GET_TRAIL_BY_ID,
        "get_public": GET_PUBLIC_TRAILS,
        "create": CREATE_TRAIL,
        "update": UPDATE_TRAIL,
        "delete": DELETE_TRAIL
    },
    "trail_point": {
        "get_by_trail": GET_TRAIL_POINTS,
        "create": CREATE_TRAIL_POINT
    },
    "feature": {
        "get_by_trail": GET_TRAIL_FEATURES,
        "add": ADD_TRAIL_FEATURE
    },
    "location": {
        "get_by_id": GET_LOCATION_BY_ID
    },
    "audit": {
        "log_action": LOG_TRAIL_ACTION
    },
    "view": {
        "trail_details": TRAIL_DETAILS_VIEW,
        "public_trails": PUBLIC_TRAILS_VIEW
    }
}