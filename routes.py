from flask import render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from app import app, db
from models import User
import os

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        image = request.files['image']

        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)

            new_user = User(name=name, email=email, image_path=image_path)
            db.session.add(new_user)
            db.session.commit()

            flash('User registered successfully!', 'success')
            return redirect(url_for('index'))

    return render_template('register.html')
