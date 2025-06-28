from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from models import db, TimetableSlot
from datetime import datetime
import pandas as pd
import io
from functools import wraps

teacher_bp = Blueprint('teacher', __name__)

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'teacher':
            if request.is_json:
                return jsonify({'error': 'Teacher access required'}), 403
            flash('Teacher access required', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@teacher_bp.route('/dashboard')
@login_required
@teacher_required
def dashboard():
    # Get teacher's timetable statistics
    teacher_slots = TimetableSlot.query.filter_by(
        teacher_id=current_user.teacher_id,
        is_active=True
    ).all()
    
    # Calculate statistics
    total_classes = len(teacher_slots)
    unique_subjects = len(set(slot.subject_code for slot in teacher_slots))
    unique_batches = len(set(slot.batch_id for slot in teacher_slots))
    
    # Get today's schedule
    today = datetime.now().strftime('%A')
    today_slots = [slot for slot in teacher_slots if slot.day == today]
    
    # Get weekly schedule grouped by day
    weekly_schedule = {}
    for slot in teacher_slots:
        if slot.day not in weekly_schedule:
            weekly_schedule[slot.day] = []
        weekly_schedule[slot.day].append(slot)
    
    # Sort slots by time for each day
    for day in weekly_schedule:
        weekly_schedule[day].sort(key=lambda x: x.time_start)
    
    stats = {
        'total_classes': total_classes,
        'unique_subjects': unique_subjects,
        'unique_batches': unique_batches,
        'today_classes': len(today_slots),
        'teacher_name': current_user.full_name,
        'teacher_id': current_user.teacher_id,
        'department': current_user.department
    }
    
    if request.is_json:
        return jsonify({
            'stats': stats,
            'today_schedule': [slot.to_dict() for slot in today_slots],
            'weekly_schedule': {day: [slot.to_dict() for slot in slots] 
                             for day, slots in weekly_schedule.items()}
        })
    
    return render_template('teacher/dashboard.html', 
                         stats=stats, 
                         today_slots=today_slots,
                         weekly_schedule=weekly_schedule)

@teacher_bp.route('/timetable')
@login_required
@teacher_required
def timetable():
    day_filter = request.args.get('day')
    subject_filter = request.args.get('subject')
    
    query = TimetableSlot.query.filter_by(
        teacher_id=current_user.teacher_id,
        is_active=True
    )
    
    if day_filter:
        query = query.filter_by(day=day_filter)
    if subject_filter:
        query = query.filter_by(subject_code=subject_filter)
    
    slots = query.order_by(TimetableSlot.slot_index).all()
    
    # Get filter options
    all_slots = TimetableSlot.query.filter_by(
        teacher_id=current_user.teacher_id,
        is_active=True
    ).all()
    
    days = sorted(set(slot.day for slot in all_slots))
    subjects = sorted(set(slot.subject_code for slot in all_slots))
    
    if request.is_json:
        return jsonify({
            'slots': [slot.to_dict() for slot in slots],
            'filters': {
                'days': days,
                'subjects': subjects
            }
        })
    
    return render_template('teacher/timetable.html', 
                         slots=slots, 
                         days=days, 
                         subjects=subjects)

@teacher_bp.route('/timetable/edit/<int:slot_id>', methods=['GET', 'PUT'])
@login_required
@teacher_required
def edit_slot(slot_id):
    slot = TimetableSlot.query.filter_by(
        id=slot_id,
        teacher_id=current_user.teacher_id
    ).first_or_404()
    
    if request.method == 'PUT':
        data = request.get_json()
        
        # Teachers can only edit limited fields
        editable_fields = ['room_id', 'room_name', 'activity_type']
        
        try:
            for key, value in data.items():
                if key in editable_fields and hasattr(slot, key):
                    setattr(slot, key, value)
            
            slot.updated_at = datetime.utcnow()
            slot.version += 1
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Timetable slot updated successfully',
                'slot': slot.to_dict()
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Update failed: {str(e)}'
            }), 500
    
    # GET request - return slot details
    if request.is_json:
        return jsonify({'slot': slot.to_dict()})
    
    return render_template('teacher/edit_slot.html', slot=slot)

