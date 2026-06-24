from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    reputation = db.Column(db.Integer, default=50)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    username = db.Column(db.String(50), unique=True)
    avatar_color = db.Column(db.String(20), default='#e94560')
    ideas = db.relationship('Idea', backref='author', lazy=True)

class Idea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    tags = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviews = db.relationship('Review', backref='idea', lazy=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    idea_id = db.Column(db.Integer, db.ForeignKey('idea.id'), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    market_need = db.Column(db.Integer, nullable=False)
    originality = db.Column(db.Integer, nullable=False)
    feasibility = db.Column(db.Integer, nullable=False)
    revenue_potential = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], backref='reviews_given')

class AIAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    idea_id = db.Column(db.Integer, db.ForeignKey('idea.id'), nullable=False)
    strengths = db.Column(db.Text)
    weaknesses = db.Column(db.Text)
    risks = db.Column(db.Text)
    questions = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)