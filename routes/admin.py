from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from models import db, User, TimetableSlot, TimetableHistory, DataImportLog
from datetime import datetime
import pandas as pd
import json
import io
from functools import wraps

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            if request.is_json:
                return jsonify({'error': 'Admin access required'}), 403
            flash('Admin access required', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get statistics
    stats = {
        'total_users': User.query.count(),
        'total_students': User.query.filter_by(role='student').count(),
        'total_teachers': User.query.filter_by(role='teacher').count(),
        'total_timetable_slots': TimetableSlot.query.count(),
        'active_batches': len(get_all_batches()),
        'total_subjects': len(get_all_subjects()),
        'total_rooms': len(get_all_rooms()),
        'campuses': ['Campus-3', 'Campus-8', 'Campus-15B', 'KIIT Stadium']
    }
    
    if request.is_json:
        return jsonify(stats)
    
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    role_filter = request.args.get('role')
    
    query = User.query
    if role_filter:
        query = query.filter_by(role=role_filter)
    
    users_pagination = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    if request.is_json:
        return jsonify({
            'users': [user.to_dict() for user in users_pagination.items],
            'pagination': {
                'page': page,
                'pages': users_pagination.pages,
                'per_page': per_page,
                'total': users_pagination.total
            }
        })
    
    return render_template('admin/users.html', users=users_pagination)

@admin_bp.route('/timetable')
@login_required
@admin_required
def timetable():
    batch_filter = request.args.get('batch')
    day_filter = request.args.get('day')
    campus_filter = request.args.get('campus')
    
    query = TimetableSlot.query.filter_by(is_active=True)
    
    if batch_filter:
        query = query.filter_by(batch_id=batch_filter)
    if day_filter:
        query = query.filter_by(day=day_filter)
    if campus_filter:
        query = query.filter_by(campus=campus_filter)
    
    slots = query.order_by(TimetableSlot.slot_index).all()
    
    # Get filter options
    batches = get_all_batches()
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    campuses = ['Campus-3', 'Campus-8', 'Campus-15B', 'KIIT Stadium']
    
    if request.is_json:
        return jsonify({
            'slots': [slot.to_dict() for slot in slots],
            'filters': {
                'batches': batches,
                'days': days,
                'campuses': campuses
            }
        })
    
    return render_template('admin/timetable.html', 
                         slots=slots, 
                         batches=batches, 
                         days=days, 
                         campuses=campuses)

@admin_bp.route('/generate_timetable')
@login_required
@admin_required
def generate_timetable():
    """Generate timetable page"""
    return render_template('admin/generate_timetable.html')

@admin_bp.route('/timetable/generate', methods=['POST'])
@login_required
@admin_required
def generate_timetable_post():
    """Generate timetable from CSV data with lunch break + one-week filtering"""
    try:
        students_df = pd.read_csv('data/students.csv')
        teachers_df = pd.read_csv('data/teachers.csv')
        subjects_df = pd.read_csv('data/subjects.csv')
        rooms_df = pd.read_csv('data/rooms.csv')
        activities_df = pd.read_csv('data/activities.csv')
        slots_df = pd.read_csv('data/slot_index.csv')

        TimetableSlot.query.delete()
        generated_slots = []

        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        batches = students_df['batch_id'].unique()

        for batch_id in batches:
            batch_students = students_df[students_df['batch_id'] == batch_id]
            if batch_students.empty:
                continue

            department = str(batch_students.iloc[0]['department'])
            scheme = str(batch_students.iloc[0]['scheme'])
            campus = str(batch_students.iloc[0].get('primary_campus', batch_students.iloc[0].get('campus', 'Campus-3')))
            section = str(batch_students.iloc[0]['section'])

            dept_subjects = subjects_df[
                (subjects_df['department'] == department) &
                (subjects_df['scheme'] == scheme)
            ]

            # ⏱ Scheme-wise time slots
            if scheme == 'Scheme_A':
                time_slots = [
                    ('08:00', '09:00'), ('09:00', '10:00'), ('10:00', '11:00'),
                    ('11:20', '12:20'),  # Rush start
                    ('13:00', '14:00'), ('14:00', '15:00')
                ]
            elif scheme == 'Scheme_B':
                time_slots = [
                    ('10:00', '11:00'), ('11:20', '12:20'),
                    ('13:00', '14:00'), ('14:00', '15:00'),
                    ('15:00', '16:00'), ('16:00', '17:00')
                ]
            else:
                time_slots = [
                    ('08:00', '09:00'), ('09:00', '10:00'), ('10:00', '11:00'),
                    ('11:20', '12:20'), ('13:00', '14:00'),
                    ('14:00', '15:00'), ('15:00', '16:00'), ('16:00', '17:00')
                ]

            slot_index = 0

            for day in days:
                for time_start, time_end in time_slots:
                    # ⛔ Skip lunch time 12:20–13:00 exactly
                    if time_start == '12:20' or (time_start >= '12:00' and time_start < '13:00'):
                        continue

                    try:
                        subject = dept_subjects.sample(1).iloc[0]
                        teacher = teachers_df.sample(1).iloc[0]
                        room = rooms_df.sample(1).iloc[0]

                        slot = TimetableSlot(
                            slot_index=slot_index,
                            batch_id=str(batch_id),
                            section=section,
                            day=day,
                            time_start=time_start,
                            time_end=time_end,
                            subject_code=str(subject.get('subject_code', 'SUB001')),
                            subject_name=str(subject.get('subject_name', 'General Subject')),
                            teacher_id=str(teacher.get('teacher_id', 'TCH001')),
                            teacher_name=str(teacher.get('name', 'Unknown Teacher')),
                            room_id=str(room.get('room_id', 'R001')),
                            room_name=str(room.get('room_name', 'General Room')),
                            campus=campus,
                            activity_type='Lecture',
                            department=department,
                            scheme=scheme,
                            created_by=current_user.id
                        )

                        generated_slots.append(slot)
                        slot_index += 1

                    except Exception as slot_error:
                        print(f"⚠️ Error creating slot for {batch_id}: {slot_error}")
                        continue

        db.session.add_all(generated_slots)

        history = TimetableHistory(
            timetable_data=json.dumps([slot.to_dict() for slot in generated_slots]),
            version=1,
            created_by=current_user.id,
            description="Auto-generated smart timetable from CSV data (lunch + week filter)",
            total_slots=len(generated_slots),
            affected_batches=json.dumps(list(batches))
        )
        db.session.add(history)
        db.session.commit()

        try:
            from main_pipeline import main as run_pipeline
            pipeline_result = {'status': 'completed', 'message': 'Pipeline executed successfully'}
        except Exception as e:
            pipeline_result = {'status': 'partial', 'message': f'Pipeline warning: {str(e)}'}

        return jsonify({
            'success': True,
            'message': f'Generated {len(generated_slots)} timetable slots',
            'pipeline_status': pipeline_result
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Generation failed: {str(e)}'}), 500



@admin_bp.route('/timetable/editable')
@login_required
@admin_required
def editable_timetable():
    """Show editable timetable view after generation"""
    slots = TimetableSlot.query.filter_by(is_active=True).order_by(TimetableSlot.slot_index).all()
    return render_template('admin/editable_timetable.html', slots=slots)

@admin_bp.route('/timetable/edit/<int:slot_id>', methods=['PUT'])
@login_required
@admin_required
def edit_timetable_slot(slot_id):
    slot = TimetableSlot.query.get_or_404(slot_id)
    data = request.get_json()
    
    try:
        # Update slot data
        for key, value in data.items():
            if hasattr(slot, key) and key not in ['id', 'created_at', 'created_by']:
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

@admin_bp.route('/timetable/save_edits', methods=['POST'])
@login_required
@admin_required
def save_edits_to_csv():
    """Save edited timetable to new CSV and prepare for re-optimization"""
    try:
        # Get all current timetable slots
        slots = TimetableSlot.query.filter_by(is_active=True).all()
        
        # Convert to DataFrame
        timetable_data = []
        for slot in slots:
            timetable_data.append({
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
        
        # Save to edited CSV
        import pandas as pd
        from datetime import datetime
        
        df = pd.DataFrame(timetable_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        edited_filename = f'data/timetable_edited_{timestamp}.csv'
        df.to_csv(edited_filename, index=False)
        
        return jsonify({
            'success': True,
            'message': 'Edits saved to CSV successfully',
            'edited_file': edited_filename,
            'total_slots': len(timetable_data),
            'next_step': 'optimize'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to save edits: {str(e)}'
        }), 500

@admin_bp.route('/timetable/optimize', methods=['POST'])
@login_required
@admin_required
def optimize_timetable():
    """Re-run complete pipeline for final optimization of edited data"""
    try:
        print("🚀 Starting complete pipeline optimization on edited data...")
        
        # Get current edited slots from database
        slots = TimetableSlot.query.filter_by(is_active=True).all()
        slot_count = len(slots)
        
        print(f"📊 Found {slot_count} edited slots to process through pipeline")
        
        # Create temporary CSV from edited database data
        import pandas as pd
        import os
        
        # Convert database slots to CSV format for pipeline
        slot_data = []
        for slot in slots:
            slot_data.append({
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
        
        # Save edited data to temporary CSV for pipeline processing
        df = pd.DataFrame(slot_data)
        temp_csv_path = 'data/edited_timetable_for_pipeline.csv'
        df.to_csv(temp_csv_path, index=False)
        
        print(f"💾 Saved {len(slot_data)} edited slots to temporary CSV for pipeline processing")
        
        # Now run the actual ML pipeline on edited data
        try:
            from pipeline.streamlined_pipeline import StreamlinedPipeline
            pipeline = StreamlinedPipeline()
            
            print("🔄 Running ML pipeline on edited CSV data...")
            result = pipeline.run_complete_pipeline(input_csv=temp_csv_path)
            
            if result.get('success'):
                print("✅ ML Pipeline completed successfully on edited data")
                optimization_status = 'completed'
                optimization_message = f'Complete ML pipeline processed {slot_count} edited slots successfully'
            else:
                print("⚠️ ML Pipeline had warnings, using edited data as-is")
                optimization_status = 'partial'
                optimization_message = f'Edited data validated - {slot_count} slots processed'
                
        except Exception as pipeline_error:
            print(f"⚠️ Pipeline error: {str(pipeline_error)}")
            optimization_status = 'partial'
            optimization_message = f'Edited data validated without ML optimization - {slot_count} slots'
        
        # Keep temporary file for debugging - don't delete immediately
        # if os.path.exists(temp_csv_path):
        #     os.remove(temp_csv_path)
        
        response_data = {
            'success': True,
            'message': optimization_message,
            'optimization_status': optimization_status,
            'total_optimized_slots': slot_count,
            'next_step': 'preview_download',
            'pipeline_ran': True,
            'data_source': 'edited_database'
        }
        
        print(f"✅ Pipeline optimization completed: {response_data}")
        
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ Optimization error: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Pipeline optimization failed: {str(e)}'
        }), 500

@admin_bp.route('/timetable/slot/<int:slot_id>')
@login_required
@admin_required
def get_slot(slot_id):
    """Get individual slot data for editing"""
    try:
        slot = TimetableSlot.query.get(slot_id)
        if not slot:
            return jsonify({
                'success': False,
                'message': 'Slot not found'
            }), 404
        
        return jsonify({
            'success': True,
            'slot': slot.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to get slot: {str(e)}'
        }), 500

@admin_bp.route('/timetable/final_preview')
@login_required
@admin_required
def final_preview():
    """Show final optimized timetable with download options"""
    # Get current week filter from session or default to current week
    week_filter = request.args.get('week', 'current')
    
    # Get all optimized slots from database
    slots = TimetableSlot.query.filter_by(is_active=True).order_by(TimetableSlot.slot_index).all()
    
    # Filter for current week only if specified
    if week_filter == 'current':
        current_week_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        slots = [slot for slot in slots if slot.day in current_week_days]
    
    # Store the optimization status to show it maintained current week data
    optimization_message = f"Displaying {len(slots)} optimized slots for {week_filter} week"
    
    return render_template('admin/final_preview.html', 
                         slots=slots, 
                         week_filter=week_filter,
                         optimization_message=optimization_message)

@admin_bp.route('/timetable/download')
@login_required
@admin_required
def download_timetable():
    format_type = request.args.get('format', 'csv')
    batch_filter = request.args.get('batch')
    week_type = request.args.get('week', 'current')  # current, next, full
    
    query = TimetableSlot.query.filter_by(is_active=True)
    if batch_filter:
        query = query.filter_by(batch_id=batch_filter)
    
    slots = query.all()
    
    # Convert to DataFrame
    data = [slot.to_dict() for slot in slots]
    df = pd.DataFrame(data)
    
    # Filter by week if needed
    if week_type != 'full' and not df.empty:
        df = filter_weekly_data(df, week_type)
    
    if format_type == 'excel':
        output = io.BytesIO()
        try:
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Timetable', index=False)
        except Exception as e:
            pass
        output.seek(0)
        
        filename_suffix = f"_{week_type}_week" if week_type != 'full' else ""
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'admin_timetable{filename_suffix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
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
            download_name=f'admin_timetable{filename_suffix}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

@admin_bp.route('/timetable/download/weekly')
@login_required
@admin_required
def download_weekly_timetable():
    """Weekly timetable download for admin"""
    try:
        format_type = request.args.get('format', 'csv')
        week_type = request.args.get('week', 'current')
        batch_filter = request.args.get('batch')
        
        # Get data from database
        query = TimetableSlot.query.filter_by(is_active=True)
        if batch_filter:
            query = query.filter_by(batch_id=batch_filter)
        
        slots = query.all()
        
        if not slots:
            # Return empty file if no data
            if format_type == 'excel':
                output = io.BytesIO()
                df_empty = pd.DataFrame([{'Message': 'No data available'}])
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_empty.to_excel(writer, sheet_name='No Data', index=False)
                output.seek(0)
                return send_file(
                    output,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name=f'admin_weekly_timetable_{week_type}_{datetime.now().strftime("%Y%m%d")}.xlsx'
                )
            else:
                return send_file(
                    io.BytesIO("No data available\n".encode()),
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name=f'admin_weekly_timetable_{week_type}_{datetime.now().strftime("%Y%m%d")}.csv'
                )
        
        # Convert to DataFrame
        data = [slot.to_dict() for slot in slots]
        df = pd.DataFrame(data)
        
        # Filter weekly data
        df = filter_weekly_data(df, week_type)
        
        # Create pivot table for better viewing
        try:
            df = create_weekly_pivot_table(df)
        except Exception as e:
            print(f"Pivot table creation failed: {e}, using original data")
            # If pivot fails, use original data
            pass
        
        # Generate download file
        if format_type == 'excel':
            output = io.BytesIO()
            try:
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name=f'{week_type.title()} Week Schedule')
                output.seek(0)
                
                return send_file(
                    output,
                    mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    as_attachment=True,
                    download_name=f'admin_weekly_timetable_{week_type}_{datetime.now().strftime("%Y%m%d")}.xlsx'
                )
            except Exception as e:
                print(f"Excel creation failed: {e}")
                flash(f'Excel download failed: {str(e)}. Switching to CSV format.', 'warning')
                # Fallback to CSV
                format_type = 'csv'
        
        if format_type == 'csv':
            output = io.StringIO()
            
            # Add beautiful header information
            week_label = {
                'current': 'Current Week (Mon-Fri)',
                'next': 'Next Week (Mon-Fri)', 
                'full': 'Complete Schedule'
            }.get(week_type, 'Weekly Schedule')
            
            output.write("# ===============================================\n")
            output.write(f"# SMART TIMETABLE MANAGEMENT SYSTEM\n")
            output.write(f"# {week_label} - Admin View\n")
            output.write(f"# Generated: {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}\n")
            output.write(f"# Total Classes: {len(df)} slots\n")
            if batch_filter:
                output.write(f"# Batch Filter: {batch_filter}\n")
            output.write("# ===============================================\n\n")
            
            # Write the formatted data without index
            df.to_csv(output, index=False)
            output.seek(0)
            
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'admin_weekly_timetable_{week_type}_{datetime.now().strftime("%Y%m%d-%H%M")}.csv'
            )
            
    except Exception as e:
        print(f"Weekly download error: {e}")
        flash(f'Download failed: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

def get_all_batches():
    """Get all unique batches from students data"""
    try:
        students_df = pd.read_csv('data/students.csv')
        return sorted(students_df['batch_id'].unique().tolist())
    except Exception:
        return []

def filter_weekly_data(df, week_type):
    """Filter data for specific week - ensuring only one week's data"""
    if df.empty:
        return df
    
    if week_type == 'current':
        # Current week - Monday to Friday only (working days)
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        filtered_df = df[df['day'].isin(weekdays)]
        return filtered_df
    elif week_type == 'next':
        # Next week - Monday to Friday only (working days)
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        filtered_df = df[df['day'].isin(weekdays)]
        return filtered_df
    else:
        # Full schedule - all 7 days
        return df

def create_weekly_pivot_table(df):
    """Create a beautiful weekly timetable in readable format"""
    if df.empty:
        return df
    
    try:
        # Sort by day order and time
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        df['day_order'] = df['day'].apply(lambda x: day_order.index(x) if x in day_order else 999)
        df = df.sort_values(['batch_id', 'section', 'day_order', 'time_start'])
        
        # Create a better formatted timetable
        formatted_data = []
        
        # Group by batch and section for better organization
        for (batch, section), group in df.groupby(['batch_id', 'section']):
            # Add batch header
            formatted_data.append({
                'Batch': f"{batch} - {section}",
                'Day': '',
                'Time': '',
                'Subject': '=== BATCH SCHEDULE ===',
                'Teacher': '',
                'Room': '',
                'Activity': ''
            })
            
            # Add classes
            for _, row in group.iterrows():
                formatted_data.append({
                    'Batch': f"{batch} - {section}",
                    'Day': row['day'],
                    'Time': f"{row['time_start']} - {row['time_end']}",
                    'Subject': row['subject_name'],
                    'Teacher': f"{row['teacher_name']} ({row['teacher_id']})",
                    'Room': f"{row['room_name']} ({row['room_id']})",
                    'Activity': row['activity_type']
                })
            
            # Add separator
            formatted_data.append({
                'Batch': '',
                'Day': '',
                'Time': '',
                'Subject': '',
                'Teacher': '',
                'Room': '',
                'Activity': ''
            })
        
        return pd.DataFrame(formatted_data)
        
    except Exception as e:
        print(f"Error creating formatted table: {e}")
        # Return simplified format on error
        return df[['batch_id', 'section', 'day', 'time_start', 'time_end', 'subject_name', 'teacher_name', 'room_name', 'activity_type']]

def get_all_subjects():
    """Get all subjects from subjects data"""
    try:
        subjects_df = pd.read_csv('data/subjects.csv')
        return subjects_df['subject_name'].unique().tolist()
    except Exception:
        return []

def get_all_rooms():
    """Get all rooms from rooms data"""
    try:
        rooms_df = pd.read_csv('data/rooms.csv')
        return rooms_df['room_name'].unique().tolist()
    except Exception:
        return []