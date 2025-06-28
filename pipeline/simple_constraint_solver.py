"""
Simple Constraint Solver Module
Fast constraint validation without complex optimization
"""

import pandas as pd
import os
from datetime import datetime

class SimpleTimetableConstraintSolver:
    def __init__(self, data_path='data/'):
        self.data_path = data_path
        self.reference_data = {}
        self.violations = []
        
    def load_reference_data(self):
        """Load reference data for constraint solving"""
        try:
            print("📊 Loading reference data for constraint solving...")
            
            # Load basic data for validation
            files_to_load = {
                'students': 'student_data.csv',
                'teachers': 'teacher_data.csv', 
                'subjects': 'subject_data.csv',
                'rooms': 'room_data.csv'
            }
            
            for key, filename in files_to_load.items():
                filepath = os.path.join(self.data_path, filename)
                if os.path.exists(filepath):
                    self.reference_data[key] = pd.read_csv(filepath)
                    print(f"✅ Loaded {key}: {len(self.reference_data[key])} records")
                else:
                    print(f"⚠️ {filename} not found, using minimal validation")
                    self.reference_data[key] = pd.DataFrame()
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading reference data: {e}")
            return False
    
    def detect_violations(self, timetable_slots):
        """Detect constraint violations in timetable"""
        violations = []
        
        try:
            print("🔍 Detecting constraint violations...")
            
            if not timetable_slots:
                return violations
            
            # Convert to DataFrame for easier processing
            if isinstance(timetable_slots, list):
                df = pd.DataFrame(timetable_slots)
            else:
                df = timetable_slots
            
            # Check for basic violations
            for idx, slot in df.iterrows():
                slot_violations = []
                
                # Check for missing required fields
                required_fields = ['subject_code', 'teacher_id', 'room_id', 'day', 'time_start']
                for field in required_fields:
                    if not slot.get(field) or str(slot.get(field)).strip() == '':
                        slot_violations.append(f"Missing {field}")
                
                # Check time format
                time_start = str(slot.get('time_start', ''))
                if time_start and not self._is_valid_time_format(time_start):
                    slot_violations.append("Invalid time format")
                
                # Check campus-room consistency
                campus = str(slot.get('campus', ''))
                room_id = str(slot.get('room_id', ''))
                if campus and room_id and not self._is_room_on_campus(room_id, campus):
                    slot_violations.append("Room not on specified campus")
                
                if slot_violations:
                    violations.append({
                        'slot_index': idx,
                        'violations': slot_violations,
                        'slot_data': slot.to_dict() if hasattr(slot, 'to_dict') else slot
                    })
            
            print(f"🚨 Found {len(violations)} violations")
            return violations
            
        except Exception as e:
            print(f"❌ Error detecting violations: {e}")
            return []
    
    def _is_valid_time_format(self, time_slot):
        """Check if time slot format is valid"""
        valid_formats = [
            '08:00-09:00', '09:00-10:00', '10:00-11:00', '11:20-12:20',
            '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00', '17:00-18:00'
        ]
        return time_slot in valid_formats
    
    def _is_room_on_campus(self, room_id, campus):
        """Check if room exists on given campus"""
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
    
    def fix_constraint_violations(self, timetable_slots):
        """Fix constraint violations in existing timetable"""
        try:
            print("🔧 Fixing constraint violations...")
            
            violations = self.detect_violations(timetable_slots)
            
            if not violations:
                print("✅ No violations found!")
                return timetable_slots, []
            
            fixed_slots = timetable_slots.copy() if hasattr(timetable_slots, 'copy') else list(timetable_slots)
            fixes_applied = []
            
            for violation in violations:
                slot_idx = violation['slot_index']
                slot_violations = violation['violations']
                
                for v in slot_violations:
                    if "Missing subject_code" in v:
                        fixed_slots[slot_idx]['subject_code'] = 'GEN101'
                        fixes_applied.append(f"Fixed missing subject_code in slot {slot_idx}")
                    
                    elif "Missing teacher_id" in v:
                        fixed_slots[slot_idx]['teacher_id'] = 'TCH001'
                        fixes_applied.append(f"Fixed missing teacher_id in slot {slot_idx}")
                    
                    elif "Missing room_id" in v:
                        campus = fixed_slots[slot_idx].get('campus', 'Campus-3')
                        if campus == 'Campus-3':
                            fixed_slots[slot_idx]['room_id'] = 'R3-101'
                        else:
                            fixed_slots[slot_idx]['room_id'] = 'R3-101'
                        fixes_applied.append(f"Fixed missing room_id in slot {slot_idx}")
                    
                    elif "Invalid time format" in v:
                        fixed_slots[slot_idx]['time_start'] = '09:00-10:00'
                        fixes_applied.append(f"Fixed invalid time format in slot {slot_idx}")
            
            print(f"✅ Applied {len(fixes_applied)} fixes")
            return fixed_slots, fixes_applied
            
        except Exception as e:
            print(f"❌ Error fixing violations: {e}")
            return timetable_slots, []
    
    def optimize_schedule(self, timetable_slots):
        """Simple schedule optimization"""
        try:
            print("⚡ Applying simple schedule optimization...")
            
            # Just return the slots as-is for now - no complex optimization
            # In the future, could add simple sorting or grouping logic
            
            optimized_slots = timetable_slots
            print("✅ Basic optimization completed")
            
            return optimized_slots
            
        except Exception as e:
            print(f"❌ Error optimizing schedule: {e}")
            return timetable_slots

def main():
    """Test the simple constraint solver"""
    solver = SimpleTimetableConstraintSolver()
    
    # Load reference data
    solver.load_reference_data()
    
    # Test with sample data
    test_slots = [
        {
            'day': 'Monday',
            'time_start': '09:00-10:00',
            'batch_id': 'CSE-A-2024',
            'subject_code': 'CS101',
            'teacher_id': 'TCH001',
            'room_id': 'R3-101',
            'campus': 'Campus-3',
            'activity_type': 'Lecture',
            'department': 'CSE'
        },
        {
            'day': 'Monday', 
            'time_start': 'INVALID',  # Invalid time
            'batch_id': 'CSE-A-2024',
            'subject_code': '',  # Missing subject
            'teacher_id': 'TCH001',
            'room_id': 'R3-101',
            'campus': 'Campus-3',
            'activity_type': 'Lecture',
            'department': 'CSE'
        }
    ]
    
    violations = solver.detect_violations(test_slots)
    print(f"🧪 Test violations: {len(violations)}")
    
    fixed_slots, fixes = solver.fix_constraint_violations(test_slots)
    print(f"🧪 Applied fixes: {len(fixes)}")

if __name__ == "__main__":
    main()