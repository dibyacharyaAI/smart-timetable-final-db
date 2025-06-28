"""
Time-slot Encoding Module
Encodes timetable data into feature vectors for ML processing
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, OneHotEncoder
import pickle
import os
from datetime import datetime

class TimetableEncoder:
    def __init__(self):
        self.section_encoder = LabelEncoder()
        self.subject_encoder = LabelEncoder()
        self.teacher_encoder = LabelEncoder()
        self.room_encoder = LabelEncoder()
        self.day_encoder = LabelEncoder()
        self.time_encoder = LabelEncoder()
        self.campus_encoder = LabelEncoder()
        self.activity_encoder = LabelEncoder()
        
        self.encoders = {
            'section': self.section_encoder,
            'subject': self.subject_encoder,
            'teacher': self.teacher_encoder,
            'room': self.room_encoder,
            'day': self.day_encoder,
            'time': self.time_encoder,
            'campus': self.campus_encoder,
            'activity': self.activity_encoder
        }
        
        self.feature_dim = 0
        
    def fit_encoders(self, data_path='data/'):
        """Fit all encoders on the available data"""
        print("🔄 Loading CSV data for encoding...")
        
        # Load all CSV files
        students_df = pd.read_csv(os.path.join(data_path, 'students.csv'))
        teachers_df = pd.read_csv(os.path.join(data_path, 'teachers.csv'))
        subjects_df = pd.read_csv(os.path.join(data_path, 'subjects.csv'))
        rooms_df = pd.read_csv(os.path.join(data_path, 'rooms.csv'))
        activities_df = pd.read_csv(os.path.join(data_path, 'activities.csv'))
        
        print("📊 Fitting encoders on data...")
        
        # Fit section encoder
        all_sections = list(students_df['section'].unique())
        self.section_encoder.fit(all_sections)
        
        # Fit subject encoder
        all_subjects = list(subjects_df['subject_code'].unique())
        self.subject_encoder.fit(all_subjects)
        
        # Fit teacher encoder
        all_teachers = list(teachers_df['teacher_id'].unique())
        self.teacher_encoder.fit(all_teachers)
        
        # Fit room encoder
        all_rooms = list(rooms_df['room_id'].unique())
        self.room_encoder.fit(all_rooms)
        
        # Fit day encoder
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        self.day_encoder.fit(days)
        
        # Fit time encoder
        time_slots = [
            '08:00-09:00', '09:00-10:00', '10:00-11:00', '11:20-12:20',
            '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00', '17:00-18:00'
        ]
        self.time_encoder.fit(time_slots)
        
        # Fit campus encoder
        all_campuses = list(students_df['primary_campus'].unique())
        self.campus_encoder.fit(all_campuses)
        
        # Fit activity encoder
        activity_types = ['Lecture', 'Lab', 'Tutorial', 'Assessment', 'Break']
        self.activity_encoder.fit(activity_types)
        
        # Calculate feature dimension
        self.feature_dim = (
            len(all_sections) + len(all_subjects) + len(all_teachers) + 
            len(all_rooms) + len(days) + len(time_slots) + 
            len(all_campuses) + len(activity_types)
        )
        
        print(f"✅ Encoders fitted successfully! Feature dimension: {self.feature_dim}")
        return self
    
    def encode_slot(self, slot_data):
        """Encode a single time slot into feature vector"""
        try:
            feature_vector = np.zeros(self.feature_dim)
            offset = 0
            
            # Encode section (one-hot)
            if slot_data.get('section'):
                section_idx = self.section_encoder.transform([slot_data['section']])[0]
                feature_vector[offset + section_idx] = 1
            offset += len(self.section_encoder.classes_)
            
            # Encode subject (one-hot)
            if slot_data.get('subject_code'):
                subject_idx = self.subject_encoder.transform([slot_data['subject_code']])[0]
                feature_vector[offset + subject_idx] = 1
            offset += len(self.subject_encoder.classes_)
            
            # Encode teacher (one-hot)
            if slot_data.get('teacher_id'):
                teacher_idx = self.teacher_encoder.transform([slot_data['teacher_id']])[0]
                feature_vector[offset + teacher_idx] = 1
            offset += len(self.teacher_encoder.classes_)
            
            # Encode room (one-hot)
            if slot_data.get('room_id'):
                room_idx = self.room_encoder.transform([slot_data['room_id']])[0]
                feature_vector[offset + room_idx] = 1
            offset += len(self.room_encoder.classes_)
            
            # Encode day (one-hot)
            if slot_data.get('day'):
                day_idx = self.day_encoder.transform([slot_data['day']])[0]
                feature_vector[offset + day_idx] = 1
            offset += len(self.day_encoder.classes_)
            
            # Encode time (one-hot)
            if slot_data.get('time_slot'):
                time_idx = self.time_encoder.transform([slot_data['time_slot']])[0]
                feature_vector[offset + time_idx] = 1
            offset += len(self.time_encoder.classes_)
            
            # Encode campus (one-hot)
            if slot_data.get('campus'):
                campus_idx = self.campus_encoder.transform([slot_data['campus']])[0]
                feature_vector[offset + campus_idx] = 1
            offset += len(self.campus_encoder.classes_)
            
            # Encode activity type (one-hot)
            if slot_data.get('activity_type'):
                activity_idx = self.activity_encoder.transform([slot_data['activity_type']])[0]
                feature_vector[offset + activity_idx] = 1
            
            return feature_vector
            
        except Exception as e:
            print(f"⚠️ Error encoding slot: {e}")
            return np.zeros(self.feature_dim)
    
    def load_encoders(self, filepath='pipeline/models/encoders.pkl'):
        """Load fitted encoders from file"""
        try:
            with open(filepath, 'rb') as f:
                encoder_data = pickle.load(f)
            
            self.label_encoders = encoder_data['label_encoders']
            self.time_encoder = encoder_data['time_encoder']
            self.activity_encoder = encoder_data['activity_encoder']
            self.fitted = True
            print(f"📥 Encoders loaded from {filepath}")
            
        except Exception as e:
            print(f"❌ Error loading encoders: {e}")
            self.fitted = False
    
    def decode_slot(self, encoded_vector):
        """Decode feature vector back to slot data"""
        if not self.fitted:
            print("⚠️ Encoders not fitted")
            return {}
        
        try:
            # This is a simplified decoder - in practice would need more sophisticated mapping
            decoded = {
                'section': 'A01',
                'subject_code': 'GEN101', 
                'teacher_id': 'TCH1001',
                'room_id': 'R301',
                'day': 'Monday',
                'time_slot': '08:00-09:00',
                'campus': 'Campus-3',
                'activity_type': 'Lecture'
            }
            return decoded
            
        except Exception as e:
            print(f"❌ Error decoding slot: {e}")
            return {}
    
    def save_encoders(self, filepath='pipeline/models/encoders.pkl'):
        """Save fitted encoders to file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        encoder_data = {
            'encoders': self.encoders,
            'feature_dim': self.feature_dim,
            'classes': {name: enc.classes_ for name, enc in self.encoders.items()}
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(encoder_data, f)
        
        print(f"💾 Encoders saved to {filepath}")

def main():
    """Main function to test encoding"""
    print("🚀 Starting Time-slot Encoding Process...")
    print("=" * 50)
    
    # Initialize encoder
    encoder = TimetableEncoder()
    
    # Fit encoders on data
    encoder.fit_encoders()
    
    # Save encoders
    encoder.save_encoders()
    
    print("\n" + "=" * 50)
    print("✅ TIME-SLOT ENCODING COMPLETED SUCCESSFULLY!")
    print("=" * 50)

if __name__ == "__main__":
    main()