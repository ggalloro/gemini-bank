import sqlalchemy as sa
import sqlalchemy.orm as so
from app import app, db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(40), unique=True)
    firstname: so.Mapped[str] = so.mapped_column(sa.String(20))
    lastname: so.Mapped[str] = so.mapped_column(sa.String(20))
    password_hash: so.Mapped[str] = so.mapped_column(sa.String(255))
    
    # Relationships
    accounts: so.Mapped[list["Account"]] = so.relationship(back_populates="owner")
    
    joined_at: so.Mapped[datetime] = so.mapped_column(default=datetime.now)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"{self.firstname} {self.lastname}"
    
class Account(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    balance: so.Mapped[float] = so.mapped_column(sa.Numeric(precision=10, scale=2))
    number: so.Mapped[int] = so.mapped_column()
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("user.id"))
    
    # Relationships
    owner: so.Mapped["User"] = so.relationship(back_populates="accounts")
    transactions: so.Mapped[list["Transaction"]] = so.relationship(back_populates="account")
    
    created_at: so.Mapped[datetime] = so.mapped_column(default=datetime.now)

class Transaction(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    amount: so.Mapped[float] = so.mapped_column(sa.Numeric(precision=10, scale=2))
    type: so.Mapped[str] = so.mapped_column(sa.String(20))
    description: so.Mapped[str] = so.mapped_column(sa.String(150))
    account_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey("account.id"))
    
    # Relationships
    account: so.Mapped["Account"] = so.relationship(back_populates="transactions")
    
    date: so.Mapped[datetime] = so.mapped_column(default=datetime.now)

with app.app_context():
    db.create_all()