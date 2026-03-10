from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from models import db, User
from app import limiter

auth = Blueprint('auth', __name__)

@limiter.limit("5 per minute")
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Invalid email or password. Please try again.')
    return render_template('login.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        security_question = request.form.get('security_question')
        security_answer = request.form.get('security_answer')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already registered. Please log in.')
            return redirect(url_for('auth.login'))

        new_user = User(
            email=email,
            username=username,
            password=generate_password_hash(password),
            security_question=security_question,
            security_answer=security_answer.lower().strip() if security_answer else None
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('main.dashboard'))
    return render_template('register.html')

@auth.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    step = request.args.get('step', '1')
    
    if request.method == 'POST':
        if step == '1':
            username = request.form.get('username')
            user = User.query.filter_by(username=username).first()
            if not user or not user.security_question:
                flash('Username not found or no security question set.')
                return redirect(url_for('auth.forgot_password'))
            return render_template('forgot_password.html', step='2', user=user)

        elif step == '2':
            user_id = request.form.get('user_id')
            answer = request.form.get('security_answer', '').lower().strip()
            user = User.query.get(user_id)
            if not user or answer != user.security_answer:
                flash('Incorrect answer. Please try again.')
                return render_template('forgot_password.html', step='2', user=user)
            return render_template('forgot_password.html', step='3', user=user)

        elif step == '3':
            user_id = request.form.get('user_id')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            user = User.query.get(user_id)
            if new_password != confirm_password:
                flash('Passwords do not match.')
                return render_template('forgot_password.html', step='3', user=user)
            user.password = generate_password_hash(new_password)
            db.session.commit()
            flash('Password reset successfully. Please log in.')
            return redirect(url_for('auth.login'))

    return render_template('forgot_password.html', step='1')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
