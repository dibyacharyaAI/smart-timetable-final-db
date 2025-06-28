from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, teacher, student
    full_name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(15))
    
    # Role-specific IDs
    teacher_id = db.Column(db.String(20), nullable=True)  # TCH1001 etc
    student_id = db.Column(db.String(20), nullable=True)  # STU220001 etc
    
    # Additional fields
    department = db.Column(db.String(100))
    batch_id = db.Column(db.String(10))
    section = db.Column(db.String(10))
    campus = db.Column(db.String(50))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    active_status = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'full_name': self.full_name,
            'teacher_id': self.teacher_id,
            'student_id': self.student_id,
            'department': self.department,
            'batch_id': self.batch_id,
            'section': self.section,
            'campus': self.campus,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.active_status
        }

class TimetableSlot(db.Model):
    __tablename__ = 'timetable_slots'
    
    id = db.Column(db.Integer, primary_key=True)
    slot_index = db.Column(db.Integer, nullable=False)
    batch_id = db.Column(db.String(10), nullable=False)
    section = db.Column(db.String(10), nullable=False)
    day = db.Column(db.String(10), nullable=False)
    time_start = db.Column(db.String(10), nullable=False)
    time_end = db.Column(db.String(10), nullable=False)
    subject_code = db.Column(db.String(20), nullable=False)
    subject_name = db.Column(db.String(200), nullable=False)
    teacher_id = db.Column(db.String(20), nullable=False)
    teacher_name = db.Column(db.String(200), nullable=False)
    room_id = db.Column(db.String(20), nullable=False)
    room_name = db.Column(db.String(100), nullable=False)
    campus = db.Column(db.String(50), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)  # Lecture, Lab, Tutorial
    department = db.Column(db.String(100), nullable=False)
    scheme = db.Column(db.String(10), nullable=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True)
    version = db.Column(db.Integer, default=1)
    
    def to_dict(self):
        return {
            'id': self.id,
            'slot_index': self.slot_index,
            'batch_id': self.batch_id,
            'section': self.section,
            'day': self.day,
            'time_start': self.time_start,
            'time_end': self.time_end,
            'subject_code': self.subject_code,
            'subject_name': self.subject_name,
            'teacher_id': self.teacher_id,
            'teacher_name': self.teacher_name,
            'room_id': self.room_id,
            'room_name': self.room_name,
            'campus': self.campus,
            'activity_type': self.activity_type,
            'department': self.department,
            'scheme': self.scheme,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'version': self.version
        }

class TimetableHistory(db.Model):
    __tablename__ = 'timetable_history'
    
    id = db.Column(db.Integer, primary_key=True)
    timetable_data = db.Column(db.Text, nullable=False)  # JSON data
    version = db.Column(db.Integer, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text)
    total_slots = db.Column(db.Integer)
    affected_batches = db.Column(db.Text)  # JSON array
    
class DataImportLog(db.Model):
    __tablename__ = 'data_import_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    file_type = db.Column(db.String(50), nullable=False)  # students, teachers, etc
    file_path = db.Column(db.String(500), nullable=False)
    records_imported = db.Column(db.Integer)
    import_status = db.Column(db.String(20), default='pending')
    error_message = db.Column(db.Text)
    imported_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    imported_at = db.Column(db.DateTime, default=datetime.utcnow)

class SystemConfig(db.Model):
    __tablename__ = 'system_config'
    
    id = db.Column(db.Integer, primary_key=True)
    config_key = db.Column(db.String(100), unique=True, nullable=False)
    config_value = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)