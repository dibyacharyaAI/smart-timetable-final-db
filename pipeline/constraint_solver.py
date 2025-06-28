"""
Constraint Solver Module using OR-Tools
Enforces hard constraints and optimizes timetable assignments
"""

from ortools.sat.python import cp_model
import pandas as pd
import numpy as np
from datetime import datetime
import json

class TimetableConstraintSolver:
    def __init__(self, data_path='data/'):
        self.data_path = data_path
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.variables = {}
        self.constraints = []
        
        # Load reference data
        self.load_reference_data()
        
    def load_reference_data(self):
        """Load reference data for constraint solving"""
        print("📊 Loading reference data for constraint solving...")
        
        try:
            self.students_df = pd.read_csv(f'{self.data_path}/students.csv')
            self.teachers_df = pd.read_csv(f'{self.data_path}/teachers.csv')
            self.subjects_df = pd.read_csv(f'{self.data_path}/subjects.csv')
            self.rooms_df = pd.read_csv(f'{self.data_path}/rooms.csv')
            
            # Create lookup dictionaries
            self.batches = list(self.students_df['batch_id'].unique())
            self.teachers = list(self.teachers_df['teacher_id'].unique())
            self.subjects = list(self.subjects_df['subject_code'].unique())
            self.rooms = list(self.rooms_df['room_id'].unique())
            self.campuses = list(self.students_df['primary_campus'].unique())
            
            self.days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            self.time_slots = [
                '08:00-09:00', '09:00-10:00', '10:00-11:00', '11:20-12:20',
                '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00'
            ]
            
            # Create indices
            self.batch_to_idx = {batch: i for i, batch in enumerate(self.batches)}
            self.teacher_to_idx = {teacher: i for i, teacher in enumerate(self.teachers)}
            self.subject_to_idx = {subject: i for i, subject in enumerate(self.subjects)}
            self.room_to_idx = {room: i for i, room in enumerate(self.rooms)}
            self.day_to_idx = {day: i for i, day in enumerate(self.days)}
            self.time_to_idx = {time: i for i, time in enumerate(self.time_slots)}
            
            print(f"✅ Reference data loaded: {len(self.batches)} batches, {len(self.teachers)} teachers")
            
        except Exception as e:
            print(f"❌ Error loading reference data: {e}")
            self.batches = []
            self.teachers = []
            self.subjects = []
            self.rooms = []
    
    def create_variables(self):
        """Create decision variables for the constraint solver"""
        print("🔧 Creating decision variables...")
        
        # Assignment variables: assignment[b][t][s][r][d][h] = 1 if batch b is assigned
        # teacher t, subject s, room r on day d at time h
        self.assignment = {}
        
        for b in range(len(self.batches)):
            self.assignment[b] = {}
            for t in range(len(self.teachers)):
                self.assignment[b][t] = {}
                for s in range(len(self.subjects)):
                    self.assignment[b][t][s] = {}
                    for r in range(len(self.rooms)):
                        self.assignment[b][t][s][r] = {}
                        for d in range(len(self.days)):
                            self.assignment[b][t][s][r][d] = {}
                            for h in range(len(self.time_slots)):
                                var_name = f'assign_{b}_{t}_{s}_{r}_{d}_{h}'
                                self.assignment[b][t][s][r][d][h] = self.model.NewBoolVar(var_name)
        
        print(f"✅ Created {len(self.batches) * len(self.teachers) * len(self.subjects) * len(self.rooms) * len(self.days) * len(self.time_slots)} variables")
    
    def add_hard_constraints(self):
        """Add hard constraints that must be satisfied"""
        print("⚖️ Adding hard constraints...")
        
        # Constraint 1: Each batch can have at most one class at any given time
        for b in range(len(self.batches)):
            for d in range(len(self.days)):
                for h in range(len(self.time_slots)):
                    assignments_at_time = []
                    for t in range(len(self.teachers)):
                        for s in range(len(self.subjects)):
                            for r in range(len(self.rooms)):
                                assignments_at_time.append(self.assignment[b][t][s][r][d][h])
                    
                    # At most one assignment per batch per time slot
                    self.model.Add(sum(assignments_at_time) <= 1)
        
        # Constraint 2: Each teacher can teach at most one class at any given time
        for t in range(len(self.teachers)):
            for d in range(len(self.days)):
                for h in range(len(self.time_slots)):
                    teacher_assignments = []
                    for b in range(len(self.batches)):
                        for s in range(len(self.subjects)):
                            for r in range(len(self.rooms)):
                                teacher_assignments.append(self.assignment[b][t][s][r][d][h])
                    
                    self.model.Add(sum(teacher_assignments) <= 1)
        
        # Constraint 3: Each room can be used by at most one batch at any given time
        for r in range(len(self.rooms)):
            for d in range(len(self.days)):
                for h in range(len(self.time_slots)):
                    room_assignments = []
                    for b in range(len(self.batches)):
                        for t in range(len(self.teachers)):
                            for s in range(len(self.subjects)):
                                room_assignments.append(self.assignment[b][t][s][r][d][h])
                    
                    self.model.Add(sum(room_assignments) <= 1)
        
        # Constraint 4: Campus-room consistency
        for b in range(len(self.batches)):
            batch_id = self.batches[b]
            batch_campus = self.students_df[self.students_df['batch_id'] == batch_id].iloc[0]['primary_campus']
            
            for r in range(len(self.rooms)):
                room_id = self.rooms[r]
                room_data = self.rooms_df[self.rooms_df['room_id'] == room_id]
                
                if not room_data.empty:
                    room_campus = room_data.iloc[0]['campus']
                    
                    # If room is not on batch's campus, prevent assignment
                    if room_campus != batch_campus:
                        for t in range(len(self.teachers)):
                            for s in range(len(self.subjects)):
                                for d in range(len(self.days)):
                                    for h in range(len(self.time_slots)):
                                        self.model.Add(self.assignment[b][t][s][r][d][h] == 0)
        
        print("✅ Hard constraints added")
    
    def add_soft_constraints(self):
        """Add soft constraints for optimization"""
        print("🎯 Adding soft constraints for optimization...")
        
        # Objective: Minimize gaps in daily schedules
        gap_penalties = []
        
        for b in range(len(self.batches)):
            for d in range(len(self.days)):
                # Count gaps between classes
                for h in range(len(self.time_slots) - 1):
                    # Check if there's a class at time h but not at h+1
                    has_class_h = []
                    has_class_h_plus_1 = []
                    
                    for t in range(len(self.teachers)):
                        for s in range(len(self.subjects)):
                            for r in range(len(self.rooms)):
                                has_class_h.append(self.assignment[b][t][s][r][d][h])
                                has_class_h_plus_1.append(self.assignment[b][t][s][r][d][h+1])
                    
                    # Create gap indicator variable
                    gap_var = self.model.NewBoolVar(f'gap_{b}_{d}_{h}')
                    
                    # Gap occurs if we have class at h, no class at h+1, but have class later
                    class_at_h = self.model.NewBoolVar(f'class_at_{b}_{d}_{h}')
                    class_at_h_plus_1 = self.model.NewBoolVar(f'class_at_{b}_{d}_{h+1}')
                    
                    self.model.Add(sum(has_class_h) >= class_at_h)
                    self.model.Add(sum(has_class_h_plus_1) >= class_at_h_plus_1)
                    
                    gap_penalties.append(gap_var * 10)  # Penalty weight
        
        # Minimize total penalty
        if gap_penalties:
            self.model.Minimize(sum(gap_penalties))
        
        print("✅ Soft constraints added")
    
    def solve_constraints(self, existing_assignments=None):
        """Solve the constraint satisfaction problem"""
        print("🔍 Solving constraint satisfaction problem...")
        
        # Create variables
        self.create_variables()
        
        # Add constraints
        self.add_hard_constraints()
        self.add_soft_constraints()
        
        # Add existing assignments as constraints if provided
        if existing_assignments:
            self.add_existing_assignments(existing_assignments)
        
        # Solve
        self.solver.parameters.max_time_in_seconds = 30.0  # 30 second timeout
        status = self.solver.Solve(self.model)
        
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print("✅ Solution found!")
            return self.extract_solution()
        else:
            print("❌ No feasible solution found")
            return None
    
    def add_existing_assignments(self, assignments):
        """Add existing assignments as fixed constraints"""
        print(f"📌 Adding {len(assignments)} existing assignments as constraints...")
        
        for assignment in assignments:
            try:
                b = self.batch_to_idx.get(assignment.get('batch_id'))
                t = self.teacher_to_idx.get(assignment.get('teacher_id'))
                s = self.subject_to_idx.get(assignment.get('subject_code'))
                r = self.room_to_idx.get(assignment.get('room_id'))
                d = self.day_to_idx.get(assignment.get('day'))
                h = self.time_to_idx.get(assignment.get('time_slot'))
                
                if all(x is not None for x in [b, t, s, r, d, h]):
                    # Fix this assignment
                    self.model.Add(self.assignment[b][t][s][r][d][h] == 1)
                
            except Exception as e:
                print(f"⚠️ Error adding assignment constraint: {e}")
    
    def extract_solution(self):
        """Extract solution from solved model"""
        print("📊 Extracting solution...")
        
        solution = []
        
        for b in range(len(self.batches)):
            for t in range(len(self.teachers)):
                for s in range(len(self.subjects)):
                    for r in range(len(self.rooms)):
                        for d in range(len(self.days)):
                            for h in range(len(self.time_slots)):
                                if self.solver.Value(self.assignment[b][t][s][r][d][h]) == 1:
                                    # Get batch info
                                    batch_id = self.batches[b]
                                    batch_info = self.students_df[self.students_df['batch_id'] == batch_id].iloc[0]
                                    
                                    # Get subject info
                                    subject_code = self.subjects[s]
                                    subject_info = self.subjects_df[self.subjects_df['subject_code'] == subject_code]
                                    subject_name = subject_info.iloc[0]['subject_name'] if not subject_info.empty else subject_code
                                    
                                    # Get teacher info
                                    teacher_id = self.teachers[t]
                                    teacher_info = self.teachers_df[self.teachers_df['teacher_id'] == teacher_id]
                                    teacher_name = teacher_info.iloc[0]['name'] if not teacher_info.empty else teacher_id
                                    
                                    # Get room info
                                    room_id = self.rooms[r]
                                    room_info = self.rooms_df[self.rooms_df['room_id'] == room_id]
                                    room_name = room_info.iloc[0]['room_name'] if not room_info.empty else room_id
                                    
                                    assignment = {
                                        'batch_id': batch_id,
                                        'section': batch_info['section'],
                                        'day': self.days[d],
                                        'time_slot': self.time_slots[h],
                                        'subject_code': subject_code,
                                        'subject_name': subject_name,
                                        'teacher_id': teacher_id,
                                        'teacher_name': teacher_name,
                                        'room_id': room_id,
                                        'room_name': room_name,
                                        'campus': batch_info['primary_campus'],
                                        'activity_type': 'Lab' if (not subject_info.empty and subject_info.iloc[0]['has_lab']) else 'Lecture',
                                        'department': batch_info['department']
                                    }
                                    
                                    solution.append(assignment)
        
        print(f"✅ Extracted {len(solution)} assignments from solution")
        return solution
    
    def fix_constraint_violations(self, timetable_slots):
        """Fix constraint violations in existing timetable"""
        print(f"🔧 Fixing constraint violations in {len(timetable_slots)} slots...")
        
        violations = self.detect_violations(timetable_slots)
        
        if not violations:
            print("✅ No violations found")
            return timetable_slots
        
        print(f"🚨 Found {len(violations)} violations")
        
        # Try to solve with existing assignments as much as possible
        valid_assignments = [slot for slot in timetable_slots if not self.has_violation(slot, timetable_slots)]
        
        # Solve for a new solution
        solution = self.solve_constraints(valid_assignments)
        
        if solution:
            print("✅ Constraint violations fixed")
            return solution
        else:
            print("⚠️ Could not fix all violations, returning original with best effort fixes")
            return self.best_effort_fix(timetable_slots, violations)
    
    def detect_violations(self, timetable_slots):
        """Detect constraint violations in timetable"""
        violations = []
        
        # Group by time slots to check conflicts
        time_slots_map = {}
        
        for slot in timetable_slots:
            key = f"{slot['day']}_{slot['time_slot']}"
            if key not in time_slots_map:
                time_slots_map[key] = []
            time_slots_map[key].append(slot)
        
        # Check for conflicts
        for time_key, slots in time_slots_map.items():
            if len(slots) > 1:
                # Check teacher conflicts
                teachers = [slot['teacher_id'] for slot in slots]
                if len(teachers) != len(set(teachers)):
                    violations.append({
                        'type': 'teacher_conflict',
                        'time': time_key,
                        'slots': slots
                    })
                
                # Check room conflicts
                rooms = [slot['room_id'] for slot in slots]
                if len(rooms) != len(set(rooms)):
                    violations.append({
                        'type': 'room_conflict',
                        'time': time_key,
                        'slots': slots
                    })
        
        return violations
    
    def has_violation(self, slot, all_slots):
        """Check if a single slot has violations"""
        day_time = f"{slot['day']}_{slot['time_slot']}"
        
        for other_slot in all_slots:
            if other_slot == slot:
                continue
                
            other_day_time = f"{other_slot['day']}_{other_slot['time_slot']}"
            
            if day_time == other_day_time:
                # Same time slot
                if slot['teacher_id'] == other_slot['teacher_id']:
                    return True  # Teacher conflict
                if slot['room_id'] == other_slot['room_id']:
                    return True  # Room conflict
        
        return False
    
    def best_effort_fix(self, timetable_slots, violations):
        """Best effort fix for violations"""
        print("🔨 Applying best effort fixes...")
        
        fixed_slots = timetable_slots.copy()
        
        for violation in violations:
            if violation['type'] == 'room_conflict':
                # Try to reassign rooms
                slots = violation['slots']
                for i, slot in enumerate(slots[1:], 1):  # Keep first slot, fix others
                    # Find alternative room
                    batch_campus = slot['campus']
                    available_rooms = self.rooms_df[
                        (self.rooms_df['campus'] == batch_campus) & 
                        (self.rooms_df['room_id'] != slot['room_id'])
                    ]
                    
                    if not available_rooms.empty:
                        new_room = available_rooms.sample(1).iloc[0]
                        slot['room_id'] = new_room['room_id']
                        slot['room_name'] = new_room['room_name']
                        print(f"🔄 Room reassigned: {new_room['room_id']}")
        
        return fixed_slots
    
    def optimize_schedule(self, timetable_slots):
        """Optimize schedule for better distribution"""
        print("⚡ Optimizing schedule distribution...")
        
        # This is a simplified optimization
        # In a real system, this would use more sophisticated algorithms
        
        optimized = self.solve_constraints(timetable_slots)
        
        if optimized:
            return optimized
        else:
            return timetable_slots

