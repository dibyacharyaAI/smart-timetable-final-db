from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from models import db, TimetableSlot
from datetime import datetime
import pandas as pd
import io
from functools import wraps

student_bp = Blueprint('student', __name__)

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'student':
            if request.is_json:
                return jsonify({'error': 'Student access required'}), 403
            flash('Student access required', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    # Get student's timetable
    student_slots = TimetableSlot.query.filter_by(
        batch_id=current_user.batch_id,
        section=current_user.section,
        is_active=True
    ).all()
    
    # Calculate statistics
    total_classes = len(student_slots)
    unique_subjects = len(set(slot.subject_code for slot in student_slots))
    unique_teachers = len(set(slot.teacher_id for slot in student_slots))
    
    # Get today's schedule
    today = datetime.now().strftime('%A')
    today_slots = [slot for slot in student_slots if slot.day == today]
    
    # Get next upcoming class
    current_time = datetime.now().strftime('%H:%M')
    upcoming_slots = [slot for slot in today_slots if slot.time_start > current_time]
    next_class = upcoming_slots[0] if upcoming_slots else None
    
    stats = {
        'total_classes': total_classes,
        'unique_subjects': unique_subjects,
        'unique_teachers': unique_teachers,
        'today_classes': len(today_slots),
        'student_name': current_user.full_name,
        'student_id': current_user.student_id,
        'batch_id': current_user.batch_id,
        'section': current_user.section,
        'department': current_user.department,
        'campus': current_user.campus
    }
    
    if request.is_json:
        return jsonify({
            'stats': stats,
            'today_schedule': [slot.to_dict() for slot in today_slots],
            'next_class': next_class.to_dict() if next_class else None
        })
    
    return render_template('student/dashboard.html', 
                         stats=stats, 
                         today_slots=today_slots,
                         next_class=next_class)

@student_bp.route('/timetable')
@login_required
@student_required
def timetable():
    day_filter = request.args.get('day')
    subject_filter = request.args.get('subject')
    
    query = TimetableSlot.query.filter_by(
        batch_id=current_user.batch_id,
        section=current_user.section,
        is_active=True
    )
    
    if day_filter:
        query = query.filter_by(day=day_filter)
    if subject_filter:
        query = query.filter_by(subject_code=subject_filter)
    
    slots = query.order_by(TimetableSlot.slot_index).all()
    
    # Get filter options
    all_slots = TimetableSlot.query.filter_by(
        batch_id=current_user.batch_id,
        section=current_user.section,
        is_active=True
    ).all()
    
    days = sorted(set(slot.day for slot in all_slots))
    subjects = sorted(set(slot.subject_code for slot in all_slots))
    
    # Group by day for better display
    weekly_schedule = {}
    for slot in slots:
        if slot.day not in weekly_schedule:
            weekly_schedule[slot.day] = []
        weekly_schedule[slot.day].append(slot)
    
    # Sort slots by time for each day
    for day in weekly_schedule:
        weekly_schedule[day].sort(key=lambda x: x.time_start)
    
    if request.is_json:
        return jsonify({
            'slots': [slot.to_dict() for slot in slots],
            'weekly_schedule': {day: [slot.to_dict() for slot in slots] 
                             for day, slots in weekly_schedule.items()},
            'filters': {
                'days': days,
                'subjects': subjects
            }
        })
    
    # Calculate additional template variables
    time_slots = sorted(set((slot.time_start, slot.time_end) for slot in all_slots))
    subjects_count = len(set(slot.subject_code for slot in all_slots))
    teachers_count = len(set(slot.teacher_id for slot in all_slots))
    total_hours = len(all_slots)
    
    # Subject details for table
    subject_details = []
    subject_summary = {}
    for slot in all_slots:
        key = (slot.subject_code, slot.subject_name, slot.teacher_name, slot.activity_type)
        if key not in subject_summary:
            subject_summary[key] = 0
        subject_summary[key] += 1
    
    for (subject_code, subject_name, teacher_name, activity_type), hours in subject_summary.items():
        subject_details.append({
            'subject_code': subject_code,
            'subject_name': subject_name,
            'teacher_name': teacher_name,
            'activity_type': activity_type,
            'hours': hours
        })
    
    return render_template('student/timetable.html', 
                         slots=slots, 
                         weekly_schedule=weekly_schedule,
                         days=days, 
                         subjects=subjects,
                         time_slots=time_slots,
                         subjects_count=subjects_count,
                         teachers_count=teachers_count,
                         total_hours=total_hours,
                         subject_details=subject_details)

@student_bp.route('/timetable/download')
@login_required
@student_required
def download_timetable():
    format_type = request.args.get('format', 'csv')
    week_type = request.args.get('week', 'current')  # current, next, full
    
    query = TimetableSlot.query.filter_by(
        batch_id=current_user.batch_id,
        section=current_user.section,
        is_active=True
    ).order_by(TimetableSlot.slot_index)
    
    slots = query.all()
    
    # Convert to DataFrame
    data = [slot.to_dict() for slot in slots]
    df = pd.DataFrame(data)
    
    # Filter by week if needed
    if week_type != 'full' and not df.empty:
        from routes.admin import filter_weekly_data
        df = filter_weekly_data(df, week_type)
    
    if format_type == 'excel':
        output = io.BytesIO()
        try:
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=f'{current_user.batch_id}_{current_user.section}', index=False)
        except Exception as e:
            pass
        output.seek(0)
        
        filename_suffix = f"_{week_type}_week" if week_type != 'full' else ""
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'student_timetable_{current_user.student_id}{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
    else:
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        filename_suffix = f"_{week_type}_week" if week_type != 'full' else ""
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'student_timetable_{current_user.student_id}{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.csv'
        )

