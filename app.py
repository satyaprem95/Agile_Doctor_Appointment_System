import os
import logging
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from data_store import DataStore
from auth import login_required, role_required

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")

# Initialize data store
data_store = DataStore()

@app.route('/')
def index():
    """Home page with login/register options"""
    if 'user_id' in session:
        user = data_store.get_user_by_id(session['user_id'])
        if user:
            if user['role'] == 'patient':
                return redirect(url_for('patient_dashboard'))
            elif user['role'] == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            elif user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'patient')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('register.html')
        
        if role not in ['patient', 'doctor']:
            flash('Invalid role selected', 'error')
            return render_template('register.html')
        
        # Check if user already exists
        if data_store.get_user_by_username(username):
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        if data_store.get_user_by_email(email):
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        # Create new user
        password_hash = generate_password_hash(password)
        user_id = data_store.create_user(username, email, password_hash, role)
        
        if user_id:
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('login.html')
        
        user = data_store.get_user_by_username(username)
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            
            flash(f'Welcome, {user["username"]}!', 'success')
            
            # Redirect based on role
            if user['role'] == 'patient':
                return redirect(url_for('patient_dashboard'))
            elif user['role'] == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            elif user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/patient/dashboard')
@login_required
@role_required('patient')
def patient_dashboard():
    """Patient dashboard"""
    user_id = session['user_id']
    appointments = data_store.get_appointments_by_patient(user_id)
    return render_template('patient_dashboard.html', appointments=appointments)

@app.route('/patient/book-appointment', methods=['GET', 'POST'])
@login_required
@role_required('patient')
def book_appointment():
    """Book new appointment"""
    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        reason = request.form.get('reason', '').strip()
        
        if not doctor_id or not appointment_date or not appointment_time:
            flash('All fields are required', 'error')
        else:
            try:
                # Validate date/time
                datetime.strptime(f"{appointment_date} {appointment_time}", "%Y-%m-%d %H:%M")
                
                appointment_id = data_store.create_appointment(
                    patient_id=session['user_id'],
                    doctor_id=int(doctor_id),
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                    reason=reason
                )
                
                if appointment_id:
                    flash('Appointment booked successfully!', 'success')
                    return redirect(url_for('patient_dashboard'))
                else:
                    flash('Failed to book appointment', 'error')
            except ValueError:
                flash('Invalid date or time format', 'error')
    
    doctors = data_store.get_doctors()
    return render_template('book_appointment.html', doctors=doctors)

@app.route('/doctor/dashboard')
@login_required
@role_required('doctor')
def doctor_dashboard():
    """Doctor dashboard"""
    user_id = session['user_id']
    appointments = data_store.get_appointments_by_doctor(user_id)
    return render_template('doctor_dashboard.html', appointments=appointments)

@app.route('/doctor/appointment/<int:appointment_id>/update', methods=['POST'])
@login_required
@role_required('doctor')
def update_appointment_status():
    """Update appointment status"""
    appointment_id = request.form.get('appointment_id')
    status = request.form.get('status')
    
    if appointment_id and status in ['approved', 'rejected', 'completed']:
        success = data_store.update_appointment_status(int(appointment_id), status)
        if success:
            flash(f'Appointment {status} successfully!', 'success')
        else:
            flash('Failed to update appointment', 'error')
    else:
        flash('Invalid request', 'error')
    
    return redirect(url_for('doctor_dashboard'))

@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    """Admin dashboard"""
    users = data_store.get_all_users()
    appointments = data_store.get_all_appointments()
    return render_template('admin_dashboard.html', users=users, appointments=appointments)

@app.route('/admin/appointment/<int:appointment_id>/update', methods=['POST'])
@login_required
@role_required('admin')
def admin_update_appointment():
    """Admin update appointment status"""
    appointment_id = request.form.get('appointment_id')
    status = request.form.get('status')
    
    if appointment_id and status in ['pending', 'approved', 'rejected', 'completed', 'cancelled']:
        success = data_store.update_appointment_status(int(appointment_id), status)
        if success:
            flash(f'Appointment {status} successfully!', 'success')
        else:
            flash('Failed to update appointment', 'error')
    else:
        flash('Invalid request', 'error')
    
    return redirect(url_for('admin_dashboard'))

# Initialize admin user if not exists
with app.app_context():
    if not data_store.get_user_by_username('admin'):
        admin_password = generate_password_hash('admin123')
        data_store.create_user('admin', 'admin@healthcare.com', admin_password, 'admin')
        logging.info("Admin user created with username: admin, password: admin123")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
