"""
Automated Reconstruction (Self-Healing) Module
Fixes anomalous timetable slots using autoencoder reconstruction and constraint solving
"""

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import pickle
import os
from datetime import datetime
from encoding import TimetableEncoder
from anomaly_detection import AnomalyDetector

class TimetableHealer:
    def __init__(self, model_path='pipeline/models/autoencoder.pth',
                 encoder_path='pipeline/models/encoders.pkl'):
        self.detector = AnomalyDetector(model_path, 'pipeline/models/threshold.pkl', encoder_path)
        self.encoder = self.detector.encoder
        self.model = self.detector.model
        self.healing_log = []
        
    def reconstruct_sequence(self, corrupted_sequence):
        """Reconstruct corrupted timetable sequence using autoencoder"""
        if self.model is None or self.encoder is None:
            print("Model या encoder load नहीं हुआ है")
            return corrupted_sequence
        
        try:
            print("🔧 Starting sequence reconstruction...")
            
            # Encode corrupted sequence
            encoded_sequence = []
            for slot in corrupted_sequence:
                encoded_slot = self.encoder.encode_slot(slot)
                encoded_sequence.append(encoded_slot)
            
            # Convert to tensor
            X = torch.FloatTensor(encoded_sequence).unsqueeze(0).to(self.detector.device)
            
            # Get latent representation and reconstruct
            with torch.no_grad():
                output, z = self.model(X)
                reconstructed = output.squeeze(0).cpu().numpy()
            
            # Decode back to slot data
            reconstructed_sequence = []
            for i, encoded_slot in enumerate(reconstructed):
                decoded_slot = self.encoder.decode_slot(encoded_slot)
                
                # Keep original structure if decoding fails
                if not decoded_slot:
                    decoded_slot = corrupted_sequence[i] if i < len(corrupted_sequence) else {}
                
                reconstructed_sequence.append(decoded_slot)
            
            print(f"✅ Sequence reconstructed: {len(reconstructed_sequence)} slots")
            return reconstructed_sequence
            
        except Exception as e:
            print(f"❌ Reconstruction error: {e}")
            return corrupted_sequence
    
    def heal_single_slot(self, corrupted_slot, context_slots=None):
        """Heal a single corrupted slot"""
        print(f"🩹 Healing slot: {corrupted_slot.get('day', 'Unknown')} {corrupted_slot.get('time_slot', 'Unknown')}")
        
        if context_slots is None:
            context_slots = []
        
        # Create sequence with corrupted slot
        full_sequence = context_slots + [corrupted_slot]
        
        # Reconstruct sequence
        reconstructed_sequence = self.reconstruct_sequence(full_sequence)
        
        # Get the healed slot (last one in sequence)
        if reconstructed_sequence:
            healed_slot = reconstructed_sequence[-1]
            
            # Post-process to ensure validity
            healed_slot = self.post_process_slot(healed_slot, corrupted_slot)
            
            # Log healing action
            self.log_healing(corrupted_slot, healed_slot, "Single slot reconstruction")
            
            return healed_slot
        
        return corrupted_slot
    
    def post_process_slot(self, reconstructed_slot, original_slot):
        """Post-process reconstructed slot to ensure validity"""
        print("🔧 Post-processing reconstructed slot...")
        
        # Ensure required fields exist
        required_fields = ['section', 'subject_code', 'teacher_id', 'room_id', 
                          'day', 'time_slot', 'campus', 'activity_type']
        
        processed_slot = {}
        
        for field in required_fields:
            if field in reconstructed_slot and reconstructed_slot[field]:
                processed_slot[field] = reconstructed_slot[field]
            elif field in original_slot:
                processed_slot[field] = original_slot[field]
            else:
                # Use fallback values
                processed_slot[field] = self.get_fallback_value(field)
        
        # Validate time slot
        if not self.is_valid_time_slot(processed_slot['time_slot']):
            processed_slot['time_slot'] = '08:00-09:00'
        
        # Ensure campus-room consistency
        processed_slot = self.ensure_campus_room_consistency(processed_slot)
        
        return processed_slot
    
    def get_fallback_value(self, field):
        """Get fallback value for missing field"""
        fallbacks = {
            'section': 'A01',
            'subject_code': 'GEN101',
            'teacher_id': 'TCH1001',
            'room_id': 'R301',
            'day': 'Monday',
            'time_slot': '08:00-09:00',
            'campus': 'Campus-3',
            'activity_type': 'Lecture'
        }
        return fallbacks.get(field, 'Unknown')
    
    def is_valid_time_slot(self, time_slot):
        """Check if time slot is valid"""
        valid_slots = [
            '08:00-09:00', '09:00-10:00', '10:00-11:00', '11:20-12:20',
            '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00', '17:00-18:00'
        ]
        return time_slot in valid_slots
    
    def ensure_campus_room_consistency(self, slot):
        """Ensure room exists on specified campus"""
        try:
            rooms_df = pd.read_csv('data/rooms.csv')
            
            # Check if room exists on campus
            campus_rooms = rooms_df[rooms_df['campus'] == slot['campus']]
            
            if not campus_rooms.empty:
                # Check if specified room is on campus
                if slot['room_id'] not in campus_rooms['room_id'].values:
                    # Assign a valid room from the campus
                    valid_room = campus_rooms.sample(1).iloc[0]
                    slot['room_id'] = valid_room['room_id']
                    print(f"🔄 Room reassigned to {slot['room_id']} for campus consistency")
            
        except Exception as e:
            print(f"⚠️ Campus-room consistency check failed: {e}")
        
        return slot
    
    def heal_batch_timetable(self, timetable_data, batch_id):
        """Heal entire batch timetable"""
        print(f"🏥 Healing batch timetable for {batch_id}...")
        
        # Filter slots for this batch
        batch_slots = [slot for slot in timetable_data if slot.get('batch_id') == batch_id]
        
        if not batch_slots:
            print(f"No slots found for batch {batch_id}")
            return timetable_data
        
        # Check for anomalies
        is_anomaly, error = self.detector.detect_anomaly(batch_slots)
        
        if not is_anomaly:
            print(f"✅ Batch {batch_id} timetable is normal, no healing needed")
            return timetable_data
        
        print(f"🚨 Anomaly detected in batch {batch_id}, starting healing process...")
        
        # Reconstruct the entire batch sequence
        healed_sequence = self.reconstruct_sequence(batch_slots)
        
        # Post-process each slot
        final_sequence = []
        for i, slot in enumerate(healed_sequence):
            original_slot = batch_slots[i] if i < len(batch_slots) else {}
            processed_slot = self.post_process_slot(slot, original_slot)
            final_sequence.append(processed_slot)
        
        # Replace slots in original timetable
        healed_timetable = []
        batch_slot_indices = []
        
        for i, slot in enumerate(timetable_data):
            if slot.get('batch_id') == batch_id:
                batch_slot_indices.append(len(healed_timetable))
                if batch_slot_indices[-1] - len(batch_slot_indices) + 1 < len(final_sequence):
                    healed_timetable.append(final_sequence[len(batch_slot_indices) - 1])
                else:
                    healed_timetable.append(slot)
            else:
                healed_timetable.append(slot)
        
        # Log batch healing
        self.log_healing(
            {'batch_id': batch_id, 'slots_count': len(batch_slots)},
            {'batch_id': batch_id, 'healed_slots_count': len(final_sequence)},
            "Batch timetable reconstruction"
        )
        
        print(f"✅ Batch {batch_id} healing completed")
        return healed_timetable
    
    def smart_conflict_resolution(self, conflicting_slots):
        """Resolve conflicts between multiple slots"""
        print(f"⚔️ Resolving conflicts between {len(conflicting_slots)} slots...")
        
        resolved_slots = []
        
        for i, slot in enumerate(conflicting_slots):
            # Check for time conflicts
            time_conflicts = [
                other for j, other in enumerate(conflicting_slots) 
                if i != j and other['day'] == slot['day'] and other['time_slot'] == slot['time_slot']
            ]
            
            if time_conflicts:
                # Resolve by shifting time or changing room
                resolved_slot = self.resolve_time_conflict(slot, time_conflicts)
                resolved_slots.append(resolved_slot)
            else:
                resolved_slots.append(slot)
        
        return resolved_slots
    
    def resolve_time_conflict(self, slot, conflicting_slots):
        """Resolve time conflict for a specific slot"""
        print(f"⏰ Resolving time conflict for {slot['day']} {slot['time_slot']}")
        
        # Try to find alternative time slot
        alternative_times = [
            '08:00-09:00', '09:00-10:00', '10:00-11:00', '11:20-12:20',
            '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00'
        ]
        
        current_time = slot['time_slot']
        occupied_times = [s['time_slot'] for s in conflicting_slots]
        
        # Find first available time
        for alt_time in alternative_times:
            if alt_time != current_time and alt_time not in occupied_times:
                slot['time_slot'] = alt_time
                print(f"🔄 Time slot changed to {alt_time}")
                break
        
        return slot
    
    def log_healing(self, original, healed, action):
        """Log healing action for audit trail"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'original': original,
            'healed': healed
        }
        self.healing_log.append(log_entry)
    
    def save_healing_log(self, filepath='pipeline/logs/healing_log.json'):
        """Save healing log to file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        import json
        with open(filepath, 'w') as f:
            json.dump(self.healing_log, f, indent=2)
        
        print(f"📝 Healing log saved: {len(self.healing_log)} entries")
    
    def emergency_rebuild(self, batch_id, base_data_path='data/'):
        """Emergency rebuild of batch timetable from scratch"""
        print(f"🚨 Emergency rebuild for batch {batch_id}...")
        
        try:
            # Load base data
            students_df = pd.read_csv(os.path.join(base_data_path, 'students.csv'))
            teachers_df = pd.read_csv(os.path.join(base_data_path, 'teachers.csv'))
            subjects_df = pd.read_csv(os.path.join(base_data_path, 'subjects.csv'))
            rooms_df = pd.read_csv(os.path.join(base_data_path, 'rooms.csv'))
            
            # Get batch info
            batch_students = students_df[students_df['batch_id'] == batch_id]
            if batch_students.empty:
                print(f"❌ Batch {batch_id} not found")
                return []
            
            batch_info = batch_students.iloc[0]
            
            # Generate new timetable
            new_timetable = []
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            time_slots = [
                '08:00-09:00', '09:00-10:00', '10:00-11:00', '11:20-12:20',
                '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00'
            ]
            
            # Get relevant subjects and teachers
            dept_subjects = subjects_df[
                (subjects_df['department'] == batch_info['department']) & 
                (subjects_df['scheme'] == batch_info['scheme'])
            ]
            
            if dept_subjects.empty:
                dept_subjects = subjects_df.sample(min(5, len(subjects_df)))
            
            dept_teachers = teachers_df[teachers_df['department'] == batch_info['department']]
            if dept_teachers.empty:
                dept_teachers = teachers_df.sample(min(3, len(teachers_df)))
            
            campus_rooms = rooms_df[rooms_df['campus'] == batch_info['primary_campus']]
            if campus_rooms.empty:
                campus_rooms = rooms_df.sample(min(10, len(rooms_df)))
            
            # Generate slots
            for day in days:
                for time_slot in time_slots:
                    if not dept_subjects.empty and not dept_teachers.empty and not campus_rooms.empty:
                        subject = dept_subjects.sample(1).iloc[0]
                        teacher = dept_teachers.sample(1).iloc[0]
                        room = campus_rooms.sample(1).iloc[0]
                        
                        slot = {
                            'batch_id': batch_id,
                            'section': batch_info['section'],
                            'day': day,
                            'time_slot': time_slot,
                            'subject_code': subject['subject_code'],
                            'teacher_id': teacher['teacher_id'],
                            'room_id': room['room_id'],
                            'campus': batch_info['primary_campus'],
                            'activity_type': 'Lab' if subject['has_lab'] else 'Lecture'
                        }
                        
                        new_timetable.append(slot)
            
            # Log emergency rebuild
            self.log_healing(
                {'batch_id': batch_id, 'action': 'corrupted'},
                {'batch_id': batch_id, 'rebuilt_slots': len(new_timetable)},
                "Emergency rebuild from base data"
            )
            
            print(f"🔧 Emergency rebuild completed: {len(new_timetable)} slots generated")
            return new_timetable
            
        except Exception as e:
            print(f"❌ Emergency rebuild failed: {e}")
            return []

