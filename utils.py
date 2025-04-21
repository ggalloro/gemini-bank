from app import app,db
from models import User, Account, Transaction

# with app.app_context():
#     user = User(firstname = "Gennaro", lastname = "Esposito", email = "gennaro@casamia.net", password_hash="45jjkio")
#     db.session.add(user)
#     db.session.commit()


with app.app_context():
    users = User.query.all()
    for user in users:
        print(f"{user.firstname} {user.lastname} {user.email}")

with app.app_context():
    accounts = Account.query.all()
    for account in accounts:
        print(f"{account.number} {account.owner}")