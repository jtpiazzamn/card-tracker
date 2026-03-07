from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    date_joined = db.Column(db.DateTime, default=db.func.current_timestamp())
    cards = db.relationship('Card', backref='owner', lazy=True)
    lots = db.relationship('Lot', backref='owner', lazy=True)

class Lot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    total_sale_price = db.Column(db.Float, nullable=False)
    date_sold = db.Column(db.DateTime, default=db.func.current_timestamp())
    notes = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cards = db.relationship('Card', backref='lot', lazy=True, foreign_keys='Card.lot_id')

    @property
    def total_buy_price(self):
        return sum(card.buy_price for card in self.cards)

    @property
    def profit_loss(self):
        return self.total_sale_price - self.total_buy_price

    @property
    def card_count(self):
        return len(self.cards)

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(150), nullable=False)
    sport = db.Column(db.String(50))
    year = db.Column(db.String(10))
    manufacturer = db.Column(db.String(100))
    condition = db.Column(db.String(50))
    buy_price = db.Column(db.Float, nullable=False)
    sell_price = db.Column(db.Float)
    photo_filename = db.Column(db.String(300))
    market_price = db.Column(db.Float)
    date_added = db.Column(db.DateTime, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lot_id = db.Column(db.Integer, db.ForeignKey('lot.id'), nullable=True)

    @property
    def profit_loss(self):
        if self.sell_price:
            return self.sell_price - self.buy_price
        elif self.market_price:
            return self.market_price - self.buy_price
        return None

    @property
    def is_sold(self):
        return self.sell_price is not None or self.lot_id is not None
    