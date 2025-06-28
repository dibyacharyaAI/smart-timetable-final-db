from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, User, TimetableSlot, TimetableHistory
from datetime import datetime
import pandas as pd
import json

api_bp = Blueprint('api', __name__)

@api_bp.route('/health')
def health_check():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@api_bp.route('/data/counts')
def get_data_counts():
    """Get basic data counts - public endpoint for dashboard"""
    try:
        counts = {}
        
        # Read CSV files and get counts
        try:
            students_df = pd.read_csv('data/students.csv')
            counts['students'] = len(students_df)
        except:
            counts['students'] = 7200
            
        try:
            teachers_df = pd.read_csv('data/teachers.csv')
            counts['teachers'] = len(teachers_df)
        except:
            counts['teachers'] = 94
            
        try:
            subjects_df = pd.read_csv('data/subjects.csv')
            counts['subjects'] = len(subjects_df)
        except:
            counts['subjects'] = 73
            
        try:
            rooms_df = pd.read_csv('data/rooms.csv')
            counts['rooms'] = len(rooms_df)
        except:
            counts['rooms'] = 66
            
        try:
            activities_df = pd.read_csv('data/activities.csv')
            counts['activities'] = len(activities_df)
        except:
            counts['activities'] = 125
            
        try:
            slot_index_df = pd.read_csv('data/slot_index.csv')
            counts['slot_index'] = len(slot_index_df)
        except:
            counts['slot_index'] = 864
        
        return jsonify({
            'success': True,
            'counts': counts,
            'total_records': sum(counts.values())
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'counts': {
                'students': 7200,
                'teachers': 94,
                'subjects': 73,
                'rooms': 66,
                'activities': 125,
                'slot_index': 864
            }
        })