@student_bp.route('/timetable/download/weekly')
@login_required
@student_required
def download_weekly_timetable():
    """Weekly timetable download for student"""
    format_type = request.args.get('format', 'csv')
    week_type = request.args.get('week', 'current')
    
    slots = TimetableSlot.query.filter_by(
        batch_id=current_user.batch_id,
        section=current_user.section,
        is_active=True
    ).order_by(TimetableSlot.slot_index).all()
    
    data = [slot.to_dict() for slot in slots]
    df = pd.DataFrame(data)
    
    if not df.empty:
        from routes.admin import filter_weekly_data, create_weekly_pivot_table
        df = filter_weekly_data(df, week_type)
        df = create_weekly_pivot_table(df)
    
    if format_type == 'excel':
        output = io.BytesIO()
        try:
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=f'{week_type.title()} Week Schedule')
        except Exception as e:
            pass
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'student_weekly_timetable_{current_user.student_id}_{week_type}_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
    else:
        output = io.StringIO()
        df.to_csv(output)
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'student_weekly_timetable_{current_user.student_id}_{week_type}_{datetime.now().strftime("%Y%m%d")}.csv'
        )

@student_bp.route('/teachers')
@login_required
@student_required
def teachers():
    """Get teachers for this student's batch"""
    try:
        # Get teacher IDs from student's timetable
        student_slots = TimetableSlot.query.filter_by(
            batch_id=current_user.batch_id,
            section=current_user.section,
            is_active=True
        ).all()
        
        teacher_ids = list(set(slot.teacher_id for slot in student_slots))
        
        # Load teacher data
        teachers_df = pd.read_csv('data/teachers.csv')
        student_teachers = teachers_df[teachers_df['teacher_id'].isin(teacher_ids)]
        
        # Add subject info from timetable
        teachers_list = []
        for _, teacher in student_teachers.iterrows():
            teacher_dict = teacher.to_dict()
            teacher_slots = [slot for slot in student_slots if slot.teacher_id == teacher['teacher_id']]
            teacher_dict['subjects_taught'] = list(set(slot.subject_name for slot in teacher_slots))
            teacher_dict['total_classes'] = len(teacher_slots)
            teachers_list.append(teacher_dict)
        
        if request.is_json:
            return jsonify({
                'teachers': teachers_list,
                'total_teachers': len(teachers_list)
            })
        
        return render_template('student/teachers.html', teachers=teachers_list)
        
    except Exception as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash(f'Error loading teachers: {str(e)}', 'error')
        return redirect(url_for('student.dashboard'))

@student_bp.route('/subjects')
@login_required
@student_required
def subjects():
    """Get subjects for this student"""
    try:
        # Get subjects from student's timetable
        student_slots = TimetableSlot.query.filter_by(
            batch_id=current_user.batch_id,
            section=current_user.section,
            is_active=True
        ).all()
        
        subject_codes = list(set(slot.subject_code for slot in student_slots))
        
        # Load subjects data
        subjects_df = pd.read_csv('data/subjects.csv')
        student_subjects = subjects_df[subjects_df['subject_code'].isin(subject_codes)]
        
        # Add schedule info
        subjects_list = []
        for _, subject in student_subjects.iterrows():
            subject_dict = subject.to_dict()
            subject_slots = [slot for slot in student_slots if slot.subject_code == subject['subject_code']]
            subject_dict['weekly_classes'] = len(subject_slots)
            subject_dict['teachers'] = list(set(slot.teacher_name for slot in subject_slots))
            subject_dict['rooms'] = list(set(slot.room_name for slot in subject_slots))
            subjects_list.append(subject_dict)
        
        if request.is_json:
            return jsonify({
                'subjects': subjects_list,
                'total_subjects': len(subjects_list)
            })
        
        return render_template('student/subjects.html', subjects=subjects_list)
        
    except Exception as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash(f'Error loading subjects: {str(e)}', 'error')
        return redirect(url_for('student.dashboard'))

@student_bp.route('/classmates')
@login_required
@student_required
def classmates():
    """Get classmates in the same batch and section"""
    try:
        # Load student data
        students_df = pd.read_csv('data/students.csv')
        classmates = students_df[
            (students_df['batch_id'] == current_user.batch_id) & 
            (students_df['section'] == current_user.section) &
            (students_df['student_id'] != current_user.student_id)
        ]
        
        classmates_list = classmates.to_dict('records') if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else [] if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else []
        
        if request.is_json:
            return jsonify({
                'classmates': classmates_list,
                'total_classmates': len(classmates_list),
                'batch_id': current_user.batch_id,
                'section': current_user.section
            })
        
        return render_template('student/classmates.html', 
                             classmates=classmates_list,
                             batch_id=current_user.batch_id,
                             section=current_user.section)
        
    except Exception as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash(f'Error loading classmates: {str(e)}', 'error')
        return redirect(url_for('student.dashboard'))