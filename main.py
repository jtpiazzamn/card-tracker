from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Card, db

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/dashboard')
@login_required
def dashboard():
    cards = Card.query.filter_by(user_id=current_user.id).all()
    total_invested = sum(card.buy_price for card in cards)
    total_value = sum(card.market_price or card.sell_price or card.buy_price for card in cards)
    total_profit_loss = total_value - total_invested
    return render_template('dashboard.html',
        cards=cards,
        total_invested=total_invested,
        total_value=total_value,
        total_profit_loss=total_profit_loss
    )