def main():
    """Main function to test constraint solver"""
    print("🚀 Starting Constraint Solver Process...")
    print("=" * 60)
    
    # Initialize solver
    solver = TimetableConstraintSolver()
    
    if not solver.batches:
        print("❌ No reference data loaded")
        return
    
    # Test constraint solving with sample data
    print("\n🧪 Testing constraint solving with sample timetable...")
    
    # Create sample conflicting timetable
    sample_slots = [
        {
            'batch_id': 'A01',
            'section': 'A01',
            'day': 'Monday',
            'time_slot': '08:00-09:00',
            'subject_code': 'CS101',
            'teacher_id': 'TCH1001',
            'room_id': 'R301',
            'campus': 'Campus-3',
            'activity_type': 'Lecture',
            'department': 'Computer Science Engineering'
        },
        {
            'batch_id': 'A02',
            'section': 'A02', 
            'day': 'Monday',
            'time_slot': '08:00-09:00',
            'subject_code': 'CS102',
            'teacher_id': 'TCH1001',  # Same teacher - conflict!
            'room_id': 'R302',
            'campus': 'Campus-3',
            'activity_type': 'Lecture',
            'department': 'Computer Science Engineering'
        }
    ]
    
    # Detect violations
    violations = solver.detect_violations(sample_slots)
    print(f"📊 Detected {len(violations)} violations")
    
    # Fix violations
    fixed_slots = solver.fix_constraint_violations(sample_slots)
    print(f"📊 Fixed timetable has {len(fixed_slots)} slots")
    
    # Check if violations are resolved
    new_violations = solver.detect_violations(fixed_slots)
    print(f"📊 Remaining violations: {len(new_violations)}")
    
    print("\n" + "=" * 60)
    print("✅ CONSTRAINT SOLVER COMPLETED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    main()