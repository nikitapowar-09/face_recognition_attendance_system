from flask import render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from app import app, db
from models import *
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os


@app.route('/')
def landing_page():
    return render_template('welcome.html')
@app.route('/employee_login', methods=['GET', 'POST'])
def employee_login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        user = Employee.query.filter_by(emp_id=user_id).first()

        if user and user.password == password:  # Use hashed passwords in production
            login_user(user)
            return redirect(url_for('employee_dashboard'))
        else:
            flash("Invalid credentials", "error")

    return render_template('emp_login.html')

# Admin Login Page
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        user = Admin.query.filter_by(admin_id=user_id).first()

        if user and user.password == password:  # Use hashed passwords in production
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid credentials", "error")

    return render_template('admin_login.html')

@app.route('/employee/dashboard')
@login_required
def employee_dashboard():
    if not isinstance(current_user, Employee):
        return redirect(url_for('login'))  # Prevent admins from accessing employee page
    return render_template('employee_home.html', name=current_user.name)

@app.route('/employee/mark_attendance', methods=['POST'])
@login_required
def mark_attendance():
    emp_id = current_user.id
    name = current_user.name
    date = datetime.utcnow().date()

    existing_record = Attendance.query.filter_by(emp_id=emp_id, date=date).first()

    if existing_record:
        if not existing_record.check_out:
            existing_record.check_out = datetime.utcnow().time()
            db.session.commit()
            return redirect(url_for('dashboard'))
        flash("Attendance already marked", "error")
        return redirect(url_for('dashboard'))

    new_attendance = Attendance(emp_id=emp_id, name=name, check_in=datetime.utcnow().time(), status="Present")
    db.session.add(new_attendance)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/employee/request_leave', methods=['POST'])
@login_required
def request_leave():
    leave_date = datetime.strptime(request.form.get('leave_date'), "%Y-%m-%d").date()
    reason = request.form.get('reason')

    new_leave = LeaveRequest(emp_id=current_user.id, name=current_user.name, leave_date=leave_date, reason=reason)
    db.session.add(new_leave)
    db.session.commit()

    return redirect(url_for('dashboard'))


@app.route('/employee/logout')
@login_required
def employee_logout():
    logout_user()
    return jsonify({"message": "Logged out"}), 200

# ------------------- ADMIN ROUTES ------------------- #

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not isinstance(current_user, Admin):
        return redirect(url_for('login'))  # Prevent employees from accessing admin page
    return render_template('admin_home.html', username=current_user.username)

@app.route('/admin/view_attendance')
@login_required
def view_attendance():
    if not isinstance(current_user, Admin):
        return jsonify({"message": "Unauthorized"}), 403

    attendance_records = Attendance.query.all()
    return render_template('view_attendance.html', records=attendance_records)

@app.route('/admin/manage_leaves', methods=['GET', 'POST'])
@login_required
def manage_leaves():
    if not isinstance(current_user, Admin):
        return jsonify({"message": "Unauthorized"}), 403

    if request.method == 'GET':
        leave_requests = LeaveRequest.query.all()
        return jsonify([{
            "id": request.id,
            "emp_id": request.emp_id,
            "name": request.name,
            "leave_date": str(request.leave_date),
            "reason": request.reason,
            "status": request.status
        } for request in leave_requests])

    elif request.method == 'POST':
        data = request.json
        leave_id = data.get('id')
        action = data.get('action')  # Accept or Reject

        leave = LeaveRequest.query.get(leave_id)
        if leave:
            leave.status = action
            db.session.commit()
            return jsonify({"message": f"Leave {action} successfully"}), 200
        return jsonify({"message": "Leave request not found"}), 404

@app.route('/admin/register_employee', methods=['POST'])
@login_required
def register_employee():
    if not isinstance(current_user, Admin):
        return jsonify({"message": "Unauthorized"}), 403

    data = request.form
    name = data.get('name')
    email = data.get('email')
    phone = data.get('phone')
    password = generate_password_hash(data.get('password'))
    image = request.files.get('image')

    image_path = os.path.join('static/uploads', f"{email}.jpg")
    image.save(image_path)

    
    last_employee = Employee.query.order_by(Employee.id.desc()).first()
    new_emp_id = f"EMP{(last_employee.id + 1) if last_employee else 1:03d}"

    new_employee = Employee(name=name, email=email, phone=phone, password=password, image_path=image_path)
    db.session.add(new_employee)
    db.session.commit()

    return jsonify({"message": "Employee registered successfully"}), 201
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/register_admin', methods=['POST'])
@login_required
def register_admin():
    data = request.form
    username = data.get('username')
    password = generate_password_hash(data.get('password'))

    # Generate ADMIN ID (format: ADMIN001, ADMIN002, ...)
    last_admin = Admin.query.order_by(Admin.id.desc()).first()
    new_admin_id = f"ADMIN{(last_admin.id + 1) if last_admin else 1:03d}"

    new_admin = Admin(admin_id=new_admin_id, username=username, password=password)
    db.session.add(new_admin)
    db.session.commit()

    return redirect(url_for('admin_dashboard'))