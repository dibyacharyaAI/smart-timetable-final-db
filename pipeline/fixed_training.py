"""
Fixed RNN Autoencoder Training Module
Simplified and robust training for timetable anomaly detection
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import pandas as pd
import pickle
import os
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

class SimpleAutoencoder(nn.Module):
    def __init__(self, input_dim=10):
        super(SimpleAutoencoder, self).__init__()
        self.input_dim = input_dim
        
        # Simple encoder-decoder architecture
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

class SimpleTimetableTrainer:
    def __init__(self):
        self.device = torch.device('cpu')
        self.model = None
        self.scaler = StandardScaler()
        self.threshold = None
        
    def load_optimized_data(self):
        """Load optimized timetable data"""
        try:
            # Load optimized data
            if os.path.exists('data/optimized_timetable_data.csv'):
                data = pd.read_csv('data/optimized_timetable_data.csv')
                print(f"✅ Loaded optimized data: {data.shape}")
                return data
            else:
                print("❌ Optimized data not found, creating sample data...")
                return self.create_sample_data()
                
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return self.create_sample_data()
    
    def create_sample_data(self):
        """Create sample training data"""
        np.random.seed(42)
        n_samples = 1000
        
        # Create 10 features matching optimized data
        data = {
            'slot_index': np.random.randint(0, 48, n_samples),
            'day_encoded': np.random.randint(0, 6, n_samples),
            'time_encoded': np.random.randint(0, 9, n_samples),
            'batch_encoded': np.random.randint(0, 72, n_samples),
            'subject_encoded': np.random.randint(0, 73, n_samples),
            'teacher_encoded': np.random.randint(0, 94, n_samples),
            'room_encoded': np.random.randint(0, 66, n_samples),
            'campus_encoded': np.random.randint(0, 4, n_samples),
            'activity_encoded': np.random.randint(0, 3, n_samples),
            'department_encoded': np.random.randint(0, 8, n_samples)
        }
        
        df = pd.DataFrame(data)
        print(f"✅ Created sample data: {df.shape}")
        return df
    
    def train_model(self, epochs=50, lr=0.001, batch_size=32):
        """Train the autoencoder model"""
        try:
            print("🚀 Starting simplified training...")
            
            # Load data
            data = self.load_optimized_data()
            
            # Prepare features (use only numerical columns)
            feature_cols = [col for col in data.columns if data[col].dtype in ['int64', 'float64']]
            X = data[feature_cols].values
            
            print(f"📊 Training features: {len(feature_cols)} columns")
            print(f"📊 Training samples: {X.shape[0]} rows")
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Split data
            X_train, X_val = train_test_split(X_scaled, test_size=0.2, random_state=42)
            
            # Create model
            input_dim = X_scaled.shape[1]
            self.model = SimpleAutoencoder(input_dim=input_dim)
            self.model.to(self.device)
            
            # Training setup
            criterion = nn.MSELoss()
            optimizer = optim.Adam(self.model.parameters(), lr=lr)
            
            # Training loop
            self.model.train()
            for epoch in range(epochs):
                # Simple batch processing
                total_loss = 0
                n_batches = len(X_train) // batch_size
                
                for i in range(0, len(X_train), batch_size):
                    batch_X = torch.FloatTensor(X_train[i:i+batch_size])
                    
                    optimizer.zero_grad()
                    outputs = self.model(batch_X)
                    loss = criterion(outputs, batch_X)
                    loss.backward()
                    optimizer.step()
                    
                    total_loss += loss.item()
                
                if epoch % 10 == 0:
                    avg_loss = total_loss / max(n_batches, 1)
                    print(f"Epoch {epoch}/{epochs}, Loss: {avg_loss:.6f}")
            
            # Compute threshold on validation set
            self.model.eval()
            with torch.no_grad():
                val_tensor = torch.FloatTensor(X_val)
                val_outputs = self.model(val_tensor)
                val_errors = torch.mean((val_tensor - val_outputs) ** 2, dim=1)
                self.threshold = float(torch.quantile(val_errors, 0.95))
            
            print(f"✅ Training completed! Threshold: {self.threshold:.6f}")
            return True
            
        except Exception as e:
            print(f"❌ Training failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def save_model(self):
        """Save trained model and metadata"""
        try:
            os.makedirs('pipeline/models', exist_ok=True)
            
            # Save model
            if self.model is not None:
                torch.save(self.model.state_dict(), 'pipeline/models/autoencoder.pth')
                print("✅ Model saved")
            
            # Save threshold
            if self.threshold is not None:
                with open('pipeline/models/threshold.pkl', 'wb') as f:
                    pickle.dump(self.threshold, f)
                print("✅ Threshold saved")
            
            # Save scaler
            with open('pipeline/models/scaler.pkl', 'wb') as f:
                pickle.dump(self.scaler, f)
                print("✅ Scaler saved")
            
            # Save metadata
            metadata = {
                'input_dim': self.model.input_dim if self.model else 10,
                'threshold': self.threshold,
                'trained_at': datetime.now().isoformat(),
                'model_type': 'SimpleAutoencoder'
            }
            with open('pipeline/models/training_metadata.pkl', 'wb') as f:
                pickle.dump(metadata, f)
                print("✅ Metadata saved")
                
            return True
            
        except Exception as e:
            print(f"❌ Failed to save model: {e}")
            return False
    
    def detect_anomaly(self, slot_data):
        """Detect anomaly in slot data"""
        try:
            if self.model is None or self.threshold is None:
                return False, 0.0
            
            # Convert slot_data to feature vector
            if isinstance(slot_data, dict):
                # Extract numerical features
                features = []
                for key in ['slot_index', 'day_encoded', 'time_encoded', 'batch_encoded', 
                           'subject_encoded', 'teacher_encoded', 'room_encoded', 
                           'campus_encoded', 'activity_encoded', 'department_encoded']:
                    features.append(slot_data.get(key, 0))
                X = np.array(features).reshape(1, -1)
            else:
                X = np.array(slot_data).reshape(1, -1)
            
            # Scale and predict
            X_scaled = self.scaler.transform(X)
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

def main():
    """Train the simplified autoencoder"""
    trainer = SimpleTimetableTrainer()
    
    print("🚀 Starting simplified training process...")
    success = trainer.train_model(epochs=30)
    
    if success:
        trainer.save_model()
        print("✅ Training completed successfully!")
        
        # Test anomaly detection
        test_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        is_anomaly, error = trainer.detect_anomaly(test_data)
        print(f"🧪 Test anomaly detection: {is_anomaly}, error: {error:.6f}")
    else:
        print("❌ Training failed!")

if __name__ == "__main__":
    main()