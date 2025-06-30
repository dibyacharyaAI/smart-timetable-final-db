# Smart Timetable Management System

> AI-Powered Academic Scheduling Platform with Multi-User Portals

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1+-green.svg)](https://flask.palletsprojects.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-blue.svg)](https://postgresql.org)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org)

## 🎯 Overview

Smart Timetable Management System एक comprehensive academic scheduling platform है जो AI-powered optimization के साथ multi-user portal functionality provide करता है। यह system RNN Autoencoder और OR-Tools constraint solving का उपयोग करके intelligent timetable generation और real-time optimization प्रदान करता है।

### Key Features
- **AI-Powered Optimization**: RNN Autoencoder + OR-Tools constraint solving
- **Multi-User Portals**: Admin, Teacher, Student के लिए अलग interface
- **Real-Time Editing**: Interactive timetable editing with ML validation
- **Export Capabilities**: CSV/Excel downloads with role-based filtering
- **RESTful APIs**: JWT authentication के साथ complete API system
- **Responsive Design**: Bootstrap 5 के साथ mobile-friendly interface

## 🚀 Quick Start

### Prerequisites
- Python 3.11 या उससे ऊपर
- PostgreSQL 12+
- Git

### Installation

1. **Repository Clone करें**
```bash
git clone https://github.com/dibyacharyaAI/smart-timetable-final-db.git
cd smart-timetable-system
```

2. **Virtual Environment Setup करें**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# या
venv\Scripts\activate     # Windows
```

3. **Dependencies Install करें**
```bash
pip install -r requirements.txt
```

4. **PostgreSQL Database Setup करें**
```bash
# PostgreSQL में database create करें
createdb smart_timetable

# Environment variables set करें
SQLALCHEMY_DATABASE_URI=postgresql://postgres:12345@localhost:5432/smart_timetable
export FLASK_SECRET_KEY="your-secret-key-here"
export JWT_SECRET_KEY="your-jwt-secret-here"
```

5. **Database Tables Create करें**
```bash
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

6. **Application Start करें**
```bash
python app_server.py
```

Application अब `http://localhost:5000` पर running होगा।

## 📊 System Data

### Pre-loaded Academic Data
- **7,200 Students** across 72 batches (36 Scheme-A + 36 Scheme-B)
- **94 Teachers** with subject expertise mapping
- **73 Subjects** across multiple departments  
- **66 Rooms** across 4 campuses
- **125 Activities** covering lectures, labs, tutorials
- **864 Time Slots** with comprehensive scheduling coverage

### Sample Login Credentials
```
Admin User:
Username: admin
Password: admin123

Teacher User: 
use data from teacher.csv

Student User:
use data from student.csv

```

## 🔧 Configuration

### Environment Variables
```bash
# Required
DATABASE_URL=postgresql://user:pass@host:port/dbname
FLASK_SECRET_KEY=your-flask-secret-key
JWT_SECRET_KEY=your-jwt-secret-key

# Optional
FLASK_ENV=development
DEBUG=True
```

### Database Configuration
```python
# config.py में database settings
SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
}
```

## 🧠 ML Pipeline Usage

### Complete Pipeline Run करें
```bash
python main_pipeline.py
```

### Individual Components Test करें
```bash
# Encoding test
python pipeline/encoding.py

# Training test  
python pipeline/training.py

# Anomaly detection test
python pipeline/anomaly_detection.py

# Constraint solver test
python pipeline/constraint_solver.py
```

### Pipeline Features
- **4-6 seconds** complete execution time
- **Real-time anomaly detection** on edits
- **Automatic constraint resolution**
- **Self-healing algorithms** for corrupted data

## 📡 API Usage

### Authentication
```bash
# Login और JWT token प्राप्त करें
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

### Timetable Operations
```bash
# All events प्राप्त करें (Token required)
curl -X GET http://localhost:5000/api/events \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Specific event प्राप्त करें
curl -X GET http://localhost:5000/api/events/1 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# New event create करें (Admin only)
curl -X POST http://localhost:5000/api/events \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_code": "CS101",
    "teacher_id": "TCH1001", 
    "room_id": "R001",
    "day": "Monday",
    "time_start": "09:00",
    "time_end": "10:00"
  }'
