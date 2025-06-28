# Smart Timetable API Documentation

## Base URL
```
https://your-app-domain.replit.app/api
```

## Authentication
All API endpoints require authentication via Bearer token in the Authorization header:
```
Authorization: Bearer <token>
```

---

## 1. Authentication APIs

### 1.1 User Login
**Endpoint:** `POST /api/auth/login`  
**Description:** Authenticates users based on role and credentials.

**Request Body:**
```json
{
  "email": "admin@university.edu",
  "password": "admin123",
  "role": "admin|teacher|student"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "1",
      "email": "admin@university.edu",
      "name": "System Administrator",
      "role": "admin",
      "studentId": null,
      "teacherId": null,
      "section": null,
      "department": "Administration",
      "phone": "+919999999999",
      "campus": "Campus-3"
    },
    "expiresIn": 86400
  },
  "message": "Login successful"
}
```

### 1.2 Token Refresh
**Endpoint:** `POST /api/auth/refresh`  
**Description:** Refreshes authentication token.

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "new_jwt_token_here",
    "expiresIn": 86400
  }
}
```

### 1.3 Logout
**Endpoint:** `POST /api/auth/logout`  
**Description:** Invalidates user session.

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

## 2. Event/Timetable APIs

### 2.1 Get All Events
**Endpoint:** `GET /api/events`  
**Description:** Retrieves events based on user role and applied filters.

**Query Parameters:**
- `section` (optional): Filter by section (A, B, C)
- `teacherId` (optional): Filter by teacher ID
- `campus` (optional): Filter by campus
- `type` (optional): Filter by event type (theory, lab, workshop)
- `day` (optional): Filter by day (0-6, where 0 is Monday)
- `startDate` (optional): Filter events from date (YYYY-MM-DD)
- `endDate` (optional): Filter events to date (YYYY-MM-DD)

**Response:**
```json
{
  "success": true,
  "data": {
    "events": [
      {
        "id": 1,
        "section": "A",
        "scheme": "A",
        "title": "Data Structures",
        "day": 0,
        "startHour": 8,
        "endHour": 9,
        "type": "theory",
        "room": "CS-101",
        "campus": "Campus-3",
        "teacher": "Dr. Aryan Maharaj",
        "teacherId": "TCH1001",
        "color": "bg-blue-100 text-blue-800",
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z"
      }
    ],
    "totalCount": 150,
    "filteredCount": 25
  }
}
```

### 2.2 Get Event by ID
**Endpoint:** `GET /api/events/{id}`  
**Description:** Retrieves a specific event by ID.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "section": "A",
    "scheme": "A",
    "title": "Data Structures",
    "day": 0,
    "startHour": 8,
    "endHour": 9,
    "type": "theory",
    "room": "CS-101",
    "campus": "Campus-3",
    "teacher": "Dr. Aryan Maharaj",
    "teacherId": "TCH1001",
    "color": "bg-blue-100 text-blue-800",
    "description": "Data Structures - Theory",
    "createdAt": "2024-01-01T00:00:00Z",
    "updatedAt": "2024-01-01T00:00:00Z"
  }
}
```

### 2.3 Create Event (Admin Only)
**Endpoint:** `POST /api/events`  
**Description:** Creates a new timetable event.

**Request Body:**
```json
{
  "section": "A",
  "scheme": "A",
  "title": "Advanced Algorithms",
  "day": 1,
  "startHour": 10,
  "endHour": 12,
  "type": "theory",
  "room": "CS-201",
  "campus": "Campus-3",
  "teacherId": "TCH1001",
  "color": "bg-blue-100 text-blue-800"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 151,
    "section": "A",
    "scheme": "A",
    "title": "Advanced Algorithms",
    "day": 1,
    "startHour": 10,
    "endHour": 12,
    "type": "theory",
    "room": "CS-201",
    "campus": "Campus-3",
    "teacher": "Dr. Aryan Maharaj",
    "teacherId": "TCH1001",
    "color": "bg-blue-100 text-blue-800",
    "createdAt": "2024-01-15T10:00:00Z",
    "updatedAt": "2024-01-15T10:00:00Z"
  },
  "message": "Event created successfully"
}
```

