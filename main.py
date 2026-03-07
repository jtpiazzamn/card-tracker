import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Card, Lot
from search import search_card_price
from PIL import Image

main = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def resize_image(filepath, max_size=(800, 800)):
    img = Image.open(filepath)
    img.thumbnail(max_size, Image.LANCZOS)
    img.save(filepath, optimize=True, quality=85)

@main.route('/')
@main.route('/dashboard')
@login_required
def dashboard():
    sport_filter = request.args.get('sport', 'all')
    sort_by = request.args.get('sort', 'date')

    query = Card.query.filter_by(user_id=current_user.id)

    if sport_filter != 'all':
        query = query.filter_by(sport=sport_filter)

    if sort_by == 'value_high':
        cards = sorted(query.all(), key=lambda c: c.market_price or c.sell_price or c.buy_price, reverse=True)
    elif sort_by == 'value_low':
        cards = sorted(query.all(), key=lambda c: c.market_price or c.sell_price or c.buy_price)
    elif sort_by == 'profit_high':
        cards = sorted(query.all(), key=lambda c: c.profit_loss or 0, reverse=True)
    elif sort_by == 'profit_low':
        cards = sorted(query.all(), key=lambda c: c.profit_loss or 0)
    elif sort_by == 'name':
        cards = sorted(query.all(), key=lambda c: c.player_name)
    else:
        cards = query.order_by(Card.date_added.desc()).all()

    all_cards = Card.query.filter_by(user_id=current_user.id).all()
    total_invested = sum(card.buy_price for card in all_cards)

    est_market_value = sum(
        card.market_price or card.buy_price
        for card in all_cards
        if not card.sell_price
    )

    realized_gains = sum(
        card.sell_price - card.buy_price
        for card in all_cards
        if card.sell_price
    )

    total_value = sum(
        card.sell_price if card.sell_price
        else (card.market_price or card.buy_price)
        for card in all_cards
    )

    total_profit_loss = total_value - total_invested

    sports = ['Baseball', 'Basketball', 'Football', 'Hockey', 'Soccer', 'Other']

    return render_template('dashboard.html',
        cards=cards,
        total_invested=total_invested,
        total_value=total_value,
        total_profit_loss=total_profit_loss,
        est_market_value=est_market_value,
        realized_gains=realized_gains,
        sport_filter=sport_filter,
        sort_by=sort_by,
        sports=sports
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
        notes = request.form.get('notes')

        photo_filename = None
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                upload_folder = 'static/uploads'
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                photo.save(filepath)
                resize_image(filepath)
                photo_filename = filename

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
            notes=notes,
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

@main.route('/edit_card/<int:card_id>', methods=['GET', 'POST'])
@login_required
def edit_card(card_id):
    card = Card.query.get_or_404(card_id)
    if card.user_id != current_user.id:
        flash('Permission denied.')
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        card.player_name = request.form.get('player_name')
        card.sport = request.form.get('sport')
        card.year = request.form.get('year')
        card.manufacturer = request.form.get('manufacturer')
        card.condition = request.form.get('condition')
        card.buy_price = float(request.form.get('buy_price'))
        sell_price = request.form.get('sell_price')
        card.sell_price = float(sell_price) if sell_price else None
        card

        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                upload_folder = 'static/uploads'
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                photo.save(filepath)
                resize_image(filepath)
                card.photo_filename = filename

        db.session.commit()
        flash('Card updated successfully.')
        return redirect(url_for('main.card_detail', card_id=card.id))

    return render_template('edit_card.html', card=card)

@main.route('/card/<int:card_id>')
@login_required
def card_detail(card_id):
    card = Card.query.get_or_404(card_id)
    if card.user_id != current_user.id:
        flash('Permission denied.')
        return redirect(url_for('main.dashboard'))
    return render_template('card_detail.html', card=card)

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
        flash('Could not find market price. Try again later.')

    return redirect(url_for('main.dashboard'))

@main.route('/export_csv')
@login_required
def export_csv():
    import csv
    import io
    from flask import Response

    cards = Card.query.filter_by(user_id=current_user.id).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'Player Name', 'Sport', 'Year', 'Manufacturer',
        'Condition', 'Buy Price', 'Sell Price', 'Market Price',
        'Profit/Loss', 'Date Added'
    ])

    for card in cards:
        writer.writerow([
            card.player_name,
            card.sport or '',
            card.year or '',
            card.manufacturer or '',
            card.condition or '',
            f'${card.buy_price:.2f}',
            f'${card.sell_price:.2f}' if card.sell_price else '',
            f'${card.market_price:.2f}' if card.market_price else '',
            f'${card.profit_loss:.2f}' if card.profit_loss is not None else '',
            card.date_added.strftime('%Y-%m-%d') if card.date_added else ''
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=card-collection.csv'}
    )

@main.route('/import_cards', methods=['GET', 'POST'])
@login_required
def import_cards():
    import csv
    import io
    import openpyxl

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected.')
            return redirect(url_for('main.import_cards'))

        file = request.files['file']
        if file.filename == '':
            flash('No file selected.')
            return redirect(url_for('main.import_cards'))

        filename = file.filename.lower()
        rows = []
        errors = []
        imported = 0

        try:
            if filename.endswith('.csv'):
                stream = io.StringIO(file.stream.read().decode('utf-8'))
                reader = csv.DictReader(stream)
                rows = list(reader)

            elif filename.endswith('.xlsx'):
                wb = openpyxl.load_workbook(file)
                ws = wb.active
                headers = [cell.value for cell in ws[1]]
                for row in ws.iter_rows(min_row=2, values_only=True):
                    rows.append(dict(zip(headers, row)))

            else:
                flash('Please upload a CSV or Excel (.xlsx) file.')
                return redirect(url_for('main.import_cards'))

        except Exception as e:
            flash(f'Error reading file: {str(e)}')
            return redirect(url_for('main.import_cards'))

        for i, row in enumerate(rows, start=2):
            try:
                player_name = row.get('Player Name') or row.get('player_name') or row.get('Name')
                if not player_name:
                    errors.append(f'Row {i}: Missing player name')
                    continue

                buy_price_raw = row.get('Buy Price') or row.get('buy_price') or '0'
                buy_price_str = str(buy_price_raw).replace('$', '').replace(',', '').strip()
                buy_price = float(buy_price_str) if buy_price_str else 0.0

                sell_price_raw = row.get('Sell Price') or row.get('sell_price') or ''
                sell_price_str = str(sell_price_raw).replace('$', '').replace(',', '').strip()
                sell_price = float(sell_price_str) if sell_price_str else None

                market_price_raw = row.get('Market Price') or row.get('market_price') or ''
                market_price_str = str(market_price_raw).replace('$', '').replace(',', '').strip()
                market_price = float(market_price_str) if market_price_str else None

                new_card = Card(
                    player_name=str(player_name).strip(),
                    sport=str(row.get('Sport') or row.get('sport') or '').strip() or None,
                    year=str(row.get('Year') or row.get('year') or '').strip() or None,
                    manufacturer=str(row.get('Manufacturer') or row.get('manufacturer') or '').strip() or None,
                    condition=str(row.get('Condition') or row.get('condition') or '').strip() or None,
                    buy_price=buy_price,
                    sell_price=sell_price,
                    market_price=market_price,
                    user_id=current_user.id
                )
                db.session.add(new_card)
                imported += 1

            except Exception as e:
                errors.append(f'Row {i}: {str(e)}')

        db.session.commit()

        if errors:
            flash(f'Imported {imported} cards. {len(errors)} rows had errors: {", ".join(errors[:3])}')
        else:
            flash(f'Successfully imported {imported} cards.')

        return redirect(url_for('main.dashboard'))

    return render_template('import_cards.html')

@main.route('/lots')
@login_required
def lots():
    lots = Lot.query.filter_by(user_id=current_user.id).order_by(Lot.date_sold.desc()).all()
    return render_template('lots.html', lots=lots)

@main.route('/create_lot', methods=['GET', 'POST'])
@login_required
def create_lot():
    if request.method == 'POST':
        name = request.form.get('name')
        total_sale_price = float(request.form.get('total_sale_price'))
        notes = request.form.get('notes')
        card_ids = request.form.getlist('card_ids')

        if not card_ids:
            flash('Please select at least one card for the lot.')
            return redirect(url_for('main.create_lot'))

        new_lot = Lot(
            name=name,
            total_sale_price=total_sale_price,
            notes=notes,
            user_id=current_user.id
        )
        db.session.add(new_lot)
        db.session.flush()

        price_per_card = total_sale_price / len(card_ids)

        for card_id in card_ids:
            card = Card.query.get(int(card_id))
            if card and card.user_id == current_user.id:
                card.lot_id = new_lot.id
                card.sell_price = round(price_per_card, 2)

        db.session.commit()
        flash(f'Lot created with {len(card_ids)} cards sold for ${total_sale_price:.2f}')
        return redirect(url_for('main.lots'))

    unsold_cards = Card.query.filter_by(
        user_id=current_user.id,
        lot_id=None
    ).filter(Card.sell_price == None).order_by(Card.player_name).all()

    return render_template('create_lot.html', cards=unsold_cards)

@main.route('/delete_lot/<int:lot_id>')
@login_required
def delete_lot(lot_id):
    lot = Lot.query.get_or_404(lot_id)
    if lot.user_id != current_user.id:
        flash('Permission denied.')
        return redirect(url_for('main.lots'))

    for card in lot.cards:
        card.lot_id = None
        card.sell_price = None

    db.session.delete(lot)
    db.session.commit()
    flash('Lot deleted and cards returned to collection.')
    return redirect(url_for('main.lots'))

@main.route('/delete_card/<int:card_id>')
@login_required
def delete_card(card_id):
    card = Card.query.get_or_404(card_id)
    if card.user_id != current_user.id:
        flash('Permission denied.')
        return redirect(url_for('main.dashboard'))
    db.session.delete(card)
    db.session.commit()
    flash('Card deleted.')
    return redirect(url_for('main.dashboard'))