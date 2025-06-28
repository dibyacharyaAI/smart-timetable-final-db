import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

# Page config
st.set_page_config(
    page_title="Teacher Portal - Smart Timetable",
    page_icon="👨‍🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #27ae60, #229954);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .schedule-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #27ae60;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .time-slot {
        background: #e8f5e8;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.25rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>👨‍🏫 Teacher Portal - Smart Timetable Management</h1>
    <p>Manage your classes, view schedules, and track student progress</p>
</div>
""", unsafe_allow_html=True)

# Teacher Selection
st.sidebar.title("👨‍🏫 Teacher Dashboard")

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

# Teacher selection
teacher_ids = data['teachers']['teacher_id'].tolist()
selected_teacher = st.sidebar.selectbox(
    "Select Teacher ID",
    options=teacher_ids,
    index=0
)

# Get teacher info
teacher_info = data['teachers'][data['teachers']['teacher_id'] == selected_teacher].iloc[0]

st.sidebar.markdown(f"""
### Teacher Information
**Name:** {teacher_info['name']}  
**Department:** {teacher_info['department']}  
**Campus:** {teacher_info['preferred_campus']}  
**Experience:** {teacher_info['experience_years']} years  
**Qualification:** {teacher_info['qualification']}
""")

page = st.sidebar.selectbox(
    "Select Page",
    ["Dashboard", "My Timetable", "Students", "Subjects", "Room Management"]
)

# Generate mock timetable for teacher
@st.cache_data
def generate_teacher_timetable(teacher_id):
    teacher_data = data['teachers'][data['teachers']['teacher_id'] == teacher_id].iloc[0]
    
    # Get teacher's subject expertise
    expertise = str(teacher_data['subject_expertise']).split(', ')
    primary_subjects = str(teacher_data['primary_subjects']).split(', ')
    
    # Find matching subjects
    teacher_subjects = data['subjects'][
        data['subjects']['subject_name'].str.contains('|'.join(expertise), case=False, na=False)
    ]
    
    if teacher_subjects.empty:
        teacher_subjects = data['subjects'].sample(3)
    
    # Generate weekly schedule
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    time_slots = [
        ('08:00', '09:00'), ('09:00', '10:00'), ('10:00', '11:00'),
        ('11:20', '12:20'), ('13:00', '14:00'), ('14:00', '15:00'),
        ('15:00', '16:00'), ('16:00', '17:00')
    ]
    
    schedule = []
    campus_rooms = data['rooms'][data['rooms']['campus'] == teacher_data['preferred_campus']]
    
    for day in days:
        for i, (start_time, end_time) in enumerate(time_slots):
            if i < 3:  # Morning slots
                subject = teacher_subjects.sample(1).iloc[0]
                room = campus_rooms.sample(1).iloc[0]
                
                schedule.append({
                    'day': day,
                    'time_start': start_time,
                    'time_end': end_time,
                    'subject_name': subject['subject_name'],
                    'subject_code': subject['subject_code'],
                    'room_name': room['room_name'],
                    'batch_id': f"A{(i%5)+1:02d}",
                    'activity_type': 'Lab' if subject['has_lab'] else 'Lecture',
                    'campus': teacher_data['preferred_campus']
                })
    
    return pd.DataFrame(schedule)

teacher_schedule = generate_teacher_timetable(selected_teacher)

# Dashboard Page
if page == "Dashboard":
    st.header(f"📊 Dashboard - {teacher_info['name']}")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📚 Total Classes", len(teacher_schedule))
    
    with col2:
        unique_subjects = len(teacher_schedule['subject_name'].unique())
        st.metric("📖 Subjects Teaching", unique_subjects)
    
    with col3:
        unique_batches = len(teacher_schedule['batch_id'].unique())
        st.metric("👥 Batches", unique_batches)
    
    with col4:
        today = datetime.now().strftime('%A')
        today_classes = len(teacher_schedule[teacher_schedule['day'] == today])
        st.metric("🕐 Today's Classes", today_classes)
    
    st.divider()
    
    # Today's Schedule
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader(f"📅 Today's Schedule ({datetime.now().strftime('%A')})")
        
        today = datetime.now().strftime('%A')
        today_schedule = teacher_schedule[teacher_schedule['day'] == today].sort_values('time_start')
        
        if not today_schedule.empty:
            for _, slot in today_schedule.iterrows():
                st.markdown(f"""
                <div class="schedule-card">
                    <strong>{slot['time_start']} - {slot['time_end']}</strong><br>
                    📚 {slot['subject_name']} ({slot['subject_code']})<br>
                    👥 Batch: {slot['batch_id']} | 🏛️ {slot['room_name']}<br>
                    ⚡ {slot['activity_type']}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No classes scheduled for today!")
    
    with col2:
        st.subheader("📊 Weekly Distribution")
        
        daily_counts = teacher_schedule['day'].value_counts()
        fig = px.bar(
            x=daily_counts.values,
            y=daily_counts.index,
            orientation='h',
            title="Classes per Day"
        )
        st.plotly_chart(fig, use_container_width=True)

# My Timetable Page
elif page == "My Timetable":
    st.header(f"📅 My Timetable - {teacher_info['name']}")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        day_filter = st.selectbox(
            "Filter by Day",
            options=['All'] + teacher_schedule['day'].unique().tolist()
        )
    
    with col2:
        subject_filter = st.selectbox(
            "Filter by Subject",
            options=['All'] + teacher_schedule['subject_name'].unique().tolist()
        )
    
    with col3:
        activity_filter = st.selectbox(
            "Filter by Activity",
            options=['All'] + teacher_schedule['activity_type'].unique().tolist()
        )
    
    # Apply filters
    filtered_schedule = teacher_schedule.copy()
    
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
                file_name=f"teacher_{selected_teacher}_timetable.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📊 Download Excel"):
            # Create Excel file
            output = pd.ExcelWriter(f'teacher_{selected_teacher}_timetable.xlsx', engine='openpyxl')
            filtered_schedule.to_excel(output, sheet_name='Timetable', index=False)
            output.close()
            
            with open(f'teacher_{selected_teacher}_timetable.xlsx', 'rb') as file:
                st.download_button(
                    label="Download Excel",
                    data=file.read(),
                    file_name=f"teacher_{selected_teacher}_timetable.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    st.divider()
    
    # Timetable display
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

# Students Page
elif page == "Students":
    st.header("👥 My Students")
    
    # Get batches taught by teacher
    taught_batches = teacher_schedule['batch_id'].unique()
    
    # Filter students
    my_students = data['students'][data['students']['batch_id'].isin(taught_batches)]
    
    if not my_students.empty:
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Total Students", len(my_students))
        
        with col2:
            st.metric("🏫 Departments", len(my_students['department'].unique()))
        
        with col3:
            st.metric("📚 Batches", len(my_students['batch_id'].unique()))
        
        with col4:
            st.metric("🏢 Sections", len(my_students['section'].unique()))
        
        # Filters
        col1, col2 = st.columns(2)
        
        with col1:
            batch_filter = st.selectbox(
                "Filter by Batch",
                options=['All'] + my_students['batch_id'].unique().tolist()
            )
        
        with col2:
            section_filter = st.selectbox(
                "Filter by Section",
                options=['All'] + my_students['section'].unique().tolist()
            )
        
        # Apply filters
        filtered_students = my_students.copy()
        
        if batch_filter != 'All':
            filtered_students = filtered_students[filtered_students['batch_id'] == batch_filter]
        if section_filter != 'All':
            filtered_students = filtered_students[filtered_students['section'] == section_filter]
        
        # Student distribution charts
        col1, col2 = st.columns(2)
        
        with col1:
            batch_counts = filtered_students['batch_id'].value_counts()
            fig = px.pie(values=batch_counts.values, names=batch_counts.index, title="Students by Batch")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            gender_counts = filtered_students['gender'].value_counts()
            fig = px.bar(x=gender_counts.index, y=gender_counts.values, title="Students by Gender")
            st.plotly_chart(fig, use_container_width=True)
        
        # Students table
        st.subheader("📋 Student List")
        st.dataframe(filtered_students[['student_id', 'name', 'email', 'batch_id', 'section', 'department']], use_container_width=True)
        
        # Download button
        if st.button("📥 Download Student List"):
            csv = filtered_students.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"students_teacher_{selected_teacher}.csv",
                mime="text/csv"
            )
    else:
        st.warning("No students found for your classes.")

