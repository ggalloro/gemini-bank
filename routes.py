from app import app, db, login
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import request, render_template, redirect, url_for, flash
from models import User, Account, Transaction
from forms import RegisterForm, LoginForm, CreateAccountForm, DepositForm, PaymentForm
from flask_login import login_required, login_user, logout_user, current_user


@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

@login.unauthorized_handler
def unauthorized():
    return redirect(url_for("login"))

@app.route("/")
def index():
    if current_user.is_authenticated:
        user = current_user
    else:
        user = "anonymous"
    return render_template("index.html", user = user)


@app.route("/register", methods = ["GET","POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(firstname = form.firstname.data, lastname = form.lastname.data, email = form.email.data)
        user.set_password(form.password1.data)
        db.session.add(user)
        try:
            db.session.commit()
            flash(f"User {user} registered correctly")
        except:
            db.session.rollback()
            flash("Problems in registration")
        return redirect(url_for('index'))           
    return render_template("register.html", form = form)


@app.route("/login", methods = ["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.email == form.email.data))
        if user and user.check_password(form.password.data):
            login_user(user, remember = form.remember.data)
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("mybank"))
        else:
            return redirect(url_for('login'))
    return render_template("login.html", form = form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/mybank", methods = ["GET","POST"])
@login_required
def mybank():
    if current_user.is_authenticated:
        user = current_user
    else:
        user = "anonymous"
    
    # Since 'accounts' is now a Mapped[List[Account]], we access it directly.
    # We must ensure current_user is attached to session or use a fresh query if needed, 
    # but flask-login usually handles this.
    accounts = user.accounts
    
    form = CreateAccountForm()
    if form.validate_on_submit():
        account_count = db.session.scalar(sa.select(sa.func.count()).select_from(Account))
        account = Account(balance=0,number=(160000+account_count+1),user_id=current_user.id)
        db.session.add(account)
        try:
            db.session.commit()
            flash(f"Account {account.number} created successfully")
        except:
            db.session.rollback()
            flash(f"Problem in account creation")
        return redirect(url_for('account', id=account.id))
    return render_template("mybank.html", user = user, accounts = accounts, form = form)

@app.route("/accounts/<int:id>", methods = ["GET","POST"])
@login_required
def account(id):
    if current_user.is_authenticated:
        user = current_user
    else:
        user = "anonymous"
    account = db.session.get(Account, id)
    # Accessing relationship directly instead of query
    transactions = account.transactions
    return render_template("account.html", user = user, account = account, transactions = transactions)

@app.route("/<int:id>/deposit", methods = ["GET","POST"])
@login_required
def deposit(id):
    if current_user.is_authenticated:
        user = current_user
    else:
        user = "anonymous"
    form = DepositForm()
    account = db.session.get(Account, id)
    if form.validate_on_submit():
        transaction = Transaction(amount = form.amount.data, type = "deposit", description = form.description.data, account_id=id)
        db.session.add(transaction)
        account.balance += transaction.amount
        try:
            flash(f"Deposit completed correctly")
            db.session.commit()
            return redirect(url_for('account', id=id))
        except:
            flash(f"Deposit failed")
            db.session.rollback()           
            return redirect(url_for('deposit', id=id))
    return render_template("deposit.html", user = user, account = account, form = form)

@app.route("/<int:id>/payment", methods = ["GET","POST"])
@login_required
def payment(id):
    if current_user.is_authenticated:
        user = current_user
    else:
        user = "anonymous"
    form = PaymentForm()
    account = db.session.get(Account, id)
    
    # Populate internal accounts choices (exclude current account)
    available_accounts = db.session.scalars(sa.select(Account).where(Account.id != id)).all()
    form.internal_account.choices = [(a.id, f"{a.number} - {a.owner.firstname} {a.owner.lastname}") for a in available_accounts]

    if form.validate_on_submit():
        amount = form.amount.data
        if amount > account.balance:
            flash("Insufficient funds")
            return redirect(url_for('payment', id=id))
            
        if form.payment_type.data == "internal":
            target_account = db.session.get(Account, form.internal_account.data)
            
            # Source Transaction
            t_source = Transaction(amount = -amount, type = "payment", description = f"Payment to {target_account.owner.firstname} {target_account.owner.lastname}: {form.description.data}", account_id=id)
            # Target Transaction
            t_target = Transaction(amount = amount, type = "transfer_in", description = f"Transfer from {account.owner.firstname} {account.owner.lastname}: {form.description.data}", account_id=target_account.id)
            
            db.session.add(t_source)
            db.session.add(t_target)
            account.balance -= amount
            target_account.balance += amount
            
        else: # External
            t_source = Transaction(amount = -amount, type = "payment", description = f"External to {form.external_account.data}: {form.description.data}", account_id=id)
            db.session.add(t_source)
            account.balance -= amount

        try:
            db.session.commit()
            flash(f"Payment completed correctly")
            return redirect(url_for('account', id=id))
        except:
            db.session.rollback()
            flash(f"Payment failed")
            return redirect(url_for('payment', id=id))
            
    return render_template("payment.html", user = user, account = account, form = form)