from datetime import datetime
import threading

class DataStore:
    """In-memory data store for users and appointments"""
    
    def __init__(self):
        self.users = {}
        self.appointments = {}
        self.next_user_id = 1
        self.next_appointment_id = 1
        self.lock = threading.Lock()
    
    def create_user(self, username, email, password_hash, role):
        """Create a new user"""
        with self.lock:
            user_id = self.next_user_id
            self.users[user_id] = {
                'id': user_id,
                'username': username,
                'email': email,
                'password_hash': password_hash,
                'role': role,
                'created_at': datetime.now()
            }
            self.next_user_id += 1
            return user_id
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        return self.users.get(user_id)
    
    def get_user_by_username(self, username):
        """Get user by username"""
        for user in self.users.values():
            if user['username'] == username:
                return user
        return None
    
    def get_user_by_email(self, email):
        """Get user by email"""
        for user in self.users.values():
            if user['email'] == email:
                return user
        return None
    
    def get_doctors(self):
        """Get all doctors"""
        return [user for user in self.users.values() if user['role'] == 'doctor']
    
    def get_all_users(self):
        """Get all users"""
        return list(self.users.values())
    
    def create_appointment(self, patient_id, doctor_id, appointment_date, appointment_time, reason):
        """Create a new appointment"""
        with self.lock:
            appointment_id = self.next_appointment_id
            
            # Get patient and doctor info
            patient = self.get_user_by_id(patient_id)
            doctor = self.get_user_by_id(doctor_id)
            
            if not patient or not doctor:
                return None
            
            self.appointments[appointment_id] = {
                'id': appointment_id,
                'patient_id': patient_id,
                'doctor_id': doctor_id,
                'patient_name': patient['username'],
                'doctor_name': doctor['username'],
                'appointment_date': appointment_date,
                'appointment_time': appointment_time,
                'reason': reason,
                'status': 'pending',
                'created_at': datetime.now()
            }
            self.next_appointment_id += 1
            return appointment_id
    
    def get_appointments_by_patient(self, patient_id):
        """Get appointments for a specific patient"""
        return [apt for apt in self.appointments.values() if apt['patient_id'] == patient_id]
    
    def get_appointments_by_doctor(self, doctor_id):
        """Get appointments for a specific doctor"""
        return [apt for apt in self.appointments.values() if apt['doctor_id'] == doctor_id]
    
    def get_all_appointments(self):
        """Get all appointments"""
        return list(self.appointments.values())
    
    def update_appointment_status(self, appointment_id, status):
        """Update appointment status"""
        with self.lock:
            if appointment_id in self.appointments:
                self.appointments[appointment_id]['status'] = status
                self.appointments[appointment_id]['updated_at'] = datetime.now()
                return True
            return False
    
    def get_appointment_by_id(self, appointment_id):
        """Get appointment by ID"""
        return self.appointments.get(appointment_id)
