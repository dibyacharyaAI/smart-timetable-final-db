"""
Quick ML Training with Optimized Data
Fast training using only essential 10 columns
"""

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import pickle
import os

class QuickAutoencoder(nn.Module):
    def __init__(self, input_dim=10):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 8)
        )
        self.decoder = nn.Sequential(
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, input_dim)
        )
    
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded

def quick_train():
    """Quick training with optimized data"""
    print("Quick training with optimized data...")
    
    # Load optimized data
    data_path = 'data/optimized_timetable_data.csv'
    if not os.path.exists(data_path):
        print("Creating optimized data first...")
        from pipeline.data_optimizer import TimetableDataOptimizer
        optimizer = TimetableDataOptimizer()
        optimizer.load_and_combine_data()
        optimizer.save_optimized_dataset()
    
    # Load and encode data
    df = pd.read_csv(data_path)
    print(f"Training data: {df.shape} - using only essential columns")
    
    # Simple encoding for quick training
    from sklearn.preprocessing import LabelEncoder
    encoded_data = df.copy()
    
    encoders = {}
    for col in ['day', 'time_slot', 'department', 'batch_type', 'subject_type', 
               'campus', 'room_type', 'teacher_dept']:
        if col in encoded_data.columns:
            le = LabelEncoder()
            encoded_data[col] = le.fit_transform(encoded_data[col].astype(str))
            encoders[col] = le
    
    # Normalize batch_size
    if 'batch_size' in encoded_data.columns:
        encoded_data['batch_size'] = encoded_data['batch_size'] / 100.0
    
    # Convert to tensor
    data_tensor = torch.FloatTensor(encoded_data.values)
    
    # Quick model
    model = QuickAutoencoder(input_dim=data_tensor.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.MSELoss()
    
    # Quick training - just 10 epochs
    print("Training for 10 epochs...")
    for epoch in range(10):
        model.train()
        optimizer.zero_grad()
        
        reconstructed = model(data_tensor)
        loss = criterion(reconstructed, data_tensor)
        
        if hasattr(loss, 'backward'):
                if hasattr(loss, 'backward'):
                loss.backward()
        optimizer.step()
        
        if epoch % 2 == 0:
            print(f"Epoch {epoch}: Loss = {loss.item() if hasattr(loss, 'item') else float(loss) if hasattr(loss, 'item') else float(loss):.4f}")
    
    # Calculate threshold
    model.eval()
    with torch.no_grad():
        reconstructed = model(data_tensor)
        errors = torch.mean((data_tensor - reconstructed) ** 2, dim=1)
        threshold = torch.quantile(errors, 0.95).item()
    
    # Save model
    os.makedirs('pipeline/models', exist_ok=True)
    torch.save(model.state_dict(), 'pipeline/models/quick_autoencoder.pth')
    
    with open('pipeline/models/quick_encoders.pkl', 'wb') as f:
        pickle.dump(encoders, f)
    
    with open('pipeline/models/quick_threshold.pkl', 'wb') as f:
        pickle.dump(threshold, f)
    
    print(f"Quick training completed!")
    print(f"Final loss: {loss.item() if hasattr(loss, 'item') else float(loss) if hasattr(loss, 'item') else float(loss):.4f}")
    print(f"Threshold: {threshold:.4f}")
    print(f"Model saved with {data_tensor.shape[1]} features (vs 20+ in old system)")
    
    return True

if __name__ == "__main__":
    quick_train()