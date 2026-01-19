import sqlalchemy as sa
import sqlalchemy.orm as so
from typing import List
from app import app, db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash



class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(40), unique=True, nullable=False)
    firstname: so.Mapped[str] = so.mapped_column(sa.String(20), nullable=False)
    lastname: so.Mapped[str] = so.mapped_column(sa.String(20), nullable=False)  
    password_hash: so.Mapped[str] = so.mapped_column(sa.String(40), nullable=False)
    
    accounts: so.Mapped[List["Account"]] = so.relationship(back_populates="owner")
    
    joined_at: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now())

    def set_password(self,password):
        self.password_hash = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"{ self.firstname } { self.lastname }"
    
class Account(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    balance: so.Mapped[float] = so.mapped_column(sa.Numeric(precision=10, scale=2), nullable=False)
    number: so.Mapped[int] = so.mapped_column(nullable=False)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id"), nullable=False)
    
    owner: so.Mapped["User"] = so.relationship(back_populates="accounts")
    transactions: so.Mapped[List["Transaction"]] = so.relationship(back_populates="account")
    
    created_at: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now())

class Transaction(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    amount: so.Mapped[float] = so.mapped_column(sa.Numeric(precision=10, scale=2), nullable=False)
    type: so.Mapped[str] = so.mapped_column(sa.String(20), nullable=False)
    description: so.Mapped[str] = so.mapped_column(sa.String(150), nullable=False)
    account_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("account.id"), nullable=False)
    
    account: so.Mapped["Account"] = so.relationship(back_populates="transactions")
    
    date: so.Mapped[datetime] = so.mapped_column(default=lambda: datetime.now())



with app.app_context():
    db.create_all()
