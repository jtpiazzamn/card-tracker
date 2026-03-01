from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    cards = db.relationship('Card', backref='owner', lazy=True)

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

    @property
    def profit_loss(self):
        if self.sell_price:
            return self.sell_price - self.buy_price
        elif self.market_price:
            return self.market_price - self.buy_price
        return None