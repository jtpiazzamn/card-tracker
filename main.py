import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Card
from search import search_card_price

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
                upload_folder = 'static/uploads'
                os.makedirs(upload_folder, exist_ok=True)
                photo.save(os.path.join(upload_folder, filename))
                photo_filename = filename

        # Search for market price automatically
        market_price = None
        if player_name:
            price, error = search_card_price(
                player_name, year, manufacturer, sport, condition
            )
            if price:
                market_price = price

        new_card = Card(
            player_name=player_name,
            sport=sport,
            year=year,
            manufacturer=manufacturer,
            condition=condition,
            buy_price=float(buy_price),
            sell_price=float(sell_price) if sell_price else None,
            photo_filename=photo_filename,
            market_price=market_price,
            user_id=current_user.id
        )
        db.session.add(new_card)
        db.session.commit()

        if market_price:
            flash(f'Card added! Market price found: ${market_price:.2f}')
        else:
            flash('Card added! No market price found automatically.')

        return redirect(url_for('main.dashboard'))

    return render_template('add_card.html')

@main.route('/search_price/<int:card_id>')
@login_required
def search_price(card_id):
    card = Card.query.get_or_404(card_id)
    if card.user_id != current_user.id:
        flash('Permission denied.')
        return redirect(url_for('main.dashboard'))

    price, error = search_card_price(
        card.player_name, card.year, card.manufacturer, card.sport, card.condition
    )

    if price:
        card.market_price = price
        db.session.commit()
        flash(f'Market price updated to ${price:.2f}')
    else:
        flash(f'Could not find market price. Try again later.')

    return redirect(url_for('main.dashboard'))

@main.route('/delete_card/<int:card_id>')
@login_required
def delete_card(card_id):
    card = Card.query.get_or_404(card_id)
    if card.user_id != current_user.id:
        flash('You do not have permission to delete this card.')
        return redirect(url_for('main.dashboard'))
    db.session.delete(card)
    db.session.commit()
    flash('Card deleted.')
    return redirect(url_for('main.dashboard'))