def main():
    """Main function to test healing module"""
    print("🚀 Starting Automated Reconstruction (Self-Healing) Process...")
    print("=" * 70)
    
    # Initialize healer
    healer = TimetableHealer()
    
    if healer.model is None:
        print("❌ Model not loaded. Please train the model first.")
        return
    
    # Test healing with sample corrupted slot
    print("\n🧪 Testing healing with corrupted slot...")
    
    corrupted_slot = {
        'section': 'A01',
        'subject_code': '',  # Missing subject
        'teacher_id': 'INVALID_TEACHER',  # Invalid teacher
        'room_id': 'R999',  # Non-existent room
        'day': 'Monday',
        'time_slot': '25:00-26:00',  # Invalid time
        'campus': 'Campus-3',
        'activity_type': 'Lecture'
    }
    
    # Heal the slot
    healed_slot = healer.heal_single_slot(corrupted_slot)
    
    print("\n📊 Healing Results:")
    print("Original slot:")
    for key, value in corrupted_slot.items():
        print(f"  {key}: {value}")
    
    print("\nHealed slot:")
    for key, value in healed_slot.items():
        print(f"  {key}: {value}")
    
    # Save healing log
    healer.save_healing_log()
    
    print("\n" + "=" * 70)
    print("✅ AUTOMATED RECONSTRUCTION (SELF-HEALING) COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    main()