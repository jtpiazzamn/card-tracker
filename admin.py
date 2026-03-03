from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Card
from functools import wraps

admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    
    user_data = []
    for user in users:
        cards = Card.query.filter_by(user_id=user.id).all()
        total_invested = sum(card.buy_price for card in cards)
        total_value = sum(
            card.sell_price if card.sell_price
            else (card.market_price or card.buy_price)
            for card in cards
        )
        profit_loss = total_value - total_invested
        
        user_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'date_joined': user.date_joined,
            'card_count': len(cards),
            'total_invested': total_invested,
            'total_value': total_value,
            'profit_loss': profit_loss
        })
    
    total_users = len(users)
    total_cards = Card.query.count()
    
    return render_template('admin.html',
        user_data=user_data,
        total_users=total_users,
        total_cards=total_cards
    )

@admin.route('/admin/make_admin/<int:user_id>')
@login_required
@admin_required
def make_admin(user_id):
    user = User.query.get_or_404(user_id)
    user.is_admin = True
    db.session.commit()
    flash(f'{user.username} is now an admin.')
    return redirect(url_for('admin.admin_dashboard'))

@admin.route('/admin/remove_admin/<int:user_id>')
@login_required
@admin_required
def remove_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot remove your own admin status.')
        return redirect(url_for('admin.admin_dashboard'))
    user.is_admin = False
    db.session.commit()
    flash(f'{user.username} admin status removed.')
    return redirect(url_for('admin.admin_dashboard'))

@admin.route('/admin/delete_user/<int:user_id>')
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('You cannot delete your own account.')
        return redirect(url_for('admin.admin_dashboard'))
    user = User.query.get_or_404(user_id)
    Card.query.filter_by(user_id=user_id).delete()
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} has been deleted.')
    return redirect(url_for('admin.admin_dashboard'))