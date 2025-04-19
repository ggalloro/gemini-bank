from app import app, db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash



class User(UserMixin, db.Model):
    id = db.column(db.Integer, primary_key=True)
    username = db.column(db.String(20), unique=True, nullable=False)
    email = db.column(db.String(40), unique=True, nullable=False)
    password_hash = db.column(db.String(40), nullable=False)
    accounts = db.relationship("Account", backref="owner", lazy="dynamic")
    joined_at = db.column(db.DateTime(), default = datetime.utcnow())

    def set_password(self,password):
        self.password_hash = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"{ self.username }"
    
class Account(db.Model):
    id = db.column(db.Integer, primary_key=True)
    balance = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    type = db.column(db.String(20), nullable=False)
    user_id = db.column(db.ForeignKey("user.id"), nullable=False)
    transactions = db.relationship("Transaction", backref="account", lazy="dynamic")
    created_at = db.column(db.DateTime(), default = datetime.utcnow())

class Transaction(db.Model):
    id = db.column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    type = db.column(db.String(20), nullable=False)
    description = db.column(db.String(120), unique=True, nullable=False)
    account_id = db.column(db.ForeignKey("account.id"), nullable=False)
    date = db.column(db.DateTime(), default = datetime.utcnow())



with app.app_context(app):
    db.create_all()
