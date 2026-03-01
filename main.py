import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Card

main = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

@main.route('/add_card', methods=['GET', 'POST'])
@login_required
def add_card():
    if request.method == 'POST':
        player_name = request.form.get('player_name')
        sport = request.form.get('sport')
        year = request.form.get('year')
        manufacturer = request.form.get('manufacturer')
        condition = request.form.get('condition')
        buy_price = request.form.get('buy_price')
        sell_price = request.form.get('sell_price')

        photo_filename = None
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                from app import create_app
                upload_folder = 'static/uploads'
                os.makedirs(upload_folder, exist_ok=True)
                photo.save(os.path.join(upload_folder, filename))
                photo_filename = filename

        new_card = Card(
            player_name=player_name,
            sport=sport,
            year=year,
            manufacturer=manufacturer,
            condition=condition,
            buy_price=float(buy_price),
            sell_price=float(sell_price) if sell_price else None,
            photo_filename=photo_filename,
            user_id=current_user.id
        )
        db.session.add(new_card)
        db.session.commit()
        flash('Card added successfully!')
        return redirect(url_for('main.dashboard'))

    return render_template('add_card.html')

@main.route('/delete_card/<int:card_id>')
@login_required
def delete_card(card_id):
    card = Card.query.get_o