### 2.4 Update Event (Admin Only)
**Endpoint:** `PUT /api/events/{id}`  
**Description:** Updates an existing event.

**Request Body:**
```json
{
  "title": "Advanced Data Structures",
  "day": 0,
  "startHour": 8,
  "endHour": 10,
  "type": "theory",
  "room": "CS-101",
  "campus": "Campus-3",
  "teacherId": "TCH1001"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "section": "A",
    "scheme": "A",
    "title": "Advanced Data Structures",
    "day": 0,
    "startHour": 8,
    "endHour": 10,
    "type": "theory",
    "room": "CS-101",
    "campus": "Campus-3",
    "teacher": "Dr. Aryan Maharaj",
    "teacherId": "TCH1001",
    "color": "bg-blue-100 text-blue-800",
    "updatedAt": "2024-01-15T10:30:00Z"
  },
  "message": "Event updated successfully"
}
```

### 2.5 Delete Event (Admin Only)
**Endpoint:** `DELETE /api/events/{id}`  
**Description:** Deletes an event.

**Response:**
```json
{
  "success": true,
  "message": "Event deleted successfully"
}
```

### 2.6 Swap Events (Admin/Teacher)
**Endpoint:** `POST /api/events/swap`  
**Description:** Swaps two events in the timetable.

**Request Body:**
```json
{
  "sourceEventId": 1,
  "targetEventId": 2,
  "reason": "Room conflict resolution"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "swappedEvents": [
      {
        "id": 1,
        "newTimeSlot": {
          "day": 1,
          "startHour": 10,
          "endHour": 12
        }
      },
      {
        "id": 2,
        "newTimeSlot": {
          "day": 0,
          "startHour": 8,
          "endHour": 9
        }
      }
    ]
  },
  "message": "Events swapped successfully"
}
```

---

## 3. User Management APIs

### 3.1 Get User Profile
**Endpoint:** `GET /api/users/profile`  
**Description:** Retrieves current user's profile information.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "1",
    "name": "System Administrator",
    "email": "admin@university.edu",
    "role": "admin",
    "phone": "+919999999999",
    "studentId": null,
    "section": null,
    "teacherId": null,
    "department": "Administration",
    "campus": "Campus-3",
    "batch": null
  }
}
```

### 3.2 Update User Profile
**Endpoint:** `PUT /api/users/profile`  
**Description:** Updates user profile information.

**Request Body:**
```json
{
  "name": "Updated Name",
  "phone": "+919876543210"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "1",
    "name": "Updated Name",
    "email": "admin@university.edu",
    "phone": "+919876543210",
    "updatedAt": "2024-01-15T10:30:00Z"
  },
  "message": "Profile updated successfully"
}
```

### 3.3 Get All Users (Admin Only)
**Endpoint:** `GET /api/users`  
**Description:** Retrieves all users with pagination.

**Query Parameters:**
- `role` (optional): Filter by role
- `department` (optional): Filter by department
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)

**Response:**
```json
{
  "success": true,
  "data": {
    "users": [
      {
        "id": "1",
        "name": "System Administrator",
        "email": "admin@university.edu",
        "role": "admin",
        "department": "Administration",
        "section": null,
        "isActive": true,
        "lastLogin": "2024-01-15T10:00:00Z"
      }
    ],
    "pagination": {
      "currentPage": 1,
      "totalPages": 5,
      "totalItems": 100,
      "itemsPerPage": 20
    }
  }
}
```

---

## 4. Teacher-Specific APIs

### 4.1 Get Teacher Schedule
**Endpoint:** `GET /api/teachers/{teacherId}/schedule`  
**Description:** Retrieves schedule for a specific teacher.

**Query Parameters:**
- `week` (optional): Week of year
- `campus` (optional): Filter by campus

**Response:**
```json
{
  "success": true,
  "data": {
    "teacherId": "TCH1001",
    "teacherName": "Dr. Aryan Maharaj",
    "schedule": [
      {
        "id": 1,
        "title": "Data Structures",
        "section": "A",
        "day": 0,
        "startHour": 8,
        "endHour": 9,
        "room": "CS-101",
        "campus": "Campus-3",
        "type": "theory"
      }
    ],
    "totalHours": 20,
    "totalClasses": 15
  }
}
```

---

## 5. Student-Specific APIs

### 5.1 Get Student Schedule
**Endpoint:** `GET /api/students/schedule`  
**Description:** Get schedule for current student.

**Response:**
```json
{
  "success": true,
  "data": {
    "studentId": "STU220001",
    "section": "A01",
    "batch": "A01",
    "schedule": [
      {
        "id": 1,
        "title": "Data Structures",
        "day": 0,
        "startHour": 8,
        "endHour": 9,
        "teacher": "Dr. Aryan Maharaj",
        "teacherId": "TCH1001",
        "room": "CS-101",
        "campus": "Campus-3",
        "type": "theory"
      }
    ],
    "totalClasses": 25
  }
}
```

---

## 6. System APIs

### 6.1 Health Check
**Endpoint:** `GET /api/health`  
**Description:** System health check (no auth required).

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "timestamp": "2024-01-15T10:00:00Z",
    "version": "1.0.0"
  }
}
```

