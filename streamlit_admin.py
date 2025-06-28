import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Page config
st.set_page_config(
    page_title="Admin Portal - Smart Timetable",
    page_icon="👨‍💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #3498db, #2980b9);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #3498db;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .download-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🎯 Admin Portal - Smart Timetable Management</h1>
    <p>Complete control over academic data and timetable generation</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("📊 Admin Dashboard")
page = st.sidebar.selectbox(
    "Select Page",
    ["Overview", "Data Management", "Timetable Generator", "User Management", "Analytics"]
)

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
    st.error("❌ Unable to load CSV data. Please check if data files exist in the 'data' folder.")
    st.stop()

# Overview Page
if page == "Overview":
    st.header("📈 System Overview")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Total Students", len(data['students']))
        st.metric("🏫 Campuses", len(data['students']['primary_campus'].unique()))
    
    with col2:
        st.metric("👨‍🏫 Teachers", len(data['teachers']))
        st.metric("🏢 Departments", len(data['students']['department'].unique()))
    
    with col3:
        st.metric("📚 Subjects", len(data['subjects']))
        st.metric("📝 Batches", len(data['students']['batch_id'].unique()))
    
    with col4:
        st.metric("🏛️ Rooms", len(data['rooms']))
        st.metric("⚡ Activities", len(data['activities']))
    
    st.divider()
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Students by department
        dept_counts = data['students']['department'].value_counts()
        fig = px.pie(
            values=dept_counts.values,
            names=dept_counts.index,
            title="Students Distribution by Department"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Students by campus
        campus_counts = data['students']['primary_campus'].value_counts()
        fig = px.bar(
            x=campus_counts.index,
            y=campus_counts.values,
            title="Students Distribution by Campus"
        )
        st.plotly_chart(fig, use_container_width=True)

# Data Management Page
elif page == "Data Management":
    st.header("📋 Data Management")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Students", "Teachers", "Subjects", "Rooms", "Activities"])
    
    with tab1:
        st.subheader("👥 Students Data")
        st.dataframe(data['students'], use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Download Students CSV"):
                csv = data['students'].to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"students_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("📊 Download Students Excel"):
                # Convert to Excel
                output = pd.ExcelWriter('temp_students.xlsx', engine='openpyxl')
                data['students'].to_excel(output, sheet_name='Students', index=False)
                output.close()
                
                with open('temp_students.xlsx', 'rb') as file:
                    st.download_button(
                        label="Download Excel",
                        data=file.read(),
                        file_name=f"students_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
    
    with tab2:
        st.subheader("👨‍🏫 Teachers Data")
        st.dataframe(data['teachers'], use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Download Teachers CSV"):
                csv = data['teachers'].to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"teachers_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
    
    with tab3:
        st.subheader("📚 Subjects Data")
        st.dataframe(data['subjects'], use_container_width=True)
    
    with tab4:
        st.subheader("🏛️ Rooms Data")
        st.dataframe(data['rooms'], use_container_width=True)
    
    with tab5:
        st.subheader("⚡ Activities Data")
        st.dataframe(data['activities'], use_container_width=True)

# Timetable Generator Page
elif page == "Timetable Generator":
    st.header("🎯 Smart Timetable Generator")
    
    st.info("🚀 Generate optimized timetables using AI-powered algorithms")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⚙️ Generation Parameters")
        
        selected_batches = st.multiselect(
            "Select Batches",
            options=data['students']['batch_id'].unique(),
            default=data['students']['batch_id'].unique()[:5]
        )
        
        selected_campuses = st.multiselect(
            "Select Campuses",
            options=data['students']['primary_campus'].unique(),
            default=data['students']['primary_campus'].unique()
        )
        
        time_preference = st.selectbox(
            "Time Preference",
            ["Morning Heavy", "Balanced", "Evening Heavy"]
        )
        
        include_labs = st.checkbox("Include Lab Sessions", value=True)
        include_tutorials = st.checkbox("Include Tutorials", value=True)
    
    with col2:
        st.subheader("📊 Preview Statistics")
        
        if selected_batches:
            filtered_students = data['students'][data['students']['batch_id'].isin(selected_batches)]
            
            st.metric("Students Affected", len(filtered_students))
            st.metric("Departments", len(filtered_students['department'].unique()))
            st.metric("Sections", len(filtered_students['section'].unique()))
            
            # Show batch distribution
            batch_counts = filtered_students['batch_id'].value_counts()
            fig = px.bar(
                x=batch_counts.index,
                y=batch_counts.values,
                title="Students per Batch"
            )
            st.plotly_chart(fig, use_container_width=True, height=300)
    
    st.divider()
    
    if st.button("🚀 Generate Smart Timetable", type="primary"):
        with st.spinner("Generating optimized timetable..."):
            progress_bar = st.progress(0)
            
            # Simulate timetable generation process
            for i in range(100):
                progress_bar.progress(i + 1)
                
            st.success("✅ Timetable generated successfully!")
            
            # Show generation summary
            st.subheader("📋 Generation Summary")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Slots Generated", "1,248")
                st.metric("Conflicts Resolved", "23")
            
            with col2:
                st.metric("Resource Utilization", "94%")
                st.metric("Optimization Score", "8.7/10")
            
            with col3:
                st.metric("Generation Time", "2.3s")
                st.metric("Quality Index", "Excellent")

# User Management Page
elif page == "User Management":
    st.header("👤 User Management")
    
    st.info("💡 Register users with role-based access control")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("➕ Add New User")
        
        with st.form("user_form"):
            username = st.text_input("Username")
            email = st.text_input("Email")
            full_name = st.text_input("Full Name")
            role = st.selectbox("Role", ["admin", "teacher", "student"])
            
            if role == "teacher":
                teacher_id = st.selectbox(
                    "Teacher ID",
                    options=data['teachers']['teacher_id'].tolist()
                )
            elif role == "student":
                student_id = st.selectbox(
                    "Student ID",
                    options=data['students']['student_id'].tolist()
                )
            
            password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            submitted = st.form_submit_button("Create User")
            
            if submitted:
                if password != confirm_password:
                    st.error("Passwords don't match!")
                elif len(password) < 6:
                    st.error("Password must be at least 6 characters!")
                else:
                    st.success(f"✅ User {username} created successfully!")
    
    with col2:
        st.subheader("📊 User Statistics")
        
        # Sample user data
        user_data = {
            'Role': ['Admin', 'Teacher', 'Student'],
            'Count': [5, 23, 156],
            'Status': ['Active', 'Active', 'Active']
        }
        
        df = pd.DataFrame(user_data)
        st.dataframe(df, use_container_width=True)
        
        # Pie chart
        fig = px.pie(
            values=df['Count'],
            names=df['Role'],
            title="User Distribution by Role"
        )
        st.plotly_chart(fig, use_container_width=True)

# Analytics Page
elif page == "Analytics":
    st.header("📊 Advanced Analytics")
    
    tab1, tab2, tab3 = st.tabs(["Resource Utilization", "Performance Metrics", "Reports"])
    
    with tab1:
        st.subheader("🏛️ Room Utilization")
        
        # Room utilization chart
        room_util_data = {
            'Campus': ['Campus-3', 'Campus-8', 'Campus-15B', 'KIIT Stadium'],
            'Utilization': [87, 92, 78, 65],
            'Capacity': [1200, 800, 950, 500]
        }
        
        df = pd.DataFrame(room_util_data)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Utilization %',
            x=df['Campus'],
            y=df['Utilization'],
            yaxis='y'
        ))
        fig.add_trace(go.Scatter(
            name='Capacity',
            x=df['Campus'],
            y=df['Capacity'],
            yaxis='y2',
            mode='lines+markers'
        ))
        
        fig.update_layout(
            title='Campus Resource Utilization',
            yaxis=dict(title='Utilization %'),
            yaxis2=dict(title='Capacity', overlaying='y', side='right')
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("⚡ System Performance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Performance metrics
            perf_metrics = {
                'Metric': ['Response Time', 'Uptime', 'Data Accuracy', 'User Satisfaction'],
                'Value': [120, 99.9, 98.5, 94.2],
                'Unit': ['ms', '%', '%', '%']
            }
            
            df = pd.DataFrame(perf_metrics)
            st.dataframe(df, use_container_width=True)
        
        with col2:
            # Performance trend
            import numpy as np
            dates = pd.date_range('2024-01-01', periods=30, freq='D')
            performance = 95 + np.random.normal(0, 2, 30)
            
            fig = px.line(
                x=dates,
                y=performance,
                title='System Performance Trend (30 days)'
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.subheader("📋 Generate Reports")
        
        report_type = st.selectbox(
            "Report Type",
            ["Student Enrollment", "Teacher Workload", "Room Utilization", "Academic Performance"]
        )
        
        date_range = st.date_input(
            "Date Range",
            value=[datetime.now().date(), datetime.now().date()],
            format="YYYY-MM-DD"
        )
        
        if st.button("📊 Generate Report"):
            st.success(f"✅ {report_type} report generated for {date_range}")
            
            # Show sample report data
            st.subheader(f"📈 {report_type} Report")
            
            if report_type == "Student Enrollment":
                st.dataframe(data['students'].head(10), use_container_width=True)
            elif report_type == "Teacher Workload":
                st.dataframe(data['teachers'].head(10), use_container_width=True)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <p>🎯 Smart Timetable Management System - Admin Portal</p>
    <p>Built with Streamlit • Real-time Data • AI-Powered</p>
</div>
""", unsafe_allow_html=True)