# Smart Timetable Management System - Complete Documentation

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [File Structure & Purpose](#file-structure--purpose)
4. [ML Pipeline Workflow](#ml-pipeline-workflow)
5. [Edit & Optimization Flow](#edit--optimization-flow)
6. [User Portal Features](#user-portal-features)
7. [API Documentation](#api-documentation)
8. [Database Schema](#database-schema)
9. [Deployment Guide](#deployment-guide)

---

## 🎯 Project Overview

**Smart Timetable Management System** एक comprehensive academic scheduling platform है जो AI-powered optimization के साथ multi-user portal functionality provide करता है।

### Key Features:
- **AI-Powered Optimization**: RNN Autoencoder + OR-Tools constraint solving
- **Multi-User Portals**: Admin, Teacher, Student के लिए अलग interface
- **Real-Time Editing**: Interactive timetable editing with ML validation
- **Export Capabilities**: CSV/Excel downloads with role-based filtering
- **RESTful APIs**: JWT authentication के साथ complete API system

---

## 🏗️ System Architecture

```
Smart Timetable System
├── Frontend Layer (Bootstrap 5 + JavaScript)
├── Authentication Layer (Flask-Login + JWT)
├── Business Logic Layer (Flask Routes)
├── ML Pipeline Layer (PyTorch + OR-Tools)
├── Data Layer (PostgreSQL + SQLAlchemy)
└── API Layer (RESTful endpoints)
```

### Core Technologies:
- **Backend**: Python 3.11, Flask, SQLAlchemy
- **Database**: PostgreSQL with connection pooling
- **ML Framework**: PyTorch, scikit-learn, OR-Tools
- **Frontend**: Bootstrap 5, Font Awesome, jQuery
- **Authentication**: Flask-Login, bcrypt, PyJWT

---

## 📁 File Structure & Purpose

### Root Files
```
├── app.py                   # Main Flask application factory
├── app_server.py           # Production server entry point
├── models.py               # Database models (User, TimetableSlot, etc.)
├── main_pipeline.py        # ML pipeline orchestrator
├── test_complete_system.py # Complete system testing
└── replit.md              # Project configuration & preferences
```

### Routes Directory
```
routes/
├── admin.py               # Admin portal routes & functionality
├── teacher.py             # Teacher portal routes & editing
├── student.py             # Student portal routes (read-only)
├── auth.py                # Authentication & user management
└── api.py                 # RESTful API endpoints
```

### Templates Directory
```
templates/
├── base.html              # Main template layout
├── auth/                  # Login/register templates
├── admin/                 # Admin portal templates
├── teacher/               # Teacher portal templates
└── student/               # Student portal templates
```

### Pipeline Directory (ML Components)
```
pipeline/
├── encoding.py            # Time-slot feature encoding
├── training.py            # RNN Autoencoder training
├── anomaly_detection.py   # Real-time anomaly detection
├── constraint_solver.py   # OR-Tools optimization
├── healing.py             # Self-healing algorithms
├── data_optimizer.py      # Data preprocessing
└── models/               # Trained ML models storage
```

### Data Directory
```
data/
├── students.csv          # 7200+ student records
├── teachers.csv          # 94 teacher profiles
├── subjects.csv          # 73 academic subjects
├── rooms.csv            # 66 room assignments
├── activities.csv       # 125 activity types
└── slot_index.csv       # 864 time slot mappings
```

### Static Assets
```
static/
├── css/                 # Custom stylesheets
├── js/                  # JavaScript functionality
└── images/              # System images & icons
```

---

## 🧠 ML Pipeline Workflow

### Phase 1: Data Encoding
**File**: `pipeline/encoding.py`
```python
TimetableEncoder.fit_encoders() → Feature Vector Creation
```
- Converts timetable slots into numerical features
- LabelEncoder for categorical data (subjects, teachers, rooms)
- OneHotEncoder for time slots and days
- Creates 10-dimensional feature vectors

### Phase 2: Model Training
**File**: `pipeline/training.py`
```python
RNNAutoencoder.train() → Sequence Learning
```
- PyTorch-based sequence-to-sequence autoencoder
- Learns normal timetable patterns
- Creates reconstruction baseline for anomaly detection
- Saves trained model as `autoencoder.pth`

### Phase 3: Anomaly Detection
**File**: `pipeline/anomaly_detection.py`
```python
AnomalyDetector.detect_anomaly() → Pattern Validation
```
- Real-time monitoring of timetable edits
- Threshold-based anomaly scoring
- Constraint violation detection
- Automatic flagging of suspicious changes

### Phase 4: Self-Healing
**File**: `pipeline/healing.py`
```python
SelfHealingModule.reconstruct_slot() → Auto-Correction
```
- Automatic reconstruction of corrupted slots
- ML-guided slot suggestions
- Maintains scheduling consistency
- Preserves academic constraints

### Phase 5: Constraint Solving
**File**: `pipeline/constraint_solver.py`
```python
ConstraintSolver.optimize() → Final Optimization
```
- OR-Tools CP-SAT solver implementation
- Hard constraint enforcement
- Resource conflict resolution
- Schedule optimization

---

## ✏️ Edit & Optimization Flow

### Interactive Editing Process:

1. **User Edit Request**
   ```
   Teacher Portal → Edit Timetable → Slot Modification
   ```

2. **Real-Time Validation**
   ```python
   routes/teacher.py → update_slot()
   ↓
   pipeline/anomaly_detection.py → detect_slot_anomaly()
   ```

3. **ML Pipeline Trigger**
   ```python
   main_pipeline.py → run_complete_pipeline()
   ↓
   encoding → training_check → anomaly_detection → healing → optimization
   ```

4. **Constraint Application**
   ```python
   pipeline/constraint_solver.py → fix_constraint_violations()
   ```

5. **Database Update**
   ```python
   models.py → TimetableSlot.update() + TimetableHistory.log()
   ```

### Optimization Triggers:
- **Manual Edit**: Teacher slot modifications
- **Batch Upload**: Admin CSV imports
- **Scheduled Run**: Daily optimization tasks
- **Conflict Detection**: Automatic resolution

---

## 👥 User Portal Features

### Admin Portal (`routes/admin.py`)
**Purpose**: Complete system control and management

**Features**:
- Smart timetable generation from CSV data
- User management (Create/Edit/Delete accounts)
- System analytics and reporting
- Bulk data operations
- ML pipeline monitoring
- Complete CRUD operations on all data

**Key Routes**:
- `/admin/dashboard` - System overview
- `/admin/generate_timetable` - AI-powered generation
- `/admin/users` - User management
- `/admin/analytics` - System metrics
- `/admin/download_timetable` - Bulk exports

### Teacher Portal (`routes/teacher.py`)
**Purpose**: Personal schedule management and limited editing

**Features**:
- Personal timetable viewing and editing
- Student and subject information access
- Room assignment modifications
- Weekly schedule downloads
- Interactive slot editing with ML validation

**Key Routes**:
- `/teacher/dashboard` - Personal overview
- `/teacher/timetable` - Schedule viewing
- `/teacher/editable_timetable` - Interactive editing
- `/teacher/students` - Student information
- `/teacher/download_timetable` - Personal exports

### Student Portal (`routes/student.py`)
**Purpose**: Read-only access to personal schedules

**Features**:
- Personal timetable viewing
- Teacher and classmate information
- Subject details and schedules
- Personal schedule downloads
- Class notifications

**Key Routes**:
- `/student/dashboard` - Personal overview
- `/student/timetable` - Schedule viewing
- `/student/teachers` - Teacher information
- `/student/download_timetable` - Personal exports

---

## 🔌 API Documentation

### Authentication APIs
```
POST /api/auth/login        # JWT token generation
POST /api/auth/refresh      # Token refresh
POST /api/auth/logout       # Session termination
```

### Timetable APIs
```
GET  /api/events           # Role-based event retrieval
GET  /api/events/{id}      # Individual event details
POST /api/events           # Event creation (Admin only)
PUT  /api/events/{id}      # Event updates (Admin only)
DELETE /api/events/{id}    # Event deletion (Admin only)
POST /api/events/swap      # Event swapping (Admin/Teacher)
```

### User Management APIs
```
GET /api/users/profile     # Current user profile
PUT /api/users/profile     # Profile updates
GET /api/users             # All users (Admin only)
```

### System APIs
```
GET /api/health            # Health check
GET /api/stats             # System statistics (Admin only)
```

### API Features:
- **JWT Authentication**: Secure token-based access
- **Role-Based Access**: Permission-based endpoint access
- **Error Handling**: Consistent error response format
- **Pagination**: Large dataset handling
- **Filtering**: Role-based data filtering

---

## 🗄️ Database Schema

### Core Tables:

**users** - User authentication and profiles
```sql
id, username, email, password_hash, role, full_name, 
teacher_id, student_id, department, created_at
```

**timetable_slots** - Core scheduling data
```sql
id, slot_index, batch_id, section, day, time_start, time_end,
subject_code, teacher_id, room_id, campus, activity_type,
created_at, is_active, version
```

**timetable_history** - Change tracking and audit
```sql
id, timetable_data, version, created_by, created_at,
description, total_slots, affected_batches
```

**system_config** - Application configuration
```sql
id, config_key, config_value, description, updated_by, updated_at
```

### Data Relationships:
- Users → TimetableSlots (One-to-Many)
- TimetableSlots → TimetableHistory (Version tracking)
- Users → SystemConfig (Configuration management)

---

## 🚀 Deployment Guide

### Production Requirements:
- Python 3.11+
- PostgreSQL 12+
- 4GB RAM minimum
- 50GB storage space

### Environment Variables:
```bash
DATABASE_URL=postgresql://user:pass@host:port/db
FLASK_SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
```

### Deployment Steps:
1. **Database Setup**: PostgreSQL with proper schemas
2. **Python Environment**: Install dependencies via `pyproject.toml`
3. **Static Assets**: Configure static file serving
4. **SSL Certificate**: HTTPS configuration
5. **Process Management**: Gunicorn/uWSGI setup
6. **Monitoring**: Health check endpoints

### Production Features:
- **Health Monitoring**: `/api/health` endpoint
- **Error Logging**: Structured logging system
- **Session Management**: Database-backed sessions
- **Security Headers**: CORS and security middleware
- **Performance**: Connection pooling and caching

---

## 📊 System Metrics

### Current Data Scale:
- **Students**: 7,200 records across 72 batches
- **Teachers**: 94 with subject expertise mapping
- **Timetable Slots**: 3,888 active scheduling entries
- **Subjects**: 73 across multiple departments
- **Rooms**: 66 across 4 campuses
- **Activities**: 125 types of academic activities

### Performance Benchmarks:
- **ML Pipeline**: 4-6 seconds complete execution
- **Database Queries**: <100ms average response
- **API Endpoints**: <200ms average response
- **Page Load**: <2 seconds average load time

---

## 🔧 Development Workflow

### Local Development:
1. Clone repository
2. Install dependencies: `pip install -r requirements.txt`
3. Setup PostgreSQL database
4. Run migrations: `python -c "from app import db; db.create_all()"`
5. Start server: `python app_server.py`

### Testing:
```bash
python test_complete_system.py  # Complete system test
python main_pipeline.py         # ML pipeline test
```

### Code Structure Guidelines:
- **Routes**: Business logic separation by user role
- **Models**: SQLAlchemy ORM with proper relationships
- **Templates**: Jinja2 with template inheritance
- **Static**: Organized CSS/JS with minification
- **Pipeline**: Modular ML components with clear interfaces

---

## 📈 Future Enhancements

### Planned Features:
- **Mobile App**: React Native implementation
- **Real-Time Notifications**: WebSocket integration
- **Advanced Analytics**: Detailed reporting dashboards
- **Multi-Language**: Hindi/English interface
- **Calendar Integration**: Google Calendar sync
- **Automated Testing**: Complete test suite coverage

### Scalability Considerations:
- **Microservices**: Component separation for scaling
- **Caching**: Redis implementation for performance
- **Load Balancing**: Multi-instance deployment
- **Database Sharding**: Large-scale data handling
- **CDN Integration**: Static asset optimization

---

## 📞 Support & Maintenance

### Documentation Updates:
- Regular feature documentation updates
- API changelog maintenance
- Performance metric tracking
- User feedback integration

### Monitoring:
- **Application Logs**: Centralized logging system
- **Performance Metrics**: Response time tracking
- **Error Tracking**: Exception monitoring
- **User Analytics**: Usage pattern analysis

---

**Last Updated**: June 27, 2025
**Version**: 1.0.0
**Status**: Production Ready