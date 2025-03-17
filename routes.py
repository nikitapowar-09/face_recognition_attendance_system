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

@app.route('/employee/login', methods=['POST'])
def employee_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    employee = Employee.query.filter_by(email=email).first()

    if employee and check_password_hash(employee.password, password):
        login_user(employee)
        return jsonify({"message": "Login successful", "id": employee.id}), 200
    return jsonify({"message": "Invalid credentials"}), 401

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
            return jsonify({"message": "Check-out recorded"}), 200
        return jsonify({"message": "Attendance already marked"}), 400

    new_attendance = Attendance(emp_id=emp_id, name=name, check_in=datetime.utcnow().time(), status="Present")
    db.session.add(new_attendance)
    db.session.commit()
    return jsonify({"message": "Check-in recorded"}), 201

@app.route('/employee/request_leave', methods=['POST'])
@login_required
def request_leave():
    data = request.json
    leave_date = datetime.strptime(data.get('leave_date'), "%Y-%m-%d").date()
    reason = data.get('reason')

    new_leave = LeaveRequest(emp_id=current_user.id, name=current_user.name, leave_date=leave_date, reason=reason)
    db.session.add(new_leave)
    db.session.commit()
    return jsonify({"message": "Leave request submitted"}), 201

@app.route('/employee/logout')
@login_required
def employee_logout():
    logout_user()
    return jsonify({"message": "Logged out"}), 200

# ------------------- ADMIN ROUTES ------------------- #

@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    admin = Admin.query.filter_by(username=username).first()
    if admin and check_password_hash(admin.password, password):
        login_user(admin)
        return jsonify({"message": "Admin login successful"}), 200
    return jsonify({"message": "Invalid admin credentials"}), 401

@app.route('/admin/view_attendance', methods=['GET'])
@login_required
def view_attendance():
    if not isinstance(current_user, Admin):
        return jsonify({"message": "Unauthorized"}), 403

    attendance_records = Attendance.query.all()
    return jsonify([{
        "id": record.id,
        "emp_id": record.emp_id,
        "name": record.name,
        "date": str(record.date),
        "check_in": str(record.check_in) if record.check_in else None,
        "check_out": str(record.check_out) if record.check_out else None,
        "status": record.status
    } for record in attendance_records])

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

    image_path = os.path.join(UPLOAD_FOLDER, f"{email}.jpg")
    image.save(image_path)

    new_employee = Employee(name=name, email=email, phone=phone, password=password, image_path=image_path)
    db.session.add(new_employee)
    db.session.commit()

    return jsonify({"message": "Employee registered successfully"}), 201