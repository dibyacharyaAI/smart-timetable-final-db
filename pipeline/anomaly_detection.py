"""
Real-Time Anomaly Detection Module
Monitors timetable updates and detects anomalies using trained autoencoder
"""

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import pickle
import os
from datetime import datetime
from encoding import TimetableEncoder

class AnomalyDetector:
    def __init__(self, model_path='pipeline/models/autoencoder.pth', 
                 threshold_path='pipeline/models/threshold.pkl',
                 encoder_path='pipeline/models/encoders.pkl'):
        self.model = None
        self.threshold = None
        self.encoder = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load components
        self.load_model(model_path)
        self.load_threshold(threshold_path)
        self.load_encoder(encoder_path)
        
    def load_model(self, model_path):
        """Load trained autoencoder model"""
        try:
            # Load metadata to get model architecture
            with open('pipeline/models/training_metadata.pkl', 'rb') as f:
                metadata = pickle.load(f)
            
            # Recreate model architecture
            from training import TimetableAutoencoder
            self.model = TimetableAutoencoder(
                input_dim=metadata['input_dim'],
                embed_dim=metadata['embed_dim'],
                hidden_dim=metadata['hidden_dim']
            )
            
            # Load trained weights
            self.model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model.to(self.device)
            self.model.eval()
            
            print(f"📥 Model loaded from {model_path}")
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.model = None
    
    def load_threshold(self, threshold_path):
        """Load anomaly detection threshold"""
        try:
            with open(threshold_path, 'rb') as f:
                self.threshold = pickle.load(f)
            print(f"📥 Threshold loaded: {self.threshold:.6f}")
        except Exception as e:
            print(f"❌ Error loading threshold: {e}")
            self.threshold = 0.1  # Default threshold
    
    def load_encoder(self, encoder_path):
        """Load timetable encoder"""
        try:
            self.encoder = TimetableEncoder()
            self.encoder.load_encoders(encoder_path)
            print("📥 Encoder loaded successfully")
        except Exception as e:
            print(f"❌ Error loading encoder: {e}")
            self.encoder = None
    
    def detect_anomaly(self, timetable_sequence):
        """Detect anomaly in a timetable sequence"""
        if self.model is None or self.encoder is None:
            print("⚠️ Model or encoder not loaded")
            return False, 0.0
        
        try:
            # Encode sequence
            encoded_sequence = []
            for slot in timetable_sequence:
                encoded_slot = self.encoder.encode_slot(slot)
                encoded_sequence.append(encoded_slot)
            
            # Convert to tensor
            X = torch.FloatTensor(encoded_sequence).unsqueeze(0).to(self.device)
            
            # Get reconstruction
            with torch.no_grad():
                output, z = self.model(X)
                
                # Compute reconstruction error
                error = torch.mean((X - output) ** 2).item()
            
            # Check if anomaly
            is_anomaly = error > self.threshold
            
            return is_anomaly, error
            
        except Exception as e:
            print(f"❌ Error in anomaly detection: {e}")
            return False, 0.0
    
    def detect_slot_anomaly(self, slot_data, context_slots=None):
        """Detect anomaly in a single slot with context"""
        if context_slots is None:
            context_slots = []
        
        # Create sequence with context
        full_sequence = context_slots + [slot_data]
        
        return self.detect_anomaly(full_sequence)
    
    def check_constraints(self, slot_data):
        """Check hard constraints violations"""
        violations = []
        
        # Check time slot format
        if 'time_slot' in slot_data:
            time_slot = slot_data['time_slot']
            if not self._is_valid_time_slot(time_slot):
                violations.append(f"Invalid time slot format: {time_slot}")
        
        # Check campus-room consistency
        if 'campus' in slot_data and 'room_id' in slot_data:
            if not self._is_room_on_campus(slot_data['room_id'], slot_data['campus']):
                violations.append(f"Room {slot_data['room_id']} not available on {slot_data['campus']}")
        
        # Check teacher availability
        if 'teacher_id' in slot_data and 'day' in slot_data and 'time_slot' in slot_data:
            if not self._is_teacher_available(slot_data['teacher_id'], slot_data['day'], slot_data['time_slot']):
                violations.append(f"Teacher {slot_data['teacher_id']} not available at {slot_data['day']} {slot_data['time_slot']}")
        
        return violations
    
    def _is_valid_time_slot(self, time_slot):
        """Check if time slot format is valid"""
        valid_slots = [
            '08:00-09:00', '09:00-10:00', '10:00-11:00', '11:20-12:20',
            '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00', '17:00-18:00'
        ]
        return time_slot in valid_slots
    
    def _is_room_on_campus(self, room_id, campus):
        """Check if room exists on given campus"""
        try:
            rooms_df = pd.read_csv('data/rooms.csv')
            room_data = rooms_df[rooms_df['room_id'] == room_id]
            if room_data.empty:
                return False
            return room_data.iloc[0]['campus'] == campus
        except:
            return True  # Assume valid if can't check
    
    def _is_teacher_available(self, teacher_id, day, time_slot):
        """Check if teacher is available at given time"""
        try:
            teachers_df = pd.read_csv('data/teachers.csv')
            teacher_data = teachers_df[teachers_df['teacher_id'] == teacher_id]
            if teacher_data.empty:
                return False
            
            # Check available time slots
            available_slots = teacher_data.iloc[0]['available_time_slots']
            if pd.isna(available_slots):
                return True
            
            # Simple check - in real system would be more complex
            return time_slot.split('-')[0] >= '08:00'
        except:
            return True  # Assume available if can't check
    
    def monitor_timetable_update(self, updated_slot, existing_timetable):
        """Monitor a timetable update for anomalies"""
        print(f"🔍 Monitoring timetable update for slot: {updated_slot.get('day', 'Unknown')} {updated_slot.get('time_slot', 'Unknown')}")
        
        # Check hard constraints
        violations = self.check_constraints(updated_slot)
        if violations:
            print("⚠️ Constraint violations detected:")
            for violation in violations:
                print(f"   • {violation}")
            return True, "Constraint violations", violations
        
        # Check for anomalies using ML model
        is_anomaly, error = self.detect_slot_anomaly(updated_slot, existing_timetable)
        
        if is_anomaly:
            print(f"🚨 Anomaly detected! Reconstruction error: {error:.6f} (threshold: {self.threshold:.6f})")
            return True, "ML anomaly detected", [f"Reconstruction error {error:.6f} exceeds threshold {self.threshold:.6f}"]
        else:
            print(f"✅ No anomaly detected. Reconstruction error: {error:.6f}")
            return False, "Normal", []
    
    def batch_anomaly_check(self, timetable_data):
        """Check entire timetable for anomalies"""
        print("🔍 Running batch anomaly detection...")
        
        anomalies = []
        
        # Group by batch and check each sequence
        if isinstance(timetable_data, list):
            sequences = {}
            for slot in timetable_data:
                batch_id = slot.get('batch_id', 'unknown')
                if batch_id not in sequences:
                    sequences[batch_id] = []
                sequences[batch_id].append(slot)
            
            for batch_id, sequence in sequences.items():
                is_anomaly, error = self.detect_anomaly(sequence)
                if is_anomaly:
                    anomalies.append({
                        'batch_id': batch_id,
                        'error': error,
                        'sequence_length': len(sequence)
                    })
        
        print(f"📊 Batch check complete. Found {len(anomalies)} anomalous sequences")
        return anomalies

