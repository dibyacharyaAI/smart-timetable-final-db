from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from models import db, TimetableSlot
from datetime import datetime, timedelta
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
    teacher_slots = TimetableSlot.query.filter_by(
        teacher_id=current_user.teacher_id,
        is_active=True
    ).all()

    total_classes = len(teacher_slots)
    unique_subjects = len(set(slot.subject_code for slot in teacher_slots))
    unique_batches = len(set(slot.batch_id for slot in teacher_slots))
    today = datetime.now().strftime('%A')
    today_slots = [slot for slot in teacher_slots if slot.day == today]

    weekly_schedule = {}
    for slot in teacher_slots:
        weekly_schedule.setdefault(slot.day, []).append(slot)

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
            'weekly_schedule': {day: [slot.to_dict() for slot in slots] for day, slots in weekly_schedule.items()}
        })

    return render_template('teacher/dashboard.html', stats=stats, today_slots=today_slots, weekly_schedule=weekly_schedule)

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

    return render_template('teacher/timetable.html', slots=slots, days=days, subjects=subjects)

@teacher_bp.route('/timetable/edit/<int:slot_id>', methods=['PUT'])
@login_required
@teacher_required
def edit_slot(slot_id):
    slot = TimetableSlot.query.filter_by(
        id=slot_id,
        teacher_id=current_user.teacher_id
    ).first_or_404()

    data = request.get_json()
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
            'message': 'Slot updated successfully',
            'slot': slot.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Update failed: {str(e)}'
        }), 500

@teacher_bp.route('/timetable/optimize', methods=['POST'])
@login_required
@teacher_required
def optimize_teacher_slots():
    try:
        slots = TimetableSlot.query.filter_by(
            teacher_id=current_user.teacher_id,
            is_active=True
        ).all()

        if not slots:
            return jsonify({"success": False, "message": "No slots found to optimize."}), 404

        schedule = {}
        for slot in slots:
            schedule.setdefault(slot.day, []).append(slot)

        conflicts = []
        auto_fixed = []
        for day, day_slots in schedule.items():
            day_slots.sort(key=lambda s: s.time_start)
            for i in range(len(day_slots)):
                for j in range(i + 1, len(day_slots)):
                    s1 = day_slots[i]
                    s2 = day_slots[j]

                    try:
                        s1_start = s1.time_start if isinstance(s1.time_start, datetime) else datetime.strptime(s1.time_start, '%H:%M').time()
                        s1_end = s1.time_end if isinstance(s1.time_end, datetime) else datetime.strptime(s1.time_end, '%H:%M').time()
                        s2_start = s2.time_start if isinstance(s2.time_start, datetime) else datetime.strptime(s2.time_start, '%H:%M').time()
                        s2_end = s2.time_end if isinstance(s2.time_end, datetime) else datetime.strptime(s2.time_end, '%H:%M').time()
                    except Exception as parse_err:
                        conflicts.append((s1.id, s2.id, f'TimeParseError: {str(parse_err)}'))
                        continue

                    if s1_start < s2_end and s2_start < s1_end:
                        if s1.room_id == s2.room_id:
                            conflicts.append((s1.id, s2.id, 'Room'))
                            try:
                                new_start = datetime.combine(datetime.today(), s2_end) + timedelta(minutes=30)
                                new_end = new_start + timedelta(hours=1)
                                s2.time_start = new_start.time()
                                s2.time_end = new_end.time()
                                s2.updated_at = datetime.utcnow()
                                s2.version += 1
                                auto_fixed.append(s2.id)
                            except Exception as auto_fix_err:
                                conflicts.append((s2.id, s2.id, f'AutoFixError: {str(auto_fix_err)}'))

                        elif s1.teacher_id == s2.teacher_id:
                            conflicts.append((s1.id, s2.id, 'Teacher'))

        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Optimization complete",
            "auto_fixed": auto_fixed,
            "conflicts": conflicts,
            "total_slots": len(slots)
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "message": f"Optimization failed: {str(e)}"
        }), 500



@teacher_bp.route('/timetable/download')
@login_required
@teacher_required
def download_teacher_timetable():
    format_type = request.args.get('format', 'csv')

    slots = TimetableSlot.query.filter_by(
        teacher_id=current_user.teacher_id,
        is_active=True
    ).all()

    data = [slot.to_dict() for slot in slots]
    df = pd.DataFrame(data)

    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'teacher_timetable_{current_user.teacher_id}_{datetime.now().strftime("%Y%m%d")}.csv'
    )
@teacher_bp.route('/timetable/editable')
@login_required
@teacher_required
def editable_timetable():
    slots = TimetableSlot.query.filter_by(
        teacher_id=current_user.teacher_id,
        is_active=True
    ).order_by(TimetableSlot.slot_index).all()

    # Load subject and room info
    subjects_df = pd.read_csv('data/subjects.csv')
    rooms_df = pd.read_csv('data/rooms.csv')

    teacher_subjects = subjects_df[
        subjects_df['subject_code'].isin([slot.subject_code for slot in slots])
    ]
    available_rooms = rooms_df.to_dict('records')

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
                           subjects=teacher_subjects.to_dict('records'),
                           rooms=available_rooms,
                           total_slots=len(slots))

@teacher_bp.route('/timetable/download/weekly')
@login_required
@teacher_required
def teacher_weekly_download():
    """Weekly timetable download for teacher"""
    format_type = request.args.get('format', 'csv')
    week_type = request.args.get('week', 'current')

    slots = TimetableSlot.query.filter_by(
        teacher_id=current_user.teacher_id,
        is_active=True
    ).all()

    if not slots:
        return send_file(
            io.BytesIO("No data available\n".encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'teacher_weekly_timetable_{week_type}_{current_user.teacher_id}.csv'
        )

    data = [slot.to_dict() for slot in slots]
    df = pd.DataFrame(data)

    # Filter for working weekdays if current or next week
    if week_type in ['current', 'next']:
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        df = df[df['day'].isin(weekdays)]

    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'teacher_weekly_timetable_{week_type}_{current_user.teacher_id}.csv'
    )

