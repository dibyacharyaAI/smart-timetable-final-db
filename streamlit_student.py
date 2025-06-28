import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Student Portal - Smart Timetable",
    page_icon="👨‍🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #e74c3c, #c0392b);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .class-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #e74c3c;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .info-box {
        background: #fef9e7;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #f39c12;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>👨‍🎓 Student Portal - Smart Timetable Management</h1>
    <p>View your schedule, check subjects, and track academic progress</p>
</div>
""", unsafe_allow_html=True)

# Student Selection
st.sidebar.title("👨‍🎓 Student Dashboard")

# Load data
@st.cache_data
def load_csv_data():
    try:
        students_df = pd.read_csv('data/students.csv')
        teachers_df = pd.read_csv('data/teachers.csv')
        subjects_df = pd.read_csv('data/subjects.csv')
        rooms_df = pd.read_csv('data/rooms.csv')
        activities_df = pd.read_csv('data/activities.csv')
        slots_df = pd.read_csv('data/slot_index.csv')
        
        return {
            'students': students_df,
            'teachers': teachers_df,
            'subjects': subjects_df,
            'rooms': rooms_df,
            'activities': activities_df,
            'slots': slots_df
        }
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

data = load_csv_data()

if data is None:
    st.error("Unable to load CSV data. Please check if data files exist.")
    st.stop()

# Student selection
student_ids = data['students']['student_id'].tolist()
selected_student = st.sidebar.selectbox(
    "Select Student ID",
    options=student_ids,
    index=0
)

# Get student info
student_info = data['students'][data['students']['student_id'] == selected_student].iloc[0]

st.sidebar.markdown(f"""
### Student Information
**Name:** {student_info['name']}  
**Batch:** {student_info['batch_id']} | **Section:** {student_info['section']}  
**Department:** {student_info['department']}  
**Campus:** {student_info['primary_campus']}  
**Year:** {student_info['year']} | **Semester:** {student_info['semester']}  
**Scheme:** {student_info['scheme']}
""")

page = st.sidebar.selectbox(
    "Select Page",
    ["Dashboard", "My Timetable", "Subjects", "Teachers", "Classmates"]
)

# Generate mock timetable for student's batch
@st.cache_data
def generate_student_timetable(batch_id, department, scheme):
    # Get subjects for this department and scheme
    dept_subjects = data['subjects'][
        (data['subjects']['department'] == department) & 
        (data['subjects']['scheme'] == scheme)
    ]
    
    if dept_subjects.empty:
        dept_subjects = data['subjects'].sample(6)
    
    # Get teachers from same department
    dept_teachers = data['teachers'][data['teachers']['department'] == department]
    if dept_teachers.empty:
        dept_teachers = data['teachers'].sample(5)
    
    # Generate weekly schedule
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    time_slots = [
        ('08:00', '09:00'), ('09:00', '10:00'), ('10:00', '11:00'),
        ('11:20', '12:20'), ('13:00', '14:00'), ('14:00', '15:00'),
        ('15:00', '16:00'), ('16:00', '17:00')
    ]
    
    schedule = []
    campus_rooms = data['rooms'][data['rooms']['campus'] == student_info['primary_campus']]
    
    for day in days:
        for i, (start_time, end_time) in enumerate(time_slots):
            if i < 4:  # 4 classes per day
                subject = dept_subjects.sample(1).iloc[0]
                teacher = dept_teachers.sample(1).iloc[0]
                room = campus_rooms.sample(1).iloc[0]
                
                schedule.append({
                    'day': day,
                    'time_start': start_time,
                    'time_end': end_time,
                    'subject_name': subject['subject_name'],
                    'subject_code': subject['subject_code'],
                    'teacher_name': teacher['name'],
                    'teacher_id': teacher['teacher_id'],
                    'room_name': room['room_name'],
                    'batch_id': batch_id,
                    'activity_type': 'Lab' if subject['has_lab'] else 'Lecture',
                    'campus': student_info['primary_campus']
                })
    
    return pd.DataFrame(schedule)

student_schedule = generate_student_timetable(
    student_info['batch_id'],
    student_info['department'],
    student_info['scheme']
)

# Dashboard Page
if page == "Dashboard":
    st.header(f"📊 Dashboard - {student_info['name']}")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📚 Total Classes", len(student_schedule))
    
    with col2:
        unique_subjects = len(student_schedule['subject_name'].unique())
        st.metric("📖 Subjects", unique_subjects)
    
    with col3:
        unique_teachers = len(student_schedule['teacher_name'].unique())
        st.metric("👨‍🏫 Teachers", unique_teachers)
    
    with col4:
        today = datetime.now().strftime('%A')
        today_classes = len(student_schedule[student_schedule['day'] == today])
        st.metric("🕐 Today's Classes", today_classes)
    
    st.divider()
    
    # Today's Schedule
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"📅 Today's Schedule ({datetime.now().strftime('%A')})")
        
        today = datetime.now().strftime('%A')
        today_schedule = student_schedule[student_schedule['day'] == today].sort_values('time_start')
        
        if not today_schedule.empty:
            for _, slot in today_schedule.iterrows():
                st.markdown(f"""
                <div class="class-card">
                    <strong>{slot['time_start']} - {slot['time_end']}</strong><br>
                    📚 {slot['subject_name']} ({slot['subject_code']})<br>
                    👨‍🏫 {slot['teacher_name']} | 🏛️ {slot['room_name']}<br>
                    ⚡ {slot['activity_type']}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No classes scheduled for today!")
    
    with col2:
        st.subheader("📊 Weekly Overview")
        
        daily_counts = student_schedule['day'].value_counts()
        fig = px.bar(
            x=daily_counts.values,
            y=daily_counts.index,
            orientation='h',
            title="Classes per Day"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Next Class Info
    current_time = datetime.now().strftime('%H:%M')
    upcoming_classes = today_schedule[today_schedule['time_start'] > current_time]
    
    if not upcoming_classes.empty:
        next_class = upcoming_classes.iloc[0]
        st.markdown(f"""
        <div class="info-box">
            <h4>🔔 Next Class</h4>
            <strong>{next_class['subject_name']}</strong> at <strong>{next_class['time_start']}</strong><br>
            👨‍🏫 {next_class['teacher_name']} | 🏛️ {next_class['room_name']}
        </div>
        """, unsafe_allow_html=True)

# My Timetable Page
elif page == "My Timetable":
    st.header(f"📅 My Timetable - {student_info['batch_id']} {student_info['section']}")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        day_filter = st.selectbox(
            "Filter by Day",
            options=['All'] + student_schedule['day'].unique().tolist()
        )
    
    with col2:
        subject_filter = st.selectbox(
            "Filter by Subject",
            options=['All'] + student_schedule['subject_name'].unique().tolist()
        )
    
    with col3:
        activity_filter = st.selectbox(
            "Filter by Activity",
            options=['All'] + student_schedule['activity_type'].unique().tolist()
        )
    
    # Apply filters
    filtered_schedule = student_schedule.copy()
    
    if day_filter != 'All':
        filtered_schedule = filtered_schedule[filtered_schedule['day'] == day_filter]
    if subject_filter != 'All':
        filtered_schedule = filtered_schedule[filtered_schedule['subject_name'] == subject_filter]
    if activity_filter != 'All':
        filtered_schedule = filtered_schedule[filtered_schedule['activity_type'] == activity_filter]
    
    # Download options
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Download CSV"):
            csv = filtered_schedule.to_csv(index=False)
            st.download_button(
                label="Download Timetable CSV",
                data=csv,
                file_name=f"student_{selected_student}_timetable.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📊 Download Excel"):
            output = pd.ExcelWriter(f'student_{selected_student}_timetable.xlsx', engine='openpyxl')
            filtered_schedule.to_excel(output, sheet_name='Timetable', index=False)
            output.close()
            
            with open(f'student_{selected_student}_timetable.xlsx', 'rb') as file:
                st.download_button(
                    label="Download Excel",
                    data=file.read(),
                    file_name=f"student_{selected_student}_timetable.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    st.divider()
    
    # Weekly Timetable Grid
    st.subheader("🗓️ Weekly Timetable")
    
    # Create pivot table for better display
    pivot_table = filtered_schedule.pivot_table(
        index=['time_start', 'time_end'],
        columns='day',
        values='subject_name',
        aggfunc='first',
        fill_value=''
    )
    
    st.dataframe(pivot_table, use_container_width=True)
    
    # Detailed view
    st.subheader("📋 Detailed Schedule")
    st.dataframe(filtered_schedule, use_container_width=True)

# Subjects Page
elif page == "Subjects":
    st.header("📚 My Subjects")
    
    # Get subjects from schedule
    taught_subjects = student_schedule['subject_name'].unique()
    subject_details = data['subjects'][data['subjects']['subject_name'].isin(taught_subjects)]
    
    if not subject_details.empty:
        # Subject statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📖 Total Subjects", len(subject_details))
        
        with col2:
            theory_subjects = len(subject_details[subject_details['has_lab'] == False])
            st.metric("📝 Theory Subjects", theory_subjects)
        
        with col3:
            lab_subjects = len(subject_details[subject_details['has_lab'] == True])
            st.metric("🔬 Lab Subjects", lab_subjects)
        
        # Subject cards
        for _, subject in subject_details.iterrows():
            with st.expander(f"📚 {subject['subject_name']} ({subject['subject_code']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Credits:** {subject['credits']}")
                    st.write(f"**Year:** {subject['year']}")
                    st.write(f"**Semester:** {subject['semester']}")
                
                with col2:
                    st.write(f"**Has Lab:** {'Yes' if subject['has_lab'] else 'No'}")
                    st.write(f"**Department:** {subject['department']}")
                    st.write(f"**Scheme:** {subject['scheme']}")
                
                # Get schedule for this subject
                subject_schedule = student_schedule[student_schedule['subject_name'] == subject['subject_name']]
                
                if not subject_schedule.empty:
                    st.write("**Weekly Schedule:**")
                    for _, slot in subject_schedule.iterrows():
                        st.write(f"• {slot['day']} {slot['time_start']}-{slot['time_end']} | {slot['teacher_name']} | {slot['room_name']}")
        
        # Subject distribution chart
        st.subheader("📊 Subject Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Credits distribution
            credits_data = subject_details['credits'].value_counts()
            fig = px.pie(values=credits_data.values, names=credits_data.index, title="Credits Distribution")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Lab vs Theory
            lab_count = len(subject_details[subject_details['has_lab'] == True])
            theory_count = len(subject_details[subject_details['has_lab'] == False])
            
            fig = px.bar(
                x=['Theory', 'Lab'],
                y=[theory_count, lab_count],
                title="Subject Types"
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No subjects found in your schedule.")

# Teachers Page
elif page == "Teachers":
    st.header("👨‍🏫 My Teachers")
    
    # Get teachers from schedule
    teacher_names = student_schedule['teacher_name'].unique()
    teacher_ids = student_schedule['teacher_id'].unique()
    
    teacher_details = data['teachers'][data['teachers']['teacher_id'].isin(teacher_ids)]
    
    if not teacher_details.empty:
        # Teacher statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("👨‍🏫 Total Teachers", len(teacher_details))
        
        with col2:
            departments = len(teacher_details['department'].unique())
            st.metric("🏢 Departments", departments)
        
        with col3:
            avg_experience = teacher_details['experience_years'].mean()
            st.metric("📈 Avg Experience", f"{avg_experience:.1f} years")
        
        # Teacher cards
        for _, teacher in teacher_details.iterrows():
            with st.expander(f"👨‍🏫 {teacher['name']} ({teacher['teacher_id']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Department:** {teacher['department']}")
                    st.write(f"**Designation:** {teacher['designation']}")
                    st.write(f"**Experience:** {teacher['experience_years']} years")
                    st.write(f"**Email:** {teacher['email']}")
                
                with col2:
                    st.write(f"**Qualification:** {teacher['qualification']}")
                    st.write(f"**Campus:** {teacher['preferred_campus']}")
                    st.write(f"**Specialization:** {teacher['specialization']}")
                    st.write(f"**Publications:** {teacher['publications_count']}")
                
                # Get subjects taught by this teacher
                teacher_subjects = student_schedule[student_schedule['teacher_id'] == teacher['teacher_id']]
                
                if not teacher_subjects.empty:
                    st.write("**Subjects Teaching You:**")
                    subjects = teacher_subjects['subject_name'].unique()
                    for subject in subjects:
                        subject_slots = teacher_subjects[teacher_subjects['subject_name'] == subject]
                        total_hours = len(subject_slots)
                        st.write(f"• {subject} ({total_hours} hours/week)")
        
        # Teacher analysis
        st.subheader("📊 Teacher Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Experience distribution
            exp_bins = pd.cut(teacher_details['experience_years'], bins=4)
            exp_counts = exp_bins.value_counts()
            fig = px.bar(
                x=[str(interval) for interval in exp_counts.index],
                y=exp_counts.values,
                title="Experience Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Qualification distribution
            qual_counts = teacher_details['qualification'].value_counts()
            fig = px.pie(values=qual_counts.values, names=qual_counts.index, title="Qualification Distribution")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No teachers found in your schedule.")

# Classmates Page
elif page == "Classmates":
    st.header(f"👥 My Classmates - {student_info['batch_id']} {student_info['section']}")
    
    # Get classmates
    classmates = data['students'][
        (data['students']['batch_id'] == student_info['batch_id']) & 
        (data['students']['section'] == student_info['section']) &
        (data['students']['student_id'] != selected_student)
    ]
    
    if not classmates.empty:
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Total Classmates", len(classmates))
        
        with col2:
            male_count = len(classmates[classmates['gender'] == 'Male'])
            st.metric("👨 Male", male_count)
        
        with col3:
            female_count = len(classmates[classmates['gender'] == 'Female'])
            st.metric("👩 Female", female_count)
        
        with col4:
            avg_age = 2024 - pd.to_datetime(classmates['date_of_birth']).dt.year.mean()
            st.metric("📅 Avg Age", f"{avg_age:.1f}")
        
        # Search functionality
        search_term = st.text_input("🔍 Search Classmates (by name or ID)")
        
        if search_term:
            filtered_classmates = classmates[
                classmates['name'].str.contains(search_term, case=False, na=False) |
                classmates['student_id'].str.contains(search_term, case=False, na=False)
            ]
        else:
            filtered_classmates = classmates
        
        # Classmates list
        st.subheader("📋 Classmates List")
        
        for _, classmate in filtered_classmates.iterrows():
            with st.expander(f"👤 {classmate['name']} ({classmate['student_id']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Email:** {classmate['email']}")
                    st.write(f"**Phone:** {classmate['phone']}")
                    st.write(f"**Gender:** {classmate['gender']}")
                    st.write(f"**Roll Number:** {classmate['roll_number']}")
                
                with col2:
                    st.write(f"**Date of Birth:** {classmate['date_of_birth']}")
                    st.write(f"**Blood Group:** {classmate['blood_group']}")
                    st.write(f"**Guardian:** {classmate['guardian_name']}")
                    st.write(f"**Emergency Contact:** {classmate['emergency_contact']}")
        
        # Class analytics
        st.subheader("📊 Class Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Gender distribution
            gender_counts = filtered_classmates['gender'].value_counts()
            fig = px.pie(values=gender_counts.values, names=gender_counts.index, title="Gender Distribution")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Blood group distribution
            blood_counts = filtered_classmates['blood_group'].value_counts()
            fig = px.bar(
                x=blood_counts.index,
                y=blood_counts.values,
                title="Blood Group Distribution"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Download classmates list
        if st.button("📥 Download Classmates List"):
            csv = filtered_classmates[['student_id', 'name', 'email', 'phone', 'gender', 'roll_number']].to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"classmates_{student_info['batch_id']}_{student_info['section']}.csv",
                mime="text/csv"
            )
    else:
        st.warning("No classmates found in your batch and section.")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>👨‍🎓 Smart Timetable Management System - Student Portal</p>
    <p>Stay organized with your academic schedule</p>
</div>
""", unsafe_allow_html=True)