```

### System Health Check
```bash
curl -X GET http://localhost:5000/api/health
```

### Complete API Documentation
API endpoints की complete list और examples के लिए `API_ENDPOINTS.md` देखें।

## 👥 User Portals

### Admin Portal Features
- **Complete System Control**: User management, system configuration
- **Smart Timetable Generation**: AI-powered schedule creation
- **Analytics Dashboard**: System metrics और reporting
- **Bulk Operations**: CSV import/export, batch processing
- **ML Pipeline Monitoring**: Real-time pipeline status

### Teacher Portal Features  
- **Personal Schedule Management**: View और edit personal timetable
- **Interactive Editing**: Real-time slot modifications with ML validation
- **Student Information**: Access to assigned students और classes
- **Download Options**: CSV/Excel exports of personal schedules
- **Room Management**: Room assignment modifications

### Student Portal Features
- **Read-Only Access**: Personal timetable viewing
- **Teacher Information**: Contact details और office hours
- **Subject Details**: Course information और schedules
- **Personal Downloads**: Individual schedule exports
- **Class Notifications**: Important updates और announcements

## 🧪 Testing

### Complete System Test
```bash
python test_complete_system.py
```

### Expected Output
```
🎯 SYSTEM TEST SUMMARY
DATABASE             ✅ PASS
DATA_FILES           ✅ PASS  
PIPELINE_MODELS      ✅ PASS
ML_PIPELINE          ✅ PASS
WEB_ENDPOINTS        ✅ PASS
TOTAL: 5/5 tests passed
🎉 ALL TESTS PASSED - SYSTEM READY!
```

### Individual Component Testing
```bash
# Database connectivity
python -c "from app import db; print('Database connected!' if db else 'Failed')"

