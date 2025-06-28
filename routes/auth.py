from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from datetime import datetime
import pandas as pd

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            username = request.form.get('username')
            password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'user': user.to_dict(),
                    'redirect_url': f'/{user.role}/dashboard'
                })
            else:
                flash('Login successful!', 'success')
                if user.role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                elif user.role == 'teacher':
                    return redirect(url_for('teacher.dashboard'))
                elif user.role == 'student':
                    return redirect(url_for('student.dashboard'))
        else:
            if request.is_json:
                return jsonify({
                    'success': False,
                    'message': 'Invalid username or password'
                }), 401
            else:
                flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == data['username']) | (User.email == data['email'])
        ).first()
        
        if existing_user:
            message = 'Username or email already exists'
            if request.is_json:
                return jsonify({'success': False, 'message': message}), 400
            else:
                flash(message, 'error')
                return render_template('auth/register.html')
        
        # Validate role-specific IDs
        role = data.get('role')
        if role == 'teacher':
            teacher_id = data.get('teacher_id')
            if not teacher_id or not validate_teacher_id(teacher_id):
                message = 'Invalid teacher ID'
                if request.is_json:
                    return jsonify({'success': False, 'message': message}), 400
                else:
                    flash(message, 'error')
                    return render_template('auth/register.html')
        
        elif role == 'student':
            student_id = data.get('student_id')
            if not student_id or not validate_student_id(student_id):
                message = 'Invalid student ID'
                if request.is_json:
                    return jsonify({'success': False, 'message': message}), 400
                else:
                    flash(message, 'error')
                    return render_template('auth/register.html')
        
        # Create new user
        try:
            user = User()
            user.username = data['username']
            user.email = data['email']
            user.role = data['role']
            user.full_name = data['full_name']
            user.phone = data.get('phone')
            user.set_password(data['password'])
            
            if role == 'teacher':
                user.teacher_id = data['teacher_id']
                teacher_data = get_teacher_data(data['teacher_id'])
                if teacher_data:
                    user.department = teacher_data['department']
                    user.campus = teacher_data['preferred_campus']
            
            elif role == 'student':
                user.student_id = data['student_id']
                student_data = get_student_data(data['student_id'])
                if student_data:
                    user.department = student_data['department']
                    user.batch_id = student_data['batch_id']
                    user.section = student_data['section']
                    user.campus = student_data['primary_campus']
            
            elif role == 'admin':
                user.department = 'Administration'
                user.campus = 'Campus-3'
            
            db.session.add(user)
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Registration successful',
                    'user': user.to_dict()
                })
            else:
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('auth.login'))
                
        except Exception as e:
            db.session.rollback()
            message = f'Registration failed: {str(e)}'
            if request.is_json:
                return jsonify({'success': False, 'message': message}), 500
            else:
                flash(message, 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    if request.is_json:
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    else:
        flash('You have been logged out.', 'info')
        return redirect(url_for('auth.login'))

def validate_teacher_id(teacher_id):
    """Validate teacher ID against CSV data"""
    try:
        teachers_df = pd.read_csv('data/teachers.csv')
        return teacher_id in teachers_df['teacher_id'].values
    except Exception:
        return False

def validate_student_id(student_id):
    """Validate student ID against CSV data"""
    try:
        students_df = pd.read_csv('data/students.csv')
        return student_id in students_df['student_id'].values
    except Exception:
        return False

def get_teacher_data(teacher_id):
    """Get teacher data from CSV"""
    try:
        teachers_df = pd.read_csv('data/teachers.csv')
        teacher_row = teachers_df[teachers_df['teacher_id'] == teacher_id].iloc[0]
        return teacher_row.to_dict()
    except Exception:
        return None

def get_student_data(student_id):
    """Get student data from CSV"""
    try:
        students_df = pd.read_csv('data/students.csv')
        student_row = students_df[students_df['student_id'] == student_id].iloc[0]
        return student_row.to_dict()
    except Exception:
        return None