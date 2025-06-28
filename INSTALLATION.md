# Smart Timetable Management System - Installation Guide

## Quick Setup

### 1. Extract Files
```bash
unzip smart-timetable-production.zip
cd smart-timetable-production
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Database
```bash
# Create PostgreSQL database
createdb smart_timetable

# Set environment variables
export DATABASE_URL="postgresql://username:password@localhost:5432/smart_timetable"
export FLASK_SECRET_KEY="your-secret-key-here"
export JWT_SECRET_KEY="your-jwt-secret-here"
```

### 4. Initialize Database
```bash
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

### 5. Start Application
```bash
python app_server.py
```

Application will run on: http://localhost:5000

## Default Login Credentials
- Admin: admin / admin123
- Teacher: teacher1 / teacher123  
- Student: student1 / student123

## Test System
```bash
python test_complete_system.py
```

Expected: 5/5 tests passed

## Production Deployment
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app_server:app
```

For complete documentation, see README.md and PROJECT_DOCUMENTATION.md