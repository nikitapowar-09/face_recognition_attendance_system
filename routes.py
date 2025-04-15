from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

from app import app, db
from models import Employee, Admin, Attendance, LeaveRequest

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "employee_login"  # Redirect users to this route if they are not logged in

# User Loader Function
@login_manager.user_loader
def load_user(user_id):
    return Employee.query.get(int(user_id)) or Admin.query.get(int(user_id))

# ---------------- EMPLOYEE ROUTES ---------------- #
@app.route('/')
def landing_page():
    return render_template('welcome.html')

@app.route('/employee_login', methods=['GET', 'POST'])
def employee_login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        user = Employee.query.filter_by(emp_id=user_id).first()

        if user and check_password_hash(user.password, password):  # Use hashed password checking
            login_user(user)
            return redirect(url_for('employee_dashboard'))
        else:
            flash("Invalid credentials", "error")

    return render_template('emp_login.html')

@app.route('/employee/dashboard')
@login_required
def employee_dashboard():
    if not isinstance(current_user, Employee):
        return redirect(url_for('employee_login'))  # Prevent admins from accessing employee page
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
            flash("Checked out successfully!", "success")
            return redirect(url_for('employee_dashboard'))
        flash("Attendance already marked", "error")
        return redirect(url_for('employee_dashboard'))

    new_attendance = Attendance(emp_id=emp_id, name=name, check_in=datetime.utcnow().time(), status="Present")
    db.session.add(new_attendance)
    db.session.commit()
    flash("Checked in successfully!", "success")
    return redirect(url_for('employee_dashboard'))

@app.route('/employee/request_leave', methods=['POST'])
@login_required
def request_leave():
    leave_date = datetime.strptime(request.form.get('leave_date'), "%Y-%m-%d").date()
    reason = request.form.get('reason')

    new_leave = LeaveRequest(emp_id=current_user.id, name=current_user.name, leave_date=leave_date, reason=reason)
    db.session.add(new_leave)
    db.session.commit()

    flash("Leave request submitted!", "success")
    return redirect(url_for('employee_dashboard'))

@app.route('/employee/logout')
@login_required
def employee_logout():
    logout_user()
    return redirect(url_for("employee_login"))

# ---------------- ADMIN ROUTES ---------------- #
@app.route("/create_first_admin")
def create_first_admin():
    from werkzeug.security import generate_password_hash
    hashed_password = generate_password_hash("admin123",  method="pbkdf2:sha256")
    new_admin = Admin(admin_id="admin", password=hashed_password)
    db.session.add(new_admin)
    db.session.commit()
    return "First admin created successfully!"

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        admin_id = request.form.get("admin_id")
        password = request.form.get("password")

        admin = Admin.query.filter_by(admin_id=admin_id).first()

        if admin and check_password_hash(admin.password, password):
            session["admin_id"] = admin.admin_id  # Store admin session
            flash("Login successful!", "success")
            return redirect(url_for("admin_dashboard"))  # Redirect to admin dashboard
        
        flash("Invalid credentials!", "danger")
        return redirect(url_for("admin_login"))

    return render_template("admin_login.html")

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if "admin_id" not in session:
        return redirect(url_for('admin_login'))  
    admin = Admin.query.filter_by(admin_id=session["admin_id"]).first()
    return render_template('admin_home.html', username=admin.username)

@app.route('/admin/view_attendance')
@login_required
def view_attendance():
    if "admin_id" not in session:
        return jsonify({"message": "Unauthorized"}), 403

    attendance_records = Attendance.query.all()
    return render_template('check_att.html', records=attendance_records)

@app.route('/admin/manage_leaves', methods=['GET', 'POST'])
@login_required
def manage_leaves():
    if "admin_id" not in session:
        return jsonify({"message": "Unauthorized"}), 403

    if request.method == 'GET':
        leave_requests = LeaveRequest.query.all()
        return jsonify([{
            "id": req.id,
            "emp_id": req.emp_id,
            "name": req.name,
            "leave_date": str(req.leave_date),
            "reason": req.reason,
            "status": req.status
        } for req in leave_requests])

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
    if "admin_id" not in session:
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

    new_employee = Employee(emp_id=new_emp_id, name=name, email=email, phone=phone, password=password, image_path=image_path)
    db.session.add(new_employee)
    db.session.commit()

    flash("Employee registered successfully!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/register_admin', methods=['POST'])
@login_required
def register_admin():
    data = request.form
    username = data.get('username')
    password = generate_password_hash(data.get('password'))

    last_admin = Admin.query.order_by(Admin.id.desc()).first()
    new_admin_id = f"ADMIN{(last_admin.id + 1) if last_admin else 1:03d}"

    new_admin = Admin(admin_id=new_admin_id, username=username, password=password)
    db.session.add(new_admin)
    db.session.commit()

    flash("Admin registered successfully!", "success")
    return redirect(url_for('admin_dashboard'))