# Data files validation
ls data/*.csv | wc -l  # Should show 6 files

# ML models check
ls pipeline/models/*.* | wc -l  # Should show 3+ model files
```

## 📁 Project Structure

```
smart-timetable-system/
├── app.py                      # Main Flask application
├── app_server.py              # Production server
├── models.py                  # Database models
├── main_pipeline.py           # ML pipeline orchestrator
├── requirements.txt           # Python dependencies
├── routes/                    # API route handlers
│   ├── admin.py              # Admin portal routes
│   ├── teacher.py            # Teacher portal routes  
│   ├── student.py            # Student portal routes
│   ├── auth.py               # Authentication routes
│   └── api.py                # RESTful API endpoints
├── templates/                 # HTML templates
│   ├── admin/                # Admin portal templates
│   ├── teacher/              # Teacher portal templates
│   └── student/              # Student portal templates
├── static/                    # CSS, JS, images
├── pipeline/                  # ML components
│   ├── encoding.py           # Feature encoding
│   ├── training.py           # Model training
│   ├── anomaly_detection.py  # Anomaly detection
│   ├── constraint_solver.py  # Optimization
│   └── models/               # Trained models
├── data/                      # CSV datasets
│   ├── students.csv          # Student records
│   ├── teachers.csv          # Teacher profiles
│   ├── subjects.csv          # Subject catalog
│   ├── rooms.csv             # Room assignments
│   ├── activities.csv        # Activity types
│   └── slot_index.csv        # Time slot mappings
└── docs/                      # Documentation
    ├── PROJECT_DOCUMENTATION.md
    └── API_ENDPOINTS.md
```

## 🔄 Development Workflow

### Local Development Setup
```bash
# Development mode में run करें
export FLASK_ENV=development
export DEBUG=True
python app_server.py
```

### Code Quality
```bash
# Code formatting
black *.py routes/*.py pipeline/*.py

# Type checking  
mypy app.py routes/ pipeline/

# Testing
pytest tests/
```

### Database Migration
```bash
# New migration create करें
flask db migrate -m "Description of changes"

# Migration apply करें
flask db upgrade
```

## 🚀 Production Deployment

### Docker Deployment
```bash
# Docker image build करें
docker build -t smart-timetable .

# Container run करें
docker run -p 5000:5000 \
  -e DATABASE_URL=your_database_url \
  -e FLASK_SECRET_KEY=your_secret_key \
  smart-timetable
```

### Manual Deployment
```bash
# Production dependencies install करें
pip install gunicorn

# Production server start करें
gunicorn -w 4 -b 0.0.0.0:5000 app_server:app
```

### Environment Setup
```bash
# Production environment variables
export FLASK_ENV=production
export DEBUG=False
export DATABASE_URL=postgresql://prod_user:pass@host:port/prod_db
```

## 📊 Performance Metrics

### Current Benchmarks
- **ML Pipeline**: 4-6 seconds complete execution
- **Database Queries**: <100ms average response
- **API Endpoints**: <200ms average response  
- **Page Load Time**: <2 seconds average
- **Concurrent Users**: 100+ supported

### System Requirements
- **Minimum**: 2GB RAM, 20GB storage
- **Recommended**: 4GB RAM, 50GB storage
- **Production**: 8GB RAM, 100GB storage

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check PostgreSQL service
sudo service postgresql status

# Check connection string
echo $DATABASE_URL
```

**Import Error for ML Components**
```bash
# Install missing dependencies
pip install torch scikit-learn ortools

# Check Python path
python -c "import sys; print(sys.path)"
```

**Port Already in Use**
```bash
# Find process using port 5000
lsof -i :5000

# Kill process
kill -9 PID
```

### Debug Mode
```bash
# Enable debug logging
export FLASK_DEBUG=True
export LOG_LEVEL=DEBUG
python app_server.py
```

## 📚 Documentation

### Complete Documentation
- [Project Documentation](PROJECT_DOCUMENTATION.md) - Complete system overview
- [API Documentation](API_ENDPOINTS.md) - RESTful API reference
- [ML Pipeline Guide](pipeline/README.md) - Machine learning components

### Key Features Documentation
- **User Authentication**: Flask-Login + JWT implementation
- **Database Design**: SQLAlchemy models और relationships
- **ML Pipeline**: PyTorch autoencoder + OR-Tools optimization
- **API Design**: RESTful endpoints with role-based access

## 🤝 Contributing

### Development Setup
```bash
# Repository fork करें
git clone https://github.com/dibyacharyaAI/smart-timetable-final-db.git

# Feature branch create करें
git checkout -b feature/your-feature-name

# Changes commit करें
git commit -m "Add your feature description"

# Pull request submit करें
git push origin feature/your-feature-name
```

### Code Standards
- **Python**: PEP 8 compliance
- **Documentation**: Docstrings for all functions
- **Testing**: Unit tests for new features
- **Git**: Conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Authors

- **Development Team** - Initial work and ongoing maintenance
- **AI Integration** - Machine learning pipeline development
- **Frontend Design** - User interface और experience

## 🙏 Acknowledgments

- **Flask Community** - Web framework support
- **PyTorch Team** - Machine learning framework
- **Bootstrap** - Frontend UI components
- **PostgreSQL** - Database system
- **OR-Tools** - Constraint optimization library

## 📞 Support

### Getting Help
- **Issues**: GitHub Issues for bug reports
- **Documentation**: Check PROJECT_DOCUMENTATION.md
- **API Questions**: Refer to API_ENDPOINTS.md
- **Performance**: Review system requirements

### Contact Information
- **Project Repository**: https://github.com/dibyacharyaAI/smart-timetable-final-db
- **Documentation**: Available in docs/ directory
- **API Testing**: Use provided curl examples

---

**Built with ❤️ for Academic Institutions**

**Version**: 1.0.0 | **Status**: Production Ready | **Last Updated**: June 27, 2025
