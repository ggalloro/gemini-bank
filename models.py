from app import app, db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash



class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(40), unique=True, nullable=False)
    firstname = db.Column(db.String(20), nullable=False)
    lastname = db.Column(db.String(20), nullable=False)  
    password_hash = db.Column(db.String(40), nullable=False)
    accounts = db.relationship("Account", backref="owner", lazy="dynamic")
    joined_at = db.Column(db.DateTime(), default = datetime.utcnow())

    def set_password(self,password):
        self.password_hash = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"{ self.firstname } { self.lastname }"
    
class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    number = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.ForeignKey("user.id"), nullable=False)
    transactions = db.relationship("Transaction", backref="account", lazy="dynamic")
    created_at = db.Column(db.DateTime(), default = datetime.utcnow())

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Numeric(precision=10, scale=2), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(120), unique=True, nullable=False)
    account_id = db.Column(db.ForeignKey("account.id"), nullable=False)
    date = db.Column(db.DateTime(), default = datetime.utcnow())



with app.app_context():
    db.create_all()
