"""
Fixed Anomaly Detection Module
Simplified and robust anomaly detection for timetable monitoring
"""

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import pickle
import os
from datetime import datetime
from sklearn.preprocessing import StandardScaler

class SimpleAutoencoder(nn.Module):
    def __init__(self, input_dim=10):
        super(SimpleAutoencoder, self).__init__()
        self.input_dim = input_dim
        
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 8)
        )
        
        self.decoder = nn.Sequential(
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, 32),
            nn.ReLU(),
            nn.Linear(32, input_dim)
        )
        
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

class FixedAnomalyDetector:
    def __init__(self, model_path='pipeline/models/autoencoder.pth', 
                 threshold_path='pipeline/models/threshold.pkl',
                 scaler_path='pipeline/models/scaler.pkl'):
        self.device = torch.device('cpu')
        self.model = None
        self.threshold = 0.1  # Default threshold
        self.scaler = StandardScaler()
        
        self.load_model(model_path)
        self.load_threshold(threshold_path)
        self.load_scaler(scaler_path)
        
    def load_model(self, model_path):
        """Load trained autoencoder model"""
        try:
            if os.path.exists(model_path):
                # Load metadata first to get input dimension
                metadata_path = 'pipeline/models/training_metadata.pkl'
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'rb') as f:
                        metadata = pickle.load(f)
                    input_dim = metadata.get('input_dim', 10)
                else:
                    input_dim = 10
                
                self.model = SimpleAutoencoder(input_dim=input_dim)
                self.model.load_state_dict(torch.load(model_path, map_location=self.device))
                self.model.eval()
                print("✅ Model loaded successfully")
            else:
                print("❌ Model file not found, will train first")
                self._train_if_needed()
                
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self._train_if_needed()
    
    def load_threshold(self, threshold_path):
        """Load anomaly detection threshold"""
        try:
            if os.path.exists(threshold_path):
                with open(threshold_path, 'rb') as f:
                    self.threshold = pickle.load(f)
                print(f"✅ Threshold loaded: {self.threshold}")
            else:
                print("❌ Threshold file not found, using default")
                
        except Exception as e:
            print(f"❌ Error loading threshold: {e}")
    
    def load_scaler(self, scaler_path):
        """Load feature scaler"""
        try:
            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                print("✅ Scaler loaded successfully")
            else:
                print("❌ Scaler file not found, using default")
                
        except Exception as e:
            print(f"❌ Error loading scaler: {e}")
    
    def _train_if_needed(self):
        """Train model if not available"""
        try:
            from fixed_training import SimpleTimetableTrainer
            print("🚀 Training model as it's not available...")
            
            trainer = SimpleTimetableTrainer()
            success = trainer.train_model(epochs=20)
            
            if success:
                trainer.save_model()
                # Reload the trained model
                self.load_model('pipeline/models/autoencoder.pth')
                self.load_threshold('pipeline/models/threshold.pkl')
                self.load_scaler('pipeline/models/scaler.pkl')
                print("✅ Model trained and loaded successfully")
            else:
                print("❌ Training failed")
                
        except Exception as e:
            print(f"❌ Training failed: {e}")
    
    def detect_anomaly(self, timetable_sequence):
        """Detect anomaly in a timetable sequence"""
        try:
            if self.model is None:
                print("❌ Model not available")
                return False, 0.0
            
            # Convert to numpy array
            if isinstance(timetable_sequence, list):
                X = np.array(timetable_sequence).reshape(1, -1)
            else:
                X = np.array(timetable_sequence).reshape(1, -1)
            
            # Ensure correct feature count
            if X.shape[1] != self.model.input_dim:
                # Pad or truncate to match model input
                if X.shape[1] < self.model.input_dim:
                    padding = np.zeros((1, self.model.input_dim - X.shape[1]))
                    X = np.concatenate([X, padding], axis=1)
                else:
                    X = X[:, :self.model.input_dim]
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Predict
            self.model.eval()
            with torch.no_grad():
                X_tensor = torch.FloatTensor(X_scaled)
                output = self.model(X_tensor)
                error = torch.mean((X_tensor - output) ** 2).item()
            
            is_anomaly = error > self.threshold
            return is_anomaly, error
            
        except Exception as e:
            print(f"❌ Anomaly detection failed: {e}")
            return False, 0.0
    
    def detect_slot_anomaly(self, slot_data, context_slots=None):
        """Detect anomaly in a single slot with context"""
        try:
            # Convert slot data to feature vector
            if isinstance(slot_data, dict):
                features = self._slot_to_features(slot_data)
            else:
                features = list(slot_data)
            
            # Basic constraint checks first
            constraint_violation = self.check_constraints(slot_data)
            if constraint_violation:
                return True, 1.0  # High anomaly score for constraint violations
            
            # ML-based anomaly detection
            return self.detect_anomaly(features)
            
        except Exception as e:
            print(f"❌ Slot anomaly detection failed: {e}")
            return False, 0.0
    
    def _slot_to_features(self, slot_data):
        """Convert slot data to feature vector"""
        # Simple encoding for demonstration
        features = [
            hash(str(slot_data.get('day', ''))) % 100,
            hash(str(slot_data.get('time_start', ''))) % 100,
            hash(str(slot_data.get('batch_id', ''))) % 100,
            hash(str(slot_data.get('subject_code', ''))) % 100,
            hash(str(slot_data.get('teacher_id', ''))) % 100,
            hash(str(slot_data.get('room_id', ''))) % 100,
            hash(str(slot_data.get('campus', ''))) % 100,
            hash(str(slot_data.get('activity_type', ''))) % 100,
            hash(str(slot_data.get('department', ''))) % 100,
            slot_data.get('slot_index', 0)
        ]
        return features[:10]  # Ensure exactly 10 features
    
    def check_constraints(self, slot_data):
        """Check hard constraints violations"""
        try:
            if isinstance(slot_data, dict):
                # Check basic constraints
                if not slot_data.get('subject_code'):
                    return True
                if not slot_data.get('teacher_id'):
                    return True
                if not slot_data.get('room_id'):
                    return True
                
                # Check time slot format
                time_start = slot_data.get('time_start', '')
                if not self._is_valid_time_slot(time_start):
                    return True
                
                # Check campus-room consistency
                campus = slot_data.get('campus', '')
                room_id = slot_data.get('room_id', '')
                if not self._is_room_on_campus(room_id, campus):
                    return True
            
            return False
            
        except Exception as e:
            print(f"❌ Constraint check failed: {e}")
            return False
    
    def _is_valid_time_slot(self, time_slot):
        """Check if time slot format is valid"""
        valid_slots = [
            '08:00-09:00', '09:00-10:00', '10:00-11:00', '11:20-12:20',
            '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00', '17:00-18:00'
        ]
        return time_slot in valid_slots
    
    def _is_room_on_campus(self, room_id, campus):
        """Check if room exists on given campus"""
        # Simple validation - rooms should start with campus identifier
        if not room_id or not campus:
            return False
        
        campus_prefixes = {
            'Campus-3': ['R3', 'C3', 'LAB3'],
            'Campus-15B': ['R15', 'C15', 'LAB15'],
            'Campus-8': ['R8', 'C8', 'LAB8'],
            'Campus-17': ['R17', 'C17', 'LAB17']
        }
        
        prefixes = campus_prefixes.get(campus, [])
        return any(room_id.startswith(prefix) for prefix in prefixes)
    
    def monitor_timetable_update(self, updated_slot, existing_timetable):
        """Monitor a timetable update for anomalies"""
        try:
            is_anomaly, score = self.detect_slot_anomaly(updated_slot)
            
            if is_anomaly:
                print(f"🚨 Anomaly detected in slot update: {score:.4f}")
                return {
                    'anomaly_detected': True,
                    'anomaly_score': score,
                    'slot_data': updated_slot,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                print(f"✅ Slot update normal: {score:.4f}")
                return {
                    'anomaly_detected': False,
                    'anomaly_score': score,
                    'slot_data': updated_slot,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"❌ Monitoring failed: {e}")
            return {
                'anomaly_detected': False,
                'anomaly_score': 0.0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def batch_anomaly_check(self, timetable_data):
        """Check entire timetable for anomalies"""
        anomalies = []
        
        try:
            for i, slot in enumerate(timetable_data):
                is_anomaly, score = self.detect_slot_anomaly(slot)
                
                if is_anomaly:
                    anomalies.append({
                        'slot_index': i,
                        'anomaly_score': score,
                        'slot_data': slot
                    })
            
            print(f"🔍 Batch check completed: {len(anomalies)} anomalies found")
            return anomalies
            
        except Exception as e:
            print(f"❌ Batch anomaly check failed: {e}")
            return []

def main():
    """Test the fixed anomaly detection"""
    detector = FixedAnomalyDetector()
    
    # Test with sample data
    test_slot = {
        'day': 'Monday',
        'time_start': '09:00-10:00',
        'batch_id': 'CSE-A-2024',
        'subject_code': 'CS101',
        'teacher_id': 'TCH001',
        'room_id': 'R3-101',
        'campus': 'Campus-3',
        'activity_type': 'Lecture',
        'department': 'CSE',
        'slot_index': 1
    }
    
    is_anomaly, score = detector.detect_slot_anomaly(test_slot)
    print(f"🧪 Test result: Anomaly={is_anomaly}, Score={score:.4f}")

if __name__ == "__main__":
    main()