@teacher_bp.route('/slot/<int:slot_id>', methods=['GET', 'PUT'])
@login_required
@teacher_required
def manage_slot(slot_id):
    slot = TimetableSlot.query.filter_by(
        id=slot_id,
        teacher_id=current_user.teacher_id
    ).first_or_404()
    
    if request.method == 'GET':
        return jsonify({'slot': slot.to_dict()})
    
    elif request.method == 'PUT':
        try:
            # Get form data
            data = request.form.to_dict()
            
            # Update fields
            slot.subject_code = data.get('subject_code', slot.subject_code)
            slot.room_id = data.get('room_id', slot.room_id)
            slot.batch_id = data.get('batch_id', slot.batch_id)
            slot.section = data.get('section', slot.section)
            slot.activity_type = data.get('activity_type', slot.activity_type)
            
            # Get updated subject name from CSV
            subjects_df = pd.read_csv('data/subjects.csv')
            subject_row = subjects_df[subjects_df['subject_code'] == slot.subject_code]
            if not subject_row.empty:
                slot.subject_name = subject_row.iloc[0]['subject_name']
            
            # Get updated room name from CSV
            rooms_df = pd.read_csv('data/rooms.csv')
            room_row = rooms_df[rooms_df['room_id'] == slot.room_id]
            if not room_row.empty:
                slot.room_name = room_row.iloc[0]['room_name']
                slot.campus = room_row.iloc[0]['campus']
            
            slot.updated_at = datetime.utcnow()
            slot.version += 1
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Slot updated successfully',
                'slot': slot.to_dict()
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Error updating slot: {str(e)}'
            }), 500

@teacher_bp.route('/timetable/editable')
@login_required
@teacher_required
def editable_timetable():
    # Get teacher's current timetable
    slots = TimetableSlot.query.filter_by(
        teacher_id=current_user.teacher_id,
        is_active=True
    ).order_by(TimetableSlot.slot_index).all()
    
    # Get unique values for dropdowns
    subjects_df = pd.read_csv('data/subjects.csv')
    rooms_df = pd.read_csv('data/rooms.csv')
    
    # Filter subjects that teacher can teach
    teacher_subjects = subjects_df[
        subjects_df['subject_code'].isin([slot.subject_code for slot in slots])
    ]
    
    # Get all available rooms
    available_rooms = rooms_df.to_dict('records') if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else [] if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else []
    
    # Days and time slots
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    time_slots = [
        ('08:00', '09:00'), ('09:00', '10:00'), ('10:00', '11:00'),
        ('11:20', '12:20'), ('13:00', '14:00'), ('14:00', '15:00'),
        ('15:00', '16:00'), ('16:00', '17:00'), ('17:00', '18:00')
    ]
    
    return render_template('teacher/editable_timetable.html',
                         slots=slots,
                         days=days,
                         time_slots=time_slots,
                         subjects=teacher_subjects.to_dict('records') if hasattr(locals().get('df', None) or locals().get('data', None), 'to_dict') else [] if hasattr(teacher_subjects, 'to_dict') else [],
                         rooms=available_rooms,
                         total_slots=len(slots))

@teacher_bp.route('/timetable/optimize', methods=['POST'])
@login_required
@teacher_required
def optimize_timetable():
    try:
        # Get teacher's current timetable
        current_slots = TimetableSlot.query.filter_by(
            teacher_id=current_user.teacher_id,
            is_active=True
        ).all()
        
        # Create temporary CSV file for pipeline
        temp_data = []
        for slot in current_slots:
            temp_data.append({
                'slot_index': slot.slot_index,
                'batch_id': slot.batch_id,
                'section': slot.section,
                'day': slot.day,
                'time_start': slot.time_start,
                'time_end': slot.time_end,
                'subject_code': slot.subject_code,
                'subject_name': slot.subject_name,
                'teacher_id': slot.teacher_id,
                'teacher_name': slot.teacher_name,
                'room_id': slot.room_id,
                'room_name': slot.room_name,
                'campus': slot.campus,
                'activity_type': slot.activity_type,
                'department': slot.department,
                'scheme': slot.scheme
            })
        
        # Save to temp CSV
        temp_df = pd.DataFrame(temp_data)
        temp_csv_path = f'data/temp_teacher_{current_user.teacher_id}.csv'
        temp_df.to_csv(temp_csv_path, index=False)
        
        # Run ML pipeline
        from pipeline.streamlined_pipeline import StreamlinedPipeline
        pipeline = StreamlinedPipeline()
        result = pipeline.run_complete_pipeline(temp_csv_path)
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Timetable optimized successfully',
                'pipeline_result': result,
                'optimized_slots': len(temp_data)
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Optimization failed: {result.get("error", "Unknown error")}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Optimization error: {str(e)}'
        }), 500