### 6.2 System Statistics (Admin Only)
**Endpoint:** `GET /api/stats`  
**Description:** Get system statistics.

**Response:**
```json
{
  "success": true,
  "data": {
    "totalUsers": 7500,
    "totalStudents": 7200,
    "totalTeachers": 100,
    "totalEvents": 864,
    "totalSections": 72,
    "activeCampuses": ["Campus-3", "Campus-8", "Campus-15B", "Campus-17"]
  }
}
```

---

## Error Responses

All endpoints return consistent error responses:

```json
{
  "success": false,
  "message": "Error description"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

---

## Usage Examples

### Login and Get Events
```javascript
// Login
const loginResponse = await fetch('/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'admin@university.edu',
    password: 'admin123',
    role: 'admin'
  })
});

const { data } = await loginResponse.json();
const token = data.token;

// Get events
const eventsResponse = await fetch('/api/events', {
  headers: { 'Authorization': `Bearer ${token}` }
});

const events = await eventsResponse.json();
```

### Create New Event (Admin)
```javascript
const newEvent = await fetch('/api/events', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    section: 'A',
    scheme: 'A',
    title: 'Machine Learning',
    day: 1,
    startHour: 10,
    endHour: 12,
    type: 'theory',
    room: 'CS-201',
    campus: 'Campus-3',
    teacherId: 'TCH1001'
  })
});
```

### Get Student Schedule
```javascript
const schedule = await fetch('/api/students/schedule', {
  headers: { 'Authorization': `Bearer ${studentToken}` }
});

const studentSchedule = await schedule.json();
```

---

## Notes for UI Developer

1. **Authentication**: Store JWT token securely and include in all API requests
2. **Role-based Access**: Different endpoints available based on user role
3. **Error Handling**: Always check `success` field in response
4. **Pagination**: Use page and limit parameters for large datasets
5. **Date Format**: All dates are in ISO 8601 format
6. **Time Slots**: Hours are in 24-hour format (8 = 8:00 AM, 14 = 2:00 PM)
7. **Day Mapping**: 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday, 5=Saturday, 6=Sunday

## Testing

You can test the APIs using tools like Postman or curl. The system includes demo accounts:
- **Admin**: admin@university.edu / admin123
- **Teachers**: Register with valid Teacher IDs from CSV data
- **Students**: Register with valid Student IDs from CSV data