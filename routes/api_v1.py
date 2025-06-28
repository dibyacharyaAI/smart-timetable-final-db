"""
Smart Timetable API v1
Comprehensive API endpoints for the Smart Timetable Management System
Based on API documentation requirements
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from models import db, User, TimetableSlot, TimetableHistory
from datetime import datetime, timedelta
import pandas as pd
import jwt
from functools import wraps
import os

api_v1 = Blueprint('api_v1', __name__, url_prefix='/api')

def api_auth_required(f):
    """API authentication decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'success': False, 'message': 'Invalid authorization header format'}), 401
        
        if not token:
            return jsonify({'success': False, 'message': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, current_app.config.get('SECRET_KEY', 'fallback-secret'), algorithms=['HS256'])
            current_api_user = User.query.get(data['user_id'])
            if not current_api_user:
                return jsonify({'success': False, 'message': 'Invalid token'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Invalid token'}), 401
        
        return f(current_api_user, *args, **kwargs)
    return decorated_function

def admin_required(f):
    """Admin role requirement decorator"""
    @wraps(f)
    def decorated_function(current_api_user, *args, **kwargs):
        if current_api_user.role != 'admin':
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        return f(current_api_user, *args, **kwargs)
    return decorated_function

def teacher_required(f):
    """Teacher role requirement decorator"""
    @wraps(f)
    def decorated_function(current_api_user, *args, **kwargs):
        if current_api_user.role not in ['teacher', 'admin']:
            return jsonify({'success': False, 'message': 'Teacher access required'}), 403
        return f(current_api_user, *args, **kwargs)
    return decorated_function

# ============================================================================
# 1. Authentication APIs
# ============================================================================

@api_v1.route('/auth/login', methods=['POST'])
def api_login():
    """API Login endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        email = data.get('email')
        password = data.get('password')
        role = data.get('role')
        
        if not all([email, password, role]):
            return jsonify({'success': False, 'message': 'Email, password, and role are required'}), 400
        
        # Find user by email and role
        user = User.query.filter_by(email=email, role=role).first()
        
        if not user or not user.check_password(password):
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        
        # Generate JWT token
        token_payload = {
            'user_id': user.id,
            'email': user.email,
            'role': user.role,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        
        token = jwt.encode(token_payload, current_app.config.get('SECRET_KEY', 'fallback-secret'), algorithm='HS256')
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'token': token,
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'name': user.full_name,
                    'role': user.role,
                    'studentId': user.student_id,
                    'teacherId': user.teacher_id,
                    'section': user.section,
                    'department': user.department,
                    'phone': user.phone,
                    'campus': user.campus
                },
                'expiresIn': 86400
            },
            'message': 'Login successful'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_v1.route('/auth/refresh', methods=['POST'])
@api_auth_required
def api_refresh_token(current_api_user):
    """Refresh authentication token"""
    try:
        token_payload = {
            'user_id': current_api_user.id,
            'email': current_api_user.email,
            'role': current_api_user.role,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        
        token = jwt.encode(token_payload, current_app.config.get('SECRET_KEY', 'fallback-secret'), algorithm='HS256')
        
        return jsonify({
            'success': True,
            'data': {
                'token': token,
                'expiresIn': 86400
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_v1.route('/auth/logout', methods=['POST'])
@api_auth_required
def api_logout(current_api_user):
    """Logout endpoint"""
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    }), 200

# ============================================================================
# 2. Event/Timetable APIs
# ============================================================================

@api_v1.route('/events', methods=['GET'])
@api_auth_required
def get_events(current_api_user):
    """Get all events based on user role and filters"""
    try:
        # Get query parameters
        section = request.args.get('section')
        teacher_id = request.args.get('teacherId')
        campus = request.args.get('campus')
        event_type = request.args.get('type')
        day = request.args.get('day')
        start_date = request.args.get('startDate')
        end_date = request.args.get('endDate')
        
        # Base query
        query = TimetableSlot.query.filter_by(is_active=True)
        
        # Apply role-based filtering
        if current_api_user.role == 'student':
            query = query.filter_by(
                batch_id=current_api_user.batch_id,
                section=current_api_user.section
            )
        elif current_api_user.role == 'teacher':
            query = query.filter_by(teacher_id=current_api_user.teacher_id)
        
        # Apply filters
        if section:
            query = query.filter_by(section=section)
        if teacher_id:
            query = query.filter_by(teacher_id=teacher_id)
        if campus:
            query = query.filter_by(campus=campus)
        if event_type:
            query = query.filter_by(activity_type=event_type)
        if day:
            query = query.filter_by(day=day)
        
        slots = query.all()
        
        events = []
        for slot in slots:
            # Map day name to number (0=Monday)
            day_mapping = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6}
            day_num = day_mapping.get(slot.day, 0)
            
            # Parse time
            start_hour = int(slot.time_start.split(':')[0])
            end_hour = int(slot.time_end.split(':')[0])
            
            event = {
                'id': slot.id,
                'section': slot.section,
                'scheme': slot.scheme,
                'title': slot.subject_name,
                'day': day_num,
                'startHour': start_hour,
                'endHour': end_hour,
                'type': slot.activity_type.lower(),
                'room': slot.room_name,
                'campus': slot.campus,
                'teacher': slot.teacher_name,
                'teacherId': slot.teacher_id,
                'color': 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-100',
                'createdAt': slot.created_at.isoformat(),
                'updatedAt': slot.updated_at.isoformat()
            }
            events.append(event)
        
        return jsonify({
            'success': True,
            'data': {
                'events': events,
                'totalCount': len(events),
                'filteredCount': len(events)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_v1.route('/events/<int:event_id>', methods=['GET'])
@api_auth_required
def get_event_by_id(current_api_user, event_id):
    """Get specific event by ID"""
    try:
        slot = TimetableSlot.query.get_or_404(event_id)
        
        # Check access permissions
        if current_api_user.role == 'student':
            if slot.batch_id != current_api_user.batch_id or slot.section != current_api_user.section:
                return jsonify({'success': False, 'message': 'Access denied'}), 403
        elif current_api_user.role == 'teacher':
            if slot.teacher_id != current_api_user.teacher_id:
                return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Map day name to number
        day_mapping = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6}
        day_num = day_mapping.get(slot.day, 0)
        
        start_hour = int(slot.time_start.split(':')[0])
        end_hour = int(slot.time_end.split(':')[0])
        
        event = {
            'id': slot.id,
            'section': slot.section,
            'scheme': slot.scheme,
            'title': slot.subject_name,
            'day': day_num,
            'startHour': start_hour,
            'endHour': end_hour,
            'type': slot.activity_type.lower(),
            'room': slot.room_name,
            'campus': slot.campus,
            'teacher': slot.teacher_name,
            'teacherId': slot.teacher_id,
            'color': 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-100',
            'description': f"{slot.subject_name} - {slot.activity_type}",
            'createdAt': slot.created_at.isoformat(),
            'updatedAt': slot.updated_at.isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': event
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_v1.route('/events', methods=['POST'])
@api_auth_required
@admin_required
def create_event(current_api_user):
    """Create new timetable event (Admin only)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        # Map day number to name
        day_mapping = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
        day_name = day_mapping.get(data.get('day', 0), 'Monday')
        
        # Create new slot
        slot = TimetableSlot()
        slot.batch_id = data.get('section', 'A01')  # Default batch based on section
        slot.section = data.get('section')
        slot.day = day_name
        slot.time_start = f"{data.get('startHour', 8):02d}:00"
        slot.time_end = f"{data.get('endHour', 9):02d}:00"
        slot.subject_name = data.get('title')
        slot.teacher_name = data.get('teacher', 'TBD')
        slot.teacher_id = data.get('teacherId', 'TBD')
        slot.room_name = data.get('room')
        slot.campus = data.get('campus')
        slot.activity_type = data.get('type', 'theory').title()
        slot.department = data.get('department', 'General')
        slot.scheme = data.get('scheme', 'A')
        slot.created_by = current_api_user.id
        slot.is_active = True
        slot.version = 1
        
        db.session.add(slot)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': slot.id,
                'section': slot.section,
                'scheme': slot.scheme,
                'title': slot.subject_name,
                'day': data.get('day', 0),
                'startHour': data.get('startHour', 8),
                'endHour': data.get('endHour', 9),
                'type': slot.activity_type.lower(),
                'room': slot.room_name,
                'campus': slot.campus,
                'teacher': slot.teacher_name,
                'teacherId': slot.teacher_id,
                'color': data.get('color', 'bg-blue-100 text-blue-800'),
                'createdAt': slot.created_at.isoformat(),
                'updatedAt': slot.updated_at.isoformat()
            },
            'message': 'Event created successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_v1.route('/events/<int:event_id>', methods=['PUT'])
@api_auth_required
@admin_required
def update_event(current_api_user, event_id):
    """Update existing event (Admin only)"""
    try:
        slot = TimetableSlot.query.get_or_404(event_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        # Update fields
        if 'title' in data:
            slot.subject_name = data['title']
        if 'day' in data:
            day_mapping = {0: 'Monday', 1: 'Tuesday', 2: 'Wednesday', 3: 'Thursday', 4: 'Friday', 5: 'Saturday', 6: 'Sunday'}
            slot.day = day_mapping.get(data['day'], 'Monday')
        if 'startHour' in data:
            slot.time_start = f"{data['startHour']:02d}:00"
        if 'endHour' in data:
            slot.time_end = f"{data['endHour']:02d}:00"
        if 'type' in data:
            slot.activity_type = data['type'].title()
        if 'room' in data:
            slot.room_name = data['room']
        if 'campus' in data:
            slot.campus = data['campus']
        if 'teacherId' in data:
            slot.teacher_id = data['teacherId']
        
        slot.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Map day name back to number
        day_mapping = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6}
        day_num = day_mapping.get(slot.day, 0)
        
        return jsonify({
            'success': True,
            'data': {
                'id': slot.id,
                'section': slot.section,
                'scheme': slot.scheme,
                'title': slot.subject_name,
                'day': day_num,
                'startHour': int(slot.time_start.split(':')[0]),
                'endHour': int(slot.time_end.split(':')[0]),
                'type': slot.activity_type.lower(),
                'room': slot.room_name,
                'campus': slot.campus,
                'teacher': slot.teacher_name,
                'teacherId': slot.teacher_id,
                'color': data.get('color', 'bg-blue-100 text-blue-800'),
                'updatedAt': slot.updated_at.isoformat()
            },
            'message': 'Event updated successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_v1.route('/events/<int:event_id>', methods=['DELETE'])
@api_auth_required
@admin_required
def delete_event(current_api_user, event_id):
    """Delete event (Admin only)"""
    try:
        slot = TimetableSlot.query.get_or_404(event_id)
        slot.is_active = False  # Soft delete
        slot.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Event deleted successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_v1.route('/events/swap', methods=['POST'])
@api_auth_required
@teacher_required
def swap_events(current_api_user):
    """Swap two events in the timetable"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        source_id = data.get('sourceEventId')
        target_id = data.get('targetEventId')
        reason = data.get('reason', 'Manual swap')
        
        if not source_id or not target_id:
            return jsonify({'success': False, 'message': 'Source and target event IDs required'}), 400
        
        source_slot = TimetableSlot.query.get_or_404(source_id)
        target_slot = TimetableSlot.query.get_or_404(target_id)
        
        # Check permissions
        if current_api_user.role == 'teacher':
            if (source_slot.teacher_id != current_api_user.teacher_id and 
                target_slot.teacher_id != current_api_user.teacher_id):
                return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Swap time slots
        temp_day = source_slot.day
        temp_start = source_slot.time_start
        temp_end = source_slot.time_end
        
        source_slot.day = target_slot.day
        source_slot.time_start = target_slot.time_start
        source_slot.time_end = target_slot.time_end
        
        target_slot.day = temp_day
        target_slot.time_start = temp_start
        target_slot.time_end = temp_end
        
        # Update timestamps
        source_slot.updated_at = datetime.utcnow()
        target_slot.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Map day names to numbers for response
        day_mapping = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6}
        
        return jsonify({
            'success': True,
            'data': {
                'swappedEvents': [
                    {
                        'id': source_slot.id,
                        'newTimeSlot': {
                            'day': day_mapping.get(source_slot.day, 0),
                            'startHour': int(source_slot.time_start.split(':')[0]),
                            'endHour': int(source_slot.time_end.split(':')[0])
                        }
                    },
                    {
                        'id': target_slot.id,
                        'newTimeSlot': {
                            'day': day_mapping.get(target_slot.day, 0),
                            'startHour': int(target_slot.time_start.split(':')[0]),
                            'endHour': int(target_slot.time_end.split(':')[0])
                        }
                    }
                ]
            },
            'message': 'Events swapped successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================================
# 3. User Management APIs
# ============================================================================

@api_v1.route('/users/profile', methods=['GET'])
@api_auth_required
def get_user_profile(current_api_user):
    """Get current user's profile"""
    try:
        profile = {
            'id': str(current_api_user.id),
            'name': current_api_user.full_name,
            'email': current_api_user.email,
            'role': current_api_user.role,
            'phone': current_api_user.phone,
            'studentId': current_api_user.student_id,
            'section': current_api_user.section,
            'teacherId': current_api_user.teacher_id,
            'department': current_api_user.department,
            'campus': current_api_user.campus,
            'batch': current_api_user.batch_id
        }
        
        return jsonify({
            'success': True,
            'data': profile
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_v1.route('/users/profile', methods=['PUT'])
@api_auth_required
def update_user_profile(current_api_user):
    """Update user profile"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
        
        # Update allowed fields
        if 'name' in data:
            current_api_user.full_name = data['name']
        if 'phone' in data:
            current_api_user.phone = data['phone']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'id': str(current_api_user.id),
                'name': current_api_user.full_name,
                'email': current_api_user.email,
                'phone': current_api_user.phone,
                'updatedAt': datetime.utcnow().isoformat()
            },
            'message': 'Profile updated successfully'
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api_v1.route('/users', methods=['GET'])
@api_auth_required
@admin_required
def get_all_users(current_api_user):
    """Get all users (Admin only)"""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        role_filter = request.args.get('role')
        department_filter = request.args.get('department')
        
        query = User.query.filter_by(active_status=True)
        
        if role_filter:
            query = query.filter_by(role=role_filter)
        if department_filter:
            query = query.filter_by(department=department_filter)
        
        users = query.paginate(page=page, per_page=limit, error_out=False)
        
        user_list = []
        for user in users.items:
            user_list.append({
                'id': str(user.id),
                'name': user.full_name,
                'email': user.email,
                'role': user.role,
                'department': user.department,
                'section': user.section,
                'isActive': user.active_status,
                'lastLogin': user.last_login.isoformat() if user.last_login else None
            })
        
        return jsonify({
            'success': True,
            'data': {
                'users': user_list,
                'pagination': {
                    'currentPage': page,
                    'totalPages': users.pages,
                    'totalItems': users.total,
                    'itemsPerPage': limit
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================================
# 4. Teacher-Specific APIs
# ============================================================================

@api_v1.route('/teachers/<teacher_id>/schedule', methods=['GET'])
@api_auth_required
def get_teacher_schedule(current_api_user, teacher_id):
    """Get schedule for specific teacher"""
    try:
        # Check permissions
        if current_api_user.role == 'teacher' and current_api_user.teacher_id != teacher_id:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        slots = TimetableSlot.query.filter_by(
            teacher_id=teacher_id,
            is_active=True
        ).all()
        
        schedule = []
        total_hours = 0
        
        for slot in slots:
            day_mapping = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6}
            start_hour = int(slot.time_start.split(':')[0])
            end_hour = int(slot.time_end.split(':')[0])
            
            schedule.append({
                'id': slot.id,
                'title': slot.subject_name,
                'section': slot.section,
                'day': day_mapping.get(slot.day, 0),
                'startHour': start_hour,
                'endHour': end_hour,
                'room': slot.room_name,
                'campus': slot.campus,
                'type': slot.activity_type.lower()
            })
            
            total_hours += (end_hour - start_hour)
        
        teacher_name = slots[0].teacher_name if slots else "Unknown"
        
        return jsonify({
            'success': True,
            'data': {
                'teacherId': teacher_id,
                'teacherName': teacher_name,
                'schedule': schedule,
                'totalHours': total_hours,
                'totalClasses': len(schedule)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================================
# 5. Student-Specific APIs  
# ============================================================================

@api_v1.route('/students/schedule', methods=['GET'])
@api_auth_required
def get_student_schedule(current_api_user):
    """Get schedule for current student"""
    try:
        if current_api_user.role != 'student':
            return jsonify({'success': False, 'message': 'Student access required'}), 403
        
        slots = TimetableSlot.query.filter_by(
            batch_id=current_api_user.batch_id,
            section=current_api_user.section,
            is_active=True
        ).all()
        
        schedule = []
        for slot in slots:
            day_mapping = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6}
            
            schedule.append({
                'id': slot.id,
                'title': slot.subject_name,
                'day': day_mapping.get(slot.day, 0),
                'startHour': int(slot.time_start.split(':')[0]),
                'endHour': int(slot.time_end.split(':')[0]),
                'teacher': slot.teacher_name,
                'teacherId': slot.teacher_id,
                'room': slot.room_name,
                'campus': slot.campus,
                'type': slot.activity_type.lower()
            })
        
        return jsonify({
            'success': True,
            'data': {
                'studentId': current_api_user.student_id,
                'section': current_api_user.section,
                'batch': current_api_user.batch_id,
                'schedule': schedule,
                'totalClasses': len(schedule)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================================
# 6. System APIs
# ============================================================================

@api_v1.route('/health', methods=['GET'])
def health_check():
    """System health check"""
    return jsonify({
        'success': True,
        'data': {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }
    }), 200

@api_v1.route('/stats', methods=['GET'])
@api_auth_required
@admin_required
def get_system_stats(current_api_user):
    """Get system statistics"""
    try:
        stats = {
            'totalUsers': User.query.filter_by(active_status=True).count(),
            'totalStudents': User.query.filter_by(role='student', active_status=True).count(),
            'totalTeachers': User.query.filter_by(role='teacher', active_status=True).count(),
            'totalEvents': TimetableSlot.query.filter_by(is_active=True).count(),
            'totalSections': len(set([u.section for u in User.query.filter_by(role='student').all() if u.section])),
            'activeCampuses': ['Campus-3', 'Campus-8', 'Campus-15B', 'Campus-17']
        }
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# Error handlers
@api_v1.errorhandler(404)
def not_found_error(error):
    return jsonify({
        'success': False,
        'message': 'Endpoint not found'
    }), 404

@api_v1.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500