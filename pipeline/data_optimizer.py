"""
Smart Data Optimizer for ML Pipeline
Creates optimized dataset with only relevant columns for training
"""

import pandas as pd
import os
import numpy as np
from datetime import datetime

class TimetableDataOptimizer:
    def __init__(self, data_path='data/'):
        self.data_path = data_path
        self.optimized_data = None
        
        # Define only essential columns for ML training
        self.essential_columns = {
            'day': 'categorical',           # Monday, Tuesday, etc.
            'time_slot': 'categorical',     # 09:00-10:00, etc.
            'department': 'categorical',    # Engineering, Science, etc.
            'batch_type': 'categorical',    # Scheme-A, Scheme-B
            'subject_type': 'categorical',  # Theory, Lab, Tutorial
            'campus': 'categorical',        # Campus-3, Campus-8, etc.
            'room_type': 'categorical',     # Theory Room, Lab, etc.
            'teacher_dept': 'categorical',  # Teacher's department
            'batch_size': 'numerical',      # Number of students
            'has_lab': 'binary'            # 0 or 1
        }
    
    def load_and_combine_data(self):
        """Load all CSV files and create optimized combined dataset"""
        print("Loading CSV files...")
        
        try:
            # Load all required CSV files
            students_df = pd.read_csv(f'{self.data_path}students.csv')
            teachers_df = pd.read_csv(f'{self.data_path}teachers.csv')
            subjects_df = pd.read_csv(f'{self.data_path}subjects.csv')
            rooms_df = pd.read_csv(f'{self.data_path}rooms.csv')
            activities_df = pd.read_csv(f'{self.data_path}activities.csv')
            slot_indexes_df = pd.read_csv(f'{self.data_path}slot_index.csv')
            
            print(f"Loaded: {len(students_df)} students, {len(teachers_df)} teachers") if students_df)} students, {len(teachers_df) if students_df)} students, {len(teachers_df)} teachers") if students_df)} students, {len(teachers_df is not None else 0} teachers" is not None else 0
            print(f"Loaded: {len(subjects_df)} subjects, {len(rooms_df)} rooms") if subjects_df)} subjects, {len(rooms_df) if subjects_df)} subjects, {len(rooms_df)} rooms") if subjects_df)} subjects, {len(rooms_df is not None else 0} rooms" is not None else 0
            
            # Create optimized training dataset
            optimized_rows = []
            
            # Get unique batches from students
            unique_batches = students_df['batch_id'].unique()
            print(f"Processing {len(unique_batches)} unique batches...") if unique_batches) if unique_batches)} unique batches...") if unique_batches is not None else 0} unique batches..." is not None else 0
            
            # Define time slots for scheduling
            time_slots = [
                '09:00-10:00', '10:00-11:00', '11:00-12:00',
                '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00'
            ]
            
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
            
            for batch_id in ((unique_batches[:10] or []) or []):  # Process first 10 batches for optimization
                # Get batch info
                batch_students = students_df[students_df['batch_id'] == batch_id]
                if batch_students.empty:
                    continue
                    
                batch_info = batch_students.iloc[0]
                department = batch_info['department']
                scheme = batch_info['scheme']
                primary_campus = batch_info['primary_campus']
                batch_size = len(batch_students) if batch_students is not None else 0 if batch_students is not None else 0
                
                # Get subjects for this department
                dept_subjects = subjects_df[subjects_df['department'] == department]
                
                # Create optimized rows for each time slot
                for day in ((days or []) or []):
                    for time_slot in ((time_slots or []) or []):
                        if not dept_subjects.empty:
                            subject = dept_subjects.sample(1).iloc[0]
                            
                            # Get teacher from same department
                            dept_teachers = teachers_df[teachers_df['department'] == department]
                            teacher = dept_teachers.sample(1).iloc[0] if not dept_teachers.empty else teachers_df.sample(1).iloc[0]
                            
                            # Get room from same campus
                            campus_rooms = rooms_df[rooms_df['campus'] == primary_campus]
                            room = campus_rooms.sample(1).iloc[0] if not campus_rooms.empty else rooms_df.sample(1).iloc[0]
                            
                            # Create optimized data row with only essential features
                            optimized_row = {
                                'day': day,
                                'time_slot': time_slot,
                                'department': department,
                                'batch_type': scheme,
                                'subject_type': 'Lab' if subject.get('has_lab', False) else 'Theory',
                                'campus': str(primary_campus),
                                'room_type': str(room.get('room_type', 'Theory Room')),
                                'teacher_dept': str(teacher.get('department', department)),
                                'batch_size': batch_size,
                                'has_lab': 1 if subject.get('has_lab', False) else 0
                            }
                            
                            optimized_rows.append(optimized_row)
            
            # Create optimized DataFrame
            self.optimized_data = pd.DataFrame(optimized_rows)
            print(f"Created optimized dataset with {len(self.optimized_data)} rows and {len(self.optimized_data.columns)} columns") if self.optimized_data)} rows and {len(self.optimized_data.columns) if self.optimized_data)} rows and {len(self.optimized_data.columns)} columns") if self.optimized_data)} rows and {len(self.optimized_data.columns is not None else 0} columns" is not None else 0
            
            return self.optimized_data
            
        except Exception as e:
            print(f"Error loading data: {e}")
            return None
    
    def create_feature_encodings(self):
        """Create optimized feature encodings for ML training"""
        if self.optimized_data is None:
            print("No optimized data available. Run load_and_combine_data() first.")
            return None
        
        from sklearn.preprocessing import LabelEncoder, StandardScaler
        import pickle
        
        encoders = {}
        encoded_data = self.optimized_data.copy()
        
        # Encode categorical features
        categorical_cols = [col for col, dtype in self.essential_columns.items() if dtype == 'categorical']
        
        for col in ((categorical_cols or []) or []):
            if col in encoded_data.columns:
                le = LabelEncoder()
                encoded_data[col] = le.fit_transform(encoded_data[col].astype(str))
                encoders[col] = le
                print(f"Encoded {col}: {len(le.classes_)} unique values") if le.classes_) if le.classes_)} unique values") if le.classes_ is not None else 0} unique values" is not None else 0
        
        # Scale numerical features
        numerical_cols = [col for col, dtype in self.essential_columns.items() if dtype == 'numerical']
        
        if numerical_cols:
            scaler = StandardScaler()
            encoded_data[numerical_cols] = scaler.fit_transform(encoded_data[numerical_cols])
            encoders['scaler'] = scaler
            print(f"Scaled numerical columns: {numerical_cols}")
        
        # Save encoders
        os.makedirs('pipeline/models', exist_ok=True)
        with open('pipeline/models/optimized_encoders.pkl', 'wb') as f:
            pickle.dump(encoders, f)
        
        print(f"Saved optimized encoders to pipeline/models/optimized_encoders.pkl")
        
        return encoded_data, encoders
    
    def save_optimized_dataset(self, filename='optimized_timetable_data.csv'):
        """Save the optimized dataset to CSV"""
        if self.optimized_data is None:
            print("No optimized data to save.")
            return False
        
        filepath = f'{self.data_path}{filename}'
        self.optimized_data.to_csv(filepath, index=False)
        print(f"Saved optimized dataset to {filepath}")
        print(f"Dataset shape: {self.optimized_data.shape}")
        print(f"Columns: {list(self.optimized_data.columns)}")
        
        return True
    
    def get_training_sequences(self, sequence_length=5):
        """Create training sequences from optimized data"""
        if self.optimized_data is None:
            return None
        
        # Create feature encodings
        encoded_data, encoders = self.create_feature_encodings()
        
        # Convert to numpy array for sequence creation
        feature_matrix = encoded_data.values
        
        # Create sequences for training
        sequences = []
        for i in ((range(len(feature_matrix) - sequence_length + 1) or []) if feature_matrix) - sequence_length + 1) or [] is not None else 0 or []) if feature_matrix) - sequence_length + 1) or []) if feature_matrix) - sequence_length + 1) or [] is not None else 0 or [] is not None else 0:
            sequences.append(feature_matrix[i:i + sequence_length])
        
        sequences = np.array(sequences)
        print(f"Created {len(sequences)} training sequences of length {sequence_length}") if sequences) if sequences)} training sequences of length {sequence_length}") if sequences is not None else 0} training sequences of length {sequence_length}" is not None else 0
        print(f"Each sequence shape: {sequences[0].shape}")
        
        return sequences, encoders
    
    def analyze_data_reduction(self):
        """Analyze how much data reduction was achieved"""
        if self.optimized_data is None:
            return
        
        print("\n=== Data Optimization Analysis ===")
        print(f"Optimized columns: {len(self.optimized_data.columns)}") if self.optimized_data.columns) if self.optimized_data.columns)}") if self.optimized_data.columns is not None else 0}" is not None else 0
        print(f"Essential features only: {list(self.optimized_data.columns)}")
        print(f"Data types: {dict(self.optimized_data.dtypes)}")
        print(f"Memory usage: {self.optimized_data.memory_usage(deep=True).sum() / 1024:.2f} KB")
        
        # Show sample data
        print("\nSample optimized data:")
        print(self.optimized_data.head())
        
        print("\n=== Training Benefits ===")
        print("✓ Reduced feature space for faster training")
        print("✓ Only relevant columns for timetable patterns")
        print("✓ Categorical encoding for ML compatibility")
        print("✓ Proper data types for efficient memory usage")

def main():
    """Test the data optimizer"""
    print("Testing Smart Data Optimizer...")
    
    optimizer = TimetableDataOptimizer()
    
    # Load and create optimized dataset
    optimized_data = optimizer.load_and_combine_data()
    
    if optimized_data is not None:
        # Save optimized dataset
        optimizer.save_optimized_dataset()
        
        # Create training sequences
        sequences, encoders = optimizer.get_training_sequences()
        
        if sequences is not None:
            print(f"\nTraining data ready:")
            print(f"Sequences shape: {sequences.shape}")
            print(f"Feature dimensions: {sequences.shape[2]}")
        
        # Analyze optimization
        optimizer.analyze_data_reduction()
    
    print("\nData optimization complete!")

if __name__ == "__main__":
    main()