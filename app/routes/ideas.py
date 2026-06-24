from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Idea, Review, AIAnalysis
from app.routes.ai import analyze_idea
import json

ideas = Blueprint('ideas', __name__)

@ideas.route('/')
def index():
    all_ideas = Idea.query.order_by(Idea.created_at.desc()).all()
    return render_template('index.html', ideas=all_ideas)

@ideas.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    if request.method == 'POST':
        if current_user.reputation < 20:
            flash('Not enough reputation points to submit an idea!')
            return redirect(url_for('ideas.index'))

        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        tags = request.form.get('tags')

        new_idea = Idea(
            title=title,
            description=description,
            category=category,
            tags=tags,
            user_id=current_user.id
        )
        current_user.reputation -= 20
        db.session.add(new_idea)
        db.session.commit()

        flash('Analyzing your idea with AI... 🤖')
        analysis = analyze_idea(title, description, category)

        ai_analysis = AIAnalysis(
            idea_id=new_idea.id,
            strengths=json.dumps(analysis.get('strengths', [])),
            weaknesses=json.dumps(analysis.get('weaknesses', [])),
            risks=json.dumps(analysis.get('risks', [])),
            questions=json.dumps(analysis.get('questions', []))
        )
        db.session.add(ai_analysis)
        db.session.commit()

        flash('Idea submitted successfully! AI analysis is ready 🎉')
        return redirect(url_for('ideas.idea_detail', idea_id=new_idea.id))

    return render_template('submit_idea.html')

@ideas.route('/idea/<int:idea_id>')
def idea_detail(idea_id):
    idea = Idea.query.get_or_404(idea_id)
    analysis = AIAnalysis.query.filter_by(idea_id=idea_id).first()

    strengths = json.loads(analysis.strengths) if analysis and analysis.strengths else []
    weaknesses = json.loads(analysis.weaknesses) if analysis and analysis.weaknesses else []
    risks = json.loads(analysis.risks) if analysis and analysis.risks else []
    questions = json.loads(analysis.questions) if analysis and analysis.questions else []

    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(
            idea_id=idea_id,
            reviewer_id=current_user.id
        ).first()

    return render_template('idea_detail.html',
                         idea=idea,
                         strengths=strengths,
                         weaknesses=weaknesses,
                         risks=risks,
                         questions=questions,
                         user_review=user_review)

@ideas.route('/idea/<int:idea_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_idea(idea_id):
    idea = Idea.query.get_or_404(idea_id)

    if idea.user_id != current_user.id:
        flash('Tum sirf apna idea edit kar sakte ho! ❌')
        return redirect(url_for('ideas.idea_detail', idea_id=idea_id))

    if request.method == 'POST':
        if current_user.reputation < 10:
            flash('Edit karne ke liye 10 points chahiye! ❌')
            return redirect(url_for('ideas.idea_detail', idea_id=idea_id))

        idea.title = request.form.get('title')
        idea.description = request.form.get('description')
        idea.category = request.form.get('category')
        idea.tags = request.form.get('tags')

        current_user.reputation -= 10
        db.session.commit()

        flash('Idea updated! -10 reputation points ✅')
        return redirect(url_for('ideas.idea_detail', idea_id=idea_id))

    return render_template('edit_idea.html', idea=idea)
@ideas.route('/idea/<int:idea_id>/delete', methods=['POST'])
@login_required
def delete_idea(idea_id):
    idea = Idea.query.get_or_404(idea_id)

    # Sirf owner delete kar sakta hai
    if idea.user_id != current_user.id:
        flash('Tum sirf apna idea delete kar sakte ho! ❌')
        return redirect(url_for('ideas.idea_detail', idea_id=idea_id))


    # Related reviews aur AI analysis bhi delete karo
    Review.query.filter_by(idea_id=idea_id).delete()
    AIAnalysis.query.filter_by(idea_id=idea_id).delete()

    db.session.delete(idea)
    db.session.commit()

    flash('Idea deleted!🗑️')
    return redirect(url_for('ideas.index'))

@ideas.route('/idea/<int:idea_id>/review', methods=['POST'])
@login_required
def review_idea(idea_id):
    idea = Idea.query.get_or_404(idea_id)

    if idea.user_id == current_user.id:
        flash('Tum apne khud ke idea ko review nahi kar sakte! ❌')
        return redirect(url_for('ideas.idea_detail', idea_id=idea_id))

    existing_review = Review.query.filter_by(
        idea_id=idea_id,
        reviewer_id=current_user.id
    ).first()

    if existing_review:
        flash('Tumne pehle se yeh idea review kiya hai! ❌')
        return redirect(url_for('ideas.idea_detail', idea_id=idea_id))

    new_review = Review(
        idea_id=idea_id,
        reviewer_id=current_user.id,
        market_need=int(request.form.get('market_need')),
        originality=int(request.form.get('originality')),
        feasibility=int(request.form.get('feasibility')),
        revenue_potential=int(request.form.get('revenue_potential')),
        comment=request.form.get('comment')
    )
    current_user.reputation += 10
    db.session.add(new_review)
    db.session.commit()
    flash('Review submitted! +10 reputation points 🎉')
    return redirect(url_for('ideas.idea_detail', idea_id=idea_id))

@ideas.route('/idea/<int:idea_id>/edit_review', methods=['POST'])
@login_required
def edit_review(idea_id):
    existing_review = Review.query.filter_by(
        idea_id=idea_id,
        reviewer_id=current_user.id
    ).first()

    if not existing_review:
        flash('Koi review nahi mili edit karne ke liye!')
        return redirect(url_for('ideas.idea_detail', idea_id=idea_id))

    existing_review.market_need = int(request.form.get('market_need'))
    existing_review.originality = int(request.form.get('originality'))
    existing_review.feasibility = int(request.form.get('feasibility'))
    existing_review.revenue_potential = int(request.form.get('revenue_potential'))
    existing_review.comment = request.form.get('comment')

    db.session.commit()
    flash('Review updated! ✅ (No extra points for editing)')
    return redirect(url_for('ideas.idea_detail', idea_id=idea_id))

@ideas.route('/trending')
def trending():
    from sqlalchemy import func

    trending_ideas = db.session.query(
        Idea,
        func.count(Review.id).label('review_count'),
        func.avg(
            (Review.market_need + Review.originality +
             Review.feasibility + Review.revenue_potential) / 4.0
        ).label('avg_rating')
    ).outerjoin(Review).group_by(Idea.id)\
     .order_by(func.count(Review.id).desc())\
     .limit(10).all()

    return render_template('trending.html', trending_ideas=trending_ideas)
@ideas.route('/search')
def search():
    query = request.args.get('q', '').strip()
    results = []
    
    if query:
        results = Idea.query.filter(
            db.or_(
                Idea.title.ilike(f'%{query}%'),
                Idea.description.ilike(f'%{query}%'),
                Idea.category.ilike(f'%{query}%'),
                Idea.tags.ilike(f'%{query}%')
            )
        ).order_by(Idea.created_at.desc()).all()
    
    return render_template('search.html', results=results, query=query)