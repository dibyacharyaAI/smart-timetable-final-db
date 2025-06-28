"""
RNN Autoencoder Training Module
Trains sequence-to-sequence autoencoder for timetable anomaly detection
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
from encoding import TimetableEncoder

class TimetableAutoencoder(nn.Module):
    def __init__(self, input_dim, embed_dim=64, hidden_dim=128):
        super(TimetableAutoencoder, self).__init__()
        self.input_dim = input_dim
        self.embed_dim = embed_dim
        self.hidden_dim = hidden_dim
        
        # Encoder: Bi-LSTM
        self.encoder = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            batch_first=True,
            bidirectional=True
        )
        
        # Latent representation
        self.fc_z = nn.Linear(2 * hidden_dim, embed_dim)
        
        # Decoder: LSTM
        self.decoder = nn.LSTM(
            input_size=embed_dim + input_dim,
            hidden_size=hidden_dim,
            batch_first=True
        )
        
        # Output layer
        self.output = nn.Linear(hidden_dim, input_dim)
        
    def forward(self, x, p=None):
        batch_size, seq_len, _ = x.shape
        
        # Encoder
        enc_out, (h_n, c_n) = self.encoder(x)
        
        # Take final hidden state from bidirectional LSTM
        z = torch.tanh(self.fc_z(enc_out[:, -1, :]))
        
        # Prepare decoder input: repeat z and concatenate with x
        z_repeated = z.unsqueeze(1).repeat(1, seq_len, 1)
        
        # Add parameter conditioning if provided
        if p is not None:
            p_repeated = p.unsqueeze(1).repeat(1, seq_len, 1)
            decoder_input = torch.cat([z_repeated, x, p_repeated], dim=-1)
        else:
            decoder_input = torch.cat([z_repeated, x], dim=-1)
        
        # Decoder
        dec_out, _ = self.decoder(decoder_input)
        
        # Output
        output = self.output(dec_out)
        
        return output, z

class TimetableTrainer:
    def __init__(self, model, device='cpu'):
        self.model = model
        self.device = device
        self.model.to(device)
        self.encoder = None
        self.train_losses = []
        self.val_losses = []
        
    def load_training_data(self, data_path='data/'):
        """Load and prepare training data from CSV files"""
        print("📊 Loading training data from CSV files...")
        
        # Load encoder
        self.encoder = TimetableEncoder()
        if os.path.exists('pipeline/models/encoders.pkl'):
            self.encoder.load_encoders('pipeline/models/encoders.pkl')
        else:
            self.encoder.fit_encoders(data_path)
            self.encoder.save_encoders('pipeline/models/encoders.pkl')
        
        # Load CSV data
        students_df = pd.read_csv(os.path.join(data_path, 'students.csv'))
        teachers_df = pd.read_csv(os.path.join(data_path, 'teachers.csv'))
        subjects_df = pd.read_csv(os.path.join(data_path, 'subjects.csv'))
        rooms_df = pd.read_csv(os.path.join(data_path, 'rooms.csv'))
        
        # Generate training sequences
        sequences = []
        batches = students_df['batch_id'].unique()
        
        print(f"🔄 Generating sequences for {len(batches)} batches...")
        
        for batch_id in batches:
            batch_students = students_df[students_df['batch_id'] == batch_id]
            if batch_students.empty:
                continue
                
            department = batch_students.iloc[0]['department']
            scheme = batch_students.iloc[0]['scheme']
            campus = batch_students.iloc[0]['primary_campus']
            section = batch_students.iloc[0]['section']
            
            # Get subjects for this department
            dept_subjects = subjects_df[
                (subjects_df['department'] == department) & 
                (subjects_df['scheme'] == scheme)
            ]
            
            if dept_subjects.empty:
                dept_subjects = subjects_df.sample(5)
            
            # Generate weekly schedule
            weekly_sequence = []
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            time_slots = [
                '08:00-09:00', '09:00-10:00', '10:00-11:00', '11:20-12:20',
                '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00'
            ]
            
            for day in days:
                for time_slot in time_slots:
                    # Create slot data
                    if not dept_subjects.empty:
                        subject = dept_subjects.sample(1).iloc[0]
                        
                        # Find teacher for subject
                        subject_teachers = teachers_df[
                            teachers_df['subject_expertise'].str.contains(
                                subject['subject_name'], na=False, case=False
                            )
                        ]
                        
                        if not subject_teachers.empty:
                            teacher = subject_teachers.sample(1).iloc[0]
                        else:
                            teacher = teachers_df.sample(1).iloc[0]
                        
                        slot_data = {
                            'section': section,
                            'subject_code': subject['subject_code'],
                            'teacher_id': teacher['teacher_id'],
                            'room_id': f"R{np.random.randint(101, 399)}",
                            'day': day,
                            'time_slot': time_slot,
                            'campus': campus,
                            'activity_type': 'Lab' if subject['has_lab'] else 'Lecture'
                        }
                        
                        # Encode slot
                        encoded_slot = self.encoder.encode_slot(slot_data)
                        weekly_sequence.append(encoded_slot)
            
            if len(weekly_sequence) > 0:
                sequences.append(np.array(weekly_sequence))
        
        print(f"✅ Generated {len(sequences)} training sequences")
        return sequences
    
    def prepare_datasets(self, sequences, test_size=0.2, val_size=0.1):
        """Prepare train/validation/test datasets"""
        print("🔄 Preparing train/validation/test datasets...")
        
        # Convert to tensors
        max_len = max(len(seq) for seq in sequences)
        
        # Pad sequences to same length
        padded_sequences = []
        for seq in sequences:
            if len(seq) < max_len:
                padding = np.zeros((max_len - len(seq), seq.shape[1]))
                padded_seq = np.vstack([seq, padding])
            else:
                padded_seq = seq
            padded_sequences.append(padded_seq)
        
        X = np.array(padded_sequences)
        
        # Split data
        X_temp, X_test = train_test_split(X, test_size=test_size, random_state=42)
        X_train, X_val = train_test_split(X_temp, test_size=val_size/(1-test_size), random_state=42)
        
        # Convert to tensors
        X_train = torch.FloatTensor(X_train).to(self.device)
        X_val = torch.FloatTensor(X_val).to(self.device)
        X_test = torch.FloatTensor(X_test).to(self.device)
        
        print(f"📊 Dataset sizes:")
        print(f"   Train: {X_train.shape}")
        print(f"   Validation: {X_val.shape}")
        print(f"   Test: {X_test.shape}")
        
        return X_train, X_val, X_test
    
    def train_model(self, X_train, X_val, epochs=100, lr=1e-3, batch_size=32):
        """Train the autoencoder model"""
        print(f"🚀 Starting training for {epochs} epochs...")
        
        # Setup optimizer and loss
        optimizer = optim.Adam(self.model.parameters(), lr=lr)
        criterion = nn.MSELoss()
        
        # Create data loaders
        train_dataset = torch.utils.data.TensorDataset(X_train, X_train)
        val_dataset = torch.utils.data.TensorDataset(X_val, X_val)
        
        train_loader = torch.utils.data.DataLoader(
            train_dataset, batch_size=batch_size, shuffle=True
        )
        val_loader = torch.utils.data.DataLoader(
            val_dataset, batch_size=batch_size, shuffle=False
        )
        
        best_val_loss = float('inf')
        patience = 10
        patience_counter = 0
        
        for epoch in range(epochs):
            # Training phase
            self.model.train()
            train_loss = 0.0
            
            for batch_x, batch_y in train_loader:
                optimizer.zero_grad()
                
                # Forward pass
                output, z = self.model(batch_x)
                loss = criterion(output, batch_y)
                
                # Backward pass
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
            
            train_loss /= len(train_loader)
            self.train_losses.append(train_loss)
            
            # Validation phase
            self.model.eval()
            val_loss = 0.0
            
            with torch.no_grad():
                for batch_x, batch_y in val_loader:
                    output, z = self.model(batch_x)
                    loss = criterion(output, batch_y)
                    val_loss += loss.item()
            
            val_loss /= len(val_loader)
            self.val_losses.append(val_loss)
            
            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                # Save best model
                torch.save(self.model.state_dict(), 'pipeline/models/best_autoencoder.pth')
            else:
                patience_counter += 1
            
            if epoch % 10 == 0:
                print(f"Epoch {epoch:4d} | Train Loss: {train_loss:.6f} | Val Loss: {val_loss:.6f}")
            
            if patience_counter >= patience:
                print(f"Early stopping at epoch {epoch}")
                break
        
        print("✅ Training completed!")
        return best_val_loss
    
    def compute_threshold(self, X_val):
        """Compute anomaly detection threshold"""
        print("🔄 Computing anomaly detection threshold...")
        
        self.model.eval()
        reconstruction_errors = []
        
        with torch.no_grad():
            for i in range(X_val.shape[0]):
                x = X_val[i:i+1]
                output, z = self.model(x)
                
                # Compute reconstruction error
                error = torch.mean((x - output) ** 2).item()
                reconstruction_errors.append(error)
        
        errors = np.array(reconstruction_errors)
        
        # Set threshold as mean + 3*std
        threshold = np.mean(errors) + 3 * np.std(errors)
        
        print(f"📊 Reconstruction error statistics:")
        print(f"   Mean: {np.mean(errors):.6f}")
        print(f"   Std: {np.std(errors):.6f}")
        print(f"   Threshold (mean + 3σ): {threshold:.6f}")
        
        # Save threshold
        with open('pipeline/models/threshold.pkl', 'wb') as f:
            pickle.dump(threshold, f)
        
        return threshold
    
    def save_model(self, filepath='pipeline/models/autoencoder.pth'):
        """Save trained model"""
        torch.save(self.model.state_dict(), filepath)
        
        # Save training metadata
        metadata = {
            'input_dim': self.model.input_dim,
            'embed_dim': self.model.embed_dim,
            'hidden_dim': self.model.hidden_dim,
            'train_losses': self.train_losses,
            'val_losses': self.val_losses,
            'trained_at': datetime.now().isoformat()
        }
        
        with open('pipeline/models/training_metadata.pkl', 'wb') as f:
            pickle.dump(metadata, f)
        
        print(f"💾 Model saved to {filepath}")

def main():
    """Main training function"""
    print("🚀 Starting RNN Autoencoder Training Process...")
    print("=" * 60)
    
    # Check if CUDA is available
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"🖥️ Using device: {device}")
    
    # Initialize trainer
    trainer = TimetableTrainer(None, device)
    
    # Load training data
    sequences = trainer.load_training_data()
    
    if len(sequences) == 0:
        print("❌ No training sequences generated!")
        return
    
    # Get input dimension
    input_dim = sequences[0].shape[1]
    print(f"📊 Input dimension: {input_dim}")
    
    # Initialize model
    model = TimetableAutoencoder(
        input_dim=input_dim,
        embed_dim=64,
        hidden_dim=128
    )
    
    trainer.model = model
    trainer.model.to(device)
    
    # Prepare datasets
    X_train, X_val, X_test = trainer.prepare_datasets(sequences)
    
    # Train model
    best_val_loss = trainer.train_model(
        X_train, X_val,
        epochs=50,
        lr=1e-3,
        batch_size=16
    )
    
    # Compute threshold
    threshold = trainer.compute_threshold(X_val)
    
    # Save model
    trainer.save_model()
    
    print("\n" + "=" * 60)
    print("✅ RNN AUTOENCODER TRAINING COMPLETED SUCCESSFULLY!")
    print(f"📊 Best validation loss: {best_val_loss:.6f}")
    print(f"📊 Anomaly threshold: {threshold:.6f}")
    print("=" * 60)

if __name__ == "__main__":
    main()