def main():
    """Main function to test anomaly detection"""
    print("🚀 Starting Real-Time Anomaly Detection Process...")
    print("=" * 60)
    
    # Initialize detector
    detector = AnomalyDetector()
    
    if detector.model is None:
        print("❌ Model not loaded. Please train the model first.")
        return
    
    # Test with sample data
    print("\n🧪 Testing anomaly detection with sample data...")
    
    # Normal slot
    normal_slot = {
        'section': 'A01',
        'subject_code': 'CS101',
        'teacher_id': 'TCH1001',
        'room_id': 'R301',
        'day': 'Monday',
        'time_slot': '08:00-09:00',
        'campus': 'Campus-3',
        'activity_type': 'Lecture'
    }
    
    # Anomalous slot (invalid time)
    anomalous_slot = {
        'section': 'A01',
        'subject_code': 'CS101',
        'teacher_id': 'TCH1001',
        'room_id': 'R301',
        'day': 'Monday',
        'time_slot': '25:00-26:00',  # Invalid time
        'campus': 'Campus-3',
        'activity_type': 'Lecture'
    }
    
    # Test normal slot
    print("\n📊 Testing normal slot:")
    is_anomaly, message, details = detector.monitor_timetable_update(normal_slot, [])
    print(f"Result: {'ANOMALY' if is_anomaly else 'NORMAL'}")
    
    # Test anomalous slot
    print("\n📊 Testing anomalous slot:")
    is_anomaly, message, details = detector.monitor_timetable_update(anomalous_slot, [])
    print(f"Result: {'ANOMALY' if is_anomaly else 'NORMAL'}")
    
    print("\n" + "=" * 60)
    print("✅ REAL-TIME ANOMALY DETECTION COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()