# Subjects Page
elif page == "Subjects":
    st.header("📚 My Subjects")
    
    # Get subjects taught by teacher
    taught_subjects = teacher_schedule['subject_name'].unique()
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
        
        # Subject details
        for _, subject in subject_details.iterrows():
            with st.expander(f"📚 {subject['subject_name']} ({subject['subject_code']})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Department:** {subject['department']}")
                    st.write(f"**Credits:** {subject['credits']}")
                    st.write(f"**Scheme:** {subject['scheme']}")
                
                with col2:
                    st.write(f"**Has Lab:** {'Yes' if subject['has_lab'] else 'No'}")
                    st.write(f"**Year:** {subject['year']}")
                    st.write(f"**Semester:** {subject['semester']}")
                
                # Get teaching schedule for this subject
                subject_schedule = teacher_schedule[teacher_schedule['subject_name'] == subject['subject_name']]
                
                if not subject_schedule.empty:
                    st.write("**Weekly Schedule:**")
                    for _, slot in subject_schedule.iterrows():
                        st.write(f"• {slot['day']} {slot['time_start']}-{slot['time_end']} | {slot['room_name']} | {slot['batch_id']}")
    else:
        st.warning("No subjects found in your schedule.")

# Room Management Page
elif page == "Room Management":
    st.header("🏛️ Room Management")
    
    # Get rooms used by teacher
    used_rooms = teacher_schedule['room_name'].unique()
    campus_rooms = data['rooms'][data['rooms']['campus'] == teacher_info['preferred_campus']]
    
    # Room utilization
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏛️ My Rooms")
        room_usage = teacher_schedule['room_name'].value_counts()
        
        for room, count in room_usage.items():
            room_info = data['rooms'][data['rooms']['room_name'] == room].iloc[0]
            
            st.markdown(f"""
            <div class="schedule-card">
                <strong>{room}</strong> ({room_info['room_id']})<br>
                📍 {room_info['campus']} | 🪑 Capacity: {room_info['capacity']}<br>
                📊 Weekly Usage: {count} hours
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("📊 Room Utilization")
        
        fig = px.bar(
            x=room_usage.values,
            y=room_usage.index,
            orientation='h',
            title="Hours per Room"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Available rooms on campus
    st.subheader(f"🏢 Available Rooms at {teacher_info['preferred_campus']}")
    
    room_type_filter = st.selectbox(
        "Filter by Room Type",
        options=['All'] + campus_rooms['room_type'].unique().tolist()
    )
    
    filtered_rooms = campus_rooms.copy()
    if room_type_filter != 'All':
        filtered_rooms = filtered_rooms[filtered_rooms['room_type'] == room_type_filter]
    
    st.dataframe(filtered_rooms[['room_id', 'room_name', 'room_type', 'capacity', 'equipment']], use_container_width=True)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>👨‍🏫 Smart Timetable Management System - Teacher Portal</p>
    <p>Manage your academic schedule efficiently</p>
</div>
""", unsafe_allow_html=True)