@teacher_bp.route('/slot/new', methods=['POST'])
@login_required
@teacher_required
def create_new_slot():
    try:
        # Get form data
        data = request.form.to_dict()
        
        # Create new slot
        slot = TimetableSlot()
        slot.teacher_id = current_user.teacher_id
        slot.teacher_name = current_user.full_name
        slot.day = data['day']
        slot.time_start = data['time_start']
        slot.time_end = data['time_end']
        slot.subject_code = data['subject_code']
        slot.room_id = data['room_id']
        slot.batch_id = data['batch_id']
        slot.section = data['section']
        slot.activity_type = data['activity_type']
        slot.campus = current_user.campus or 'Campus-3'
        slot.department = current_user.department
        slot.scheme = 'Scheme-A'  # Default
        slot.created_by = current_user.id
        
        # Get subject name from CSV
        subjects_df = pd.read_csv('data/subjects.csv')
        subject_row = subjects_df[subjects_df['subject_code'] == data['subject_code']]
        if not subject_row.empty:
            slot.subject_name = subject_row.iloc[0]['subject_name']
        else:
            slot.subject_name = data['subject_code']
        
        # Get room name from CSV
        rooms_df = pd.read_csv('data/rooms.csv')
        room_row = rooms_df[rooms_df['room_id'] == data['room_id']]
        if not room_row.empty:
            slot.room_name = room_row.iloc[0]['room_name']
            slot.campus = room_row.iloc[0]['campus']
        else:
            slot.room_name = data['room_id']
        
        # Generate slot index
        slot.slot_index = len(TimetableSlot.query.all()) + 1
        
        db.session.add(slot)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'New slot created successfully',
            'slot': slot.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating slot: {str(e)}'
        }), 500

@teacher_bp.route('/slot/<int:slot_id>', methods=['DELETE'])
@login_required
@teacher_required
def delete_slot(slot_id):
    try:
        slot = TimetableSlot.query.get_or_404(slot_id)
        
        # Check if teacher owns this slot
        if slot.teacher_id != current_user.teacher_id:
            return jsonify({
                'success': False,
                'message': 'You can only delete your own slots'
            }), 403
        
        # Soft delete
        slot.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Slot deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting slot: {str(e)}'
        }), 500

@teacher_bp.route('/download_timetable')
@teacher_bp.route('/timetable/download')
@login_required
@teacher_required
def download_timetable():
    format_type = request.args.get('format', 'csv')
    week_type = request.args.get('week', 'full')  # current, next, full
    
    # Get teacher's complete timetable data
    slots = TimetableSlot.query.filter_by(
        teacher_id=current_user.teacher_id,
        is_active=True
    ).order_by(TimetableSlot.slot_index).all()
    
    # Convert to DataFrame with complete data
    data = []
    for slot in slots:
        slot_dict = slot.to_dict()
        data.append(slot_dict)
    
    df = pd.DataFrame(data)
    
    # For CSV format, always provide FULL teacher timetable data
    if format_type == 'csv':
        # CSV gets complete teacher timetable regardless of week parameter
        output = io.StringIO()
        if not df.empty:
            # Sort by day order and time for better readability
            day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            df['day_order'] = df['day'].map({day: i for i, day in enumerate(day_order)})
            df = df.sort_values(['day_order', 'time_start']).drop('day_order', axis=1)
            
            # Add header with teacher info
            output.write(f"# Teacher Timetable - {current_user.full_name} ({current_user.teacher_id})\n")
            output.write(f"# Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            output.write(f"# Total Classes: {len(df)}\n\n")
            
        df.to_csv(output, index=False)
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'teacher_full_timetable_{current_user.teacher_id}_{datetime.now().strftime("%Y%m%d")}.csv'
        )
    
    # For Excel format, apply week filtering if requested
    elif format_type == 'excel':
        if week_type != 'full' and not df.empty:
            current_date = datetime.now()
            if week_type == 'current':
                # Current week - filter by current week's days
                df = df[df['day'].isin(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])]
            elif week_type == 'next':
                # Next week - same filtering but for next week
                df = df[df['day'].isin(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])]
        
        output = io.BytesIO()
        try:
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=f'Teacher_{current_user.teacher_id}', index=False)
        except Exception as e:
            flash(f'Error creating Excel file: {str(e)}', 'error')
            return redirect(url_for('teacher.timetable'))
        
        output.seek(0)
        filename_suffix = f"_{week_type}_week" if week_type != 'full' else "_full"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'teacher_timetable_{current_user.teacher_id}{filename_suffix}_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )



@teacher_bp.route('/timetable/download/weekly')
@login_required
@teacher_required
def teacher_weekly_download():
    """Enhanced weekly timetable download for teacher"""
    format_type = request.args.get('format', 'csv')
    week_type = request.args.get('week', 'current')
    
    # Get teacher's complete timetable data
    slots = TimetableSlot.query.filter_by(
        teacher_id=current_user.teacher_id,
        is_active=True
    ).order_by(TimetableSlot.slot_index).all()
    
    if not slots:
        flash('No timetable data found for download.', 'warning')
        return redirect(url_for('teacher.timetable'))
    
    # Convert to DataFrame with complete data
    data = []
    for slot in slots:
        slot_dict = slot.to_dict()
        data.append(slot_dict)
    
    df = pd.DataFrame(data)
    
    # Apply week filtering based on request
    if week_type == 'current':
        # Current week - filter weekdays only
        df = df[df['day'].isin(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])]
        week_label = "Current Week"
    elif week_type == 'next':
        # Next week - filter weekdays only  
        df = df[df['day'].isin(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])]
        week_label = "Next Week"
    else:
        # Full schedule including weekends
        week_label = "Full Schedule"
    
    # Sort for better readability
    if not df.empty:
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        df['day_order'] = df['day'].apply(lambda x: day_order.index(x) if x in day_order else 7)
        df = df.sort_values(['day_order', 'time_start']).drop('day_order', axis=1)
    
    if format_type == 'excel':
        output = io.BytesIO()
        try:
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=f'{week_label}', index=False)
        except Exception as e:
            flash(f'Error creating Excel file: {str(e)}', 'error')
            return redirect(url_for('teacher.timetable'))
        
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'teacher_{week_type}_week_{current_user.teacher_id}_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
    else:
        # CSV format - provide complete teacher data for week
        output = io.StringIO()
        
        # Add header information
        output.write(f"# Teacher Weekly Timetable - {week_label}\n")
        output.write(f"# Teacher: {current_user.full_name} ({current_user.teacher_id})\n")
        output.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        output.write(f"# Total Classes: {len(df)}\n\n")
        
        df.to_csv(output, index=False)
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'teacher_{week_type}_week_{current_user.teacher_id}_{datetime.now().strftime("%Y%m%d")}.csv'
        )

@teacher_bp.route('/students')
@login_required
@teacher_required
def students():
    """Get students taught by this teacher"""
    try:
        # Validate teacher ID
        if not current_user.teacher_id:
            if request.is_json:
                return jsonify({'error': 'Teacher ID not found'}), 400
            flash('Teacher ID not found. Please contact administrator.', 'error')
            return redirect(url_for('teacher.dashboard'))
        
        # Get batches taught by this teacher
        teacher_slots = TimetableSlot.query.filter_by(
            teacher_id=current_user.teacher_id,
            is_active=True
        ).all()
        
        batch_ids = list(set(slot.batch_id for slot in teacher_slots))
        
        # If no batches found
        if not batch_ids:
            students_list = []
        else:
            # Load student data
            try:
                students_df = pd.read_csv('data/students.csv')
                teacher_students = students_df[students_df['batch_id'].isin(batch_ids)]
                students_list = teacher_students.to_dict('records')
            except FileNotFoundError:
                students_list = []
                batch_ids = []
            except Exception as csv_error:
                print(f"CSV Error: {csv_error}")
                students_list = []
        
        if request.is_json:
            return jsonify({
                'students': students_list,
                'total_students': len(students_list),
                'batches': batch_ids
            })
        
        return render_template('teacher/students.html', 
                             students=students_list, 
                             batches=batch_ids)
        
    except Exception as e:
        print(f"Students route error: {e}")
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash(f'Error loading students: {str(e)}', 'error')
        return redirect(url_for('teacher.dashboard'))

@teacher_bp.route('/subjects')
@login_required
@teacher_required
def subjects():
    """Get subjects taught by this teacher"""
    try:
        # Get teacher data
        teachers_df = pd.read_csv('data/teachers.csv')
        teacher_data = teachers_df[teachers_df['teacher_id'] == current_user.teacher_id]
        
        if teacher_data.empty:
            subjects_list = []
        else:
            teacher_info = teacher_data.iloc[0]
            # Get subjects from expertise and primary subjects
            expertise = str(teacher_info.get('subject_expertise', ''))
            primary = str(teacher_info.get('primary_subjects', ''))
            
            # Load subjects data
            subjects_df = pd.read_csv('data/subjects.csv')
            
            # Find matching subjects
            teacher_subjects = subjects_df[
                subjects_df['subject_name'].str.contains('|'.join(expertise.split(', ')), na=False, case=False) |
                subjects_df['subject_name'].str.contains('|'.join(primary.split(', ')), na=False, case=False)
            ]
            
            subjects_list = teacher_subjects.to_dict('records') if hasattr(teacher_subjects, 'to_dict') else []
        
        if request.is_json:
            return jsonify({
                'subjects': subjects_list,
                'total_subjects': len(subjects_list)
            })
        
        return render_template('teacher/subjects.html', subjects=subjects_list)
        
    except Exception as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash(f'Error loading subjects: {str(e)}', 'error')
        return redirect(url_for('teacher.dashboard'))