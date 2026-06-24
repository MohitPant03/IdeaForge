from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import User, Idea, Review

profile = Blueprint('profile', __name__)

@profile.route('/profile/<int:user_id>')
def view_profile(user_id):
    user = User.query.get_or_404(user_id)
    ideas = Idea.query.filter_by(user_id=user_id).order_by(Idea.created_at.desc()).all()
    reviews_given = Review.query.filter_by(reviewer_id=user_id).count()
    return render_template('profile.html', user=user, ideas=ideas, reviews_given=reviews_given)

@profile.route('/profile')
@login_required
def my_profile():
    return view_profile(current_user.id)

@profile.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        username = request.form.get('username').strip().lower()
        avatar_color = request.form.get('avatar_color')

        # Username unique check
        if username:
            existing = User.query.filter_by(username=username).first()
            if existing and existing.id != current_user.id:
                flash('Username already taken! ❌')
                return redirect(url_for('profile.edit_profile'))
            current_user.username = username

        if avatar_color:
            current_user.avatar_color = avatar_color

        db.session.commit()
        flash('Profile updated! ✅')
        return redirect(url_for('profile.my_profile'))

    return render_template('edit_profile.html')