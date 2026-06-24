from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists!')
            return redirect(url_for('auth.register'))

        new_user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Account created! Please login.')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password!')
            return redirect(url_for('auth.login'))

        login_user(user)
        return redirect(url_for('ideas.index'))

    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/login/google')
def google_login():
    from flask import current_app
    import urllib.parse
    
    client_id = current_app.config['GOOGLE_CLIENT_ID']
    redirect_uri = url_for('auth.google_callback', _external=True)
    
    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'access_type': 'offline'
    }
    
    auth_url = 'https://accounts.google.com/o/oauth2/auth?' + urllib.parse.urlencode(params)
    return redirect(auth_url)

@auth.route('/login/google/authorized')
def google_callback():
    from flask import current_app
    import urllib.parse
    import urllib.request
    import json
    
    code = request.args.get('code')
    if not code:
        flash('Google login failed!')
        return redirect(url_for('auth.login'))
    
    # Exchange code for token
    token_url = 'https://oauth2.googleapis.com/token'
    token_data = {
        'code': code,
        'client_id': current_app.config['GOOGLE_CLIENT_ID'],
        'client_secret': current_app.config['GOOGLE_CLIENT_SECRET'],
        'redirect_uri': url_for('auth.google_callback', _external=True),
        'grant_type': 'authorization_code'
    }
    
    token_data_encoded = urllib.parse.urlencode(token_data).encode('utf-8')
    token_req = urllib.request.Request(token_url, data=token_data_encoded, method='POST')
    token_req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    
    with urllib.request.urlopen(token_req) as response:
        token_response = json.loads(response.read().decode('utf-8'))
    
    access_token = token_response.get('access_token')
    
    # Get user info
    user_info_url = f'https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}'
    with urllib.request.urlopen(user_info_url) as response:
        user_info = json.loads(response.read().decode('utf-8'))
    
    email = user_info.get('email')
    name = user_info.get('name')
    
    # Check if user exists
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash('google-oauth-user')
        )
        db.session.add(user)
        db.session.commit()
    
    login_user(user)
    flash(f'Welcome {name}! Logged in with Google. 🎉')
    return redirect(url_for('ideas.index'))