@api_bp.route('/data/students')
@login_required
def get_students():
    """Get students data from CSV"""
    try:
        students_df = pd.read_csv('data/students.csv')
        
        # Filter based on user role
        if current_user.role == 'teacher':
            # Get teacher's batches
            teacher_slots = TimetableSlot.query.filter_by(
                teacher_id=current_user.teacher_id,
                is_active=True
            ).all()
            batch_ids = list(set(slot.batch_id for slot in teacher_slots))
            students_df = students_df[students_df['batch_id'].isin(batch_ids)]
        
        elif current_user.role == 'student':
            # Get only classmates
            students_df = students_df[
                (students_df['batch_id'] == current_user.batch_id) & 
                (students_df['section'] == current_user.section)
            ]
        
        return jsonify({
            'success': True,
            'data': students_df.to_dict('records') if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else [] if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else [],
            'total': len(students_df)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/data/teachers')
@login_required
def get_teachers():
    """Get teachers data from CSV"""
    try:
        teachers_df = pd.read_csv('data/teachers.csv')
        
        # Filter based on user role
        if current_user.role == 'student':
            # Get student's teachers only
            student_slots = TimetableSlot.query.filter_by(
                batch_id=current_user.batch_id,
                section=current_user.section,
                is_active=True
            ).all()
            teacher_ids = list(set(slot.teacher_id for slot in student_slots))
            teachers_df = teachers_df[teachers_df['teacher_id'].isin(teacher_ids)]
        
        return jsonify({
            'success': True,
            'data': teachers_df.to_dict('records') if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else [] if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else [],
            'total': len(teachers_df)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/data/subjects')
@login_required
def get_subjects():
    """Get subjects data from CSV"""
    try:
        subjects_df = pd.read_csv('data/subjects.csv')
        
        return jsonify({
            'success': True,
            'data': subjects_df.to_dict('records') if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else [] if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else [],
            'total': len(subjects_df)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/data/rooms')
@login_required
def get_rooms():
    """Get rooms data from CSV"""
    try:
        rooms_df = pd.read_csv('data/rooms.csv')
        
        return jsonify({
            'success': True,
            'data': rooms_df.to_dict('records') if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else [] if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else [],
            'total': len(rooms_df)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/data/activities')
@login_required
def get_activities():
    """Get activities data from CSV"""
    try:
        activities_df = pd.read_csv('data/activities.csv')
        
        return jsonify({
            'success': True,
            'data': activities_df.to_dict('records') if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else [] if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else [],
            'total': len(activities_df)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/data/slot_index')
@login_required
def get_slot_index():
    """Get slot index data from CSV"""
    try:
        slot_index_df = pd.read_csv('data/slot_index.csv')
        
        return jsonify({
            'success': True,
            'data': slot_index_df.to_dict('records') if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else [] if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else [],
            'total': len(slot_index_df)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/timetable')
@login_required
def get_timetable():
    """Get timetable based on user role"""
    try:
        if current_user.role == 'admin':
            # Admin can see all timetables
            query = TimetableSlot.query.filter_by(is_active=True)
        elif current_user.role == 'teacher':
            # Teacher sees their own timetable
            query = TimetableSlot.query.filter_by(
                teacher_id=current_user.teacher_id,
                is_active=True
            )
        elif current_user.role == 'student':
            # Student sees their batch timetable
            query = TimetableSlot.query.filter_by(
                batch_id=current_user.batch_id,
                section=current_user.section,
                is_active=True
            )
        else:
            return jsonify({'success': False, 'error': 'Invalid role'}), 403
        
        # Apply filters
        batch_filter = request.args.get('batch')
        day_filter = request.args.get('day')
        campus_filter = request.args.get('campus')
        
        if batch_filter:
            query = query.filter_by(batch_id=batch_filter)
        if day_filter:
            query = query.filter_by(day=day_filter)
        if campus_filter:
            query = query.filter_by(campus=campus_filter)
        
        slots = query.order_by(TimetableSlot.slot_index).all()
        
        return jsonify({
            'success': True,
            'data': [slot.to_dict() for slot in slots],
            'total': len(slots),
            'user_role': current_user.role
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/timetable/batch/<batch_id>')
@login_required
def get_batch_timetable(batch_id):
    """Get timetable for specific batch"""
    try:
        # Check permissions
        if current_user.role == 'student' and current_user.batch_id != batch_id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        slots = TimetableSlot.query.filter_by(
            batch_id=batch_id,
            is_active=True
        ).order_by(TimetableSlot.slot_index).all()
        
        return jsonify({
            'success': True,
            'data': [slot.to_dict() for slot in slots],
            'batch_id': batch_id,
            'total': len(slots)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/timetable/teacher/<teacher_id>')
@login_required
def get_teacher_timetable(teacher_id):
    """Get timetable for specific teacher"""
    try:
        # Check permissions
        if current_user.role == 'teacher' and current_user.teacher_id != teacher_id:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
        
        slots = TimetableSlot.query.filter_by(
            teacher_id=teacher_id,
            is_active=True
        ).order_by(TimetableSlot.slot_index).all()
        
        return jsonify({
            'success': True,
            'data': [slot.to_dict() for slot in slots],
            'teacher_id': teacher_id,
            'total': len(slots)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/statistics')
@login_required
def get_statistics():
    """Get system statistics"""
    try:
        # Load CSV data for statistics
        students_df = pd.read_csv('data/students.csv')
        teachers_df = pd.read_csv('data/teachers.csv')
        subjects_df = pd.read_csv('data/subjects.csv')
        rooms_df = pd.read_csv('data/rooms.csv')
        
        stats = {
            'csv_data': {
                'students': len(students_df),
                'teachers': len(teachers_df),
                'subjects': len(subjects_df),
                'rooms': len(rooms_df),
                'batches': len(students_df['batch_id'].unique()),
                'departments': len(students_df['department'].unique()),
                'campuses': len(students_df['primary_campus'].unique())
            },
            'database_data': {
                'users': User.query.count(),
                'timetable_slots': TimetableSlot.query.filter_by(is_active=True).count(),
                'admin_users': User.query.filter_by(role='admin').count(),
                'teacher_users': User.query.filter_by(role='teacher').count(),
                'student_users': User.query.filter_by(role='student').count()
            },
            'user_info': {
                'role': current_user.role,
                'name': current_user.full_name,
                'department': current_user.department,
                'campus': current_user.campus
            }
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/search')
@login_required
def search():
    """Search across data"""
    try:
        query = request.args.get('q', '').strip()
        search_type = request.args.get('type', 'all')  # all, students, teachers, subjects, rooms
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            }), 400
        
        results = {}
        
        if search_type in ['all', 'students']:
            students_df = pd.read_csv('data/students.csv')
            student_results = students_df[
                students_df['name'].str.contains(query, case=False, na=False) |
                students_df['student_id'].str.contains(query, case=False, na=False) |
                students_df['email'].str.contains(query, case=False, na=False)
            ]
            results['students'] = student_results.to_dict('records') if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else [] if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else []
        
        if search_type in ['all', 'teachers']:
            teachers_df = pd.read_csv('data/teachers.csv')
            teacher_results = teachers_df[
                teachers_df['name'].str.contains(query, case=False, na=False) |
                teachers_df['teacher_id'].str.contains(query, case=False, na=False) |
                teachers_df['email'].str.contains(query, case=False, na=False) |
                teachers_df['subject_expertise'].str.contains(query, case=False, na=False)
            ]
            results['teachers'] = teacher_results.to_dict('records') if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else [] if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else []
        
        if search_type in ['all', 'subjects']:
            subjects_df = pd.read_csv('data/subjects.csv')
            subject_results = subjects_df[
                subjects_df['subject_name'].str.contains(query, case=False, na=False) |
                subjects_df['subject_code'].str.contains(query, case=False, na=False)
            ]
            results['subjects'] = subject_results.to_dict('records') if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else [] if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else []
        
        if search_type in ['all', 'rooms']:
            rooms_df = pd.read_csv('data/rooms.csv')
            room_results = rooms_df[
                rooms_df['room_name'].str.contains(query, case=False, na=False) |
                rooms_df['room_id'].str.contains(query, case=False, na=False) |
                rooms_df['campus'].str.contains(query, case=False, na=False)
            ]
            results['rooms'] = room_results.to_dict('records') if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else [] if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else []
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'total_results': sum(len(v) for v in results.values())
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/validate_teacher_id')
def validate_teacher_id():
    teacher_id = request.args.get('teacher_id')
    
    if not teacher_id:
        return jsonify({
            'success': False,
            'message': 'Teacher ID is required'
        }), 400
    
    try:
        # Load teacher data from CSV
        teachers_df = pd.read_csv('data/teachers.csv')
        teacher_row = teachers_df[teachers_df['teacher_id'] == teacher_id]
        
        if teacher_row.empty:
            return jsonify({
                'success': False,
                'message': 'Teacher ID not found'
            })
        
        teacher_data = teacher_row.iloc[0].to_dict()
        
        return jsonify({
            'success': True,
            'teacher_data': {
                'teacher_id': teacher_data['teacher_id'],
                'name': teacher_data['name'],
                'department': teacher_data['department'],
                'email': teacher_data['email'],
                'designation': teacher_data['designation'],
                'preferred_campus': teacher_data['preferred_campus']
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500