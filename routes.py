from app import app, db, login
from flask import request, render_template, redirect, url_for, flash
from models import User, Account, Transaction
from forms import RegisterForm, LoginForm, CreateAccountForm, DepositForm, PaymentForm
from flask_login import login_required, login_user, logout_user, current_user
import sqlalchemy as sa

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
    
    # Use explicit select instead of lazy loading for clarity and 2.0 style
    accounts = db.session.scalars(sa.select(Account).where(Account.user_id == current_user.id)).all()
    
    form = CreateAccountForm()
    if form.validate_on_submit():
        # Count existing accounts for number generation
        account_count = db.session.scalar(sa.select(sa.func.count()).select_from(Account)) or 0
        account = Account(balance=0, number=(160000 + account_count + 1), user_id=current_user.id)
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
    transactions = db.session.scalars(sa.select(Transaction).where(Transaction.account_id == id)).all()
    
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
            db.session.commit()
            flash("Deposit completed correctly")
            return redirect(url_for('account', id=id))
        except:
            db.session.rollback()
            flash("Deposit failed")
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
    
    all_accounts = db.session.scalars(sa.select(Account).where(Account.id != id)).all()
    form.internal_account.choices = [(acc.id, f"{acc.number} - {acc.owner.firstname} {acc.owner.lastname}") for acc in all_accounts]

    if form.validate_on_submit():
        if account.balance < form.amount.data:
            flash("Insufficient funds")
            return redirect(url_for('payment', id=id))

        if form.payment_type.data == 'internal':
            recipient_id = form.internal_account.data
            recipient_account = db.session.get(Account, recipient_id)
            
            t_out = Transaction(amount = -form.amount.data, type = "transfer_out", description = f"To {recipient_account.owner.firstname} {recipient_account.owner.lastname}: {form.description.data}", account_id=id)
            t_in = Transaction(amount = form.amount.data, type = "transfer_in", description = f"From {user.firstname} {user.lastname}: {form.description.data}", account_id=recipient_id)
            
            db.session.add(t_out)
            db.session.add(t_in)
            account.balance -= form.amount.data
            recipient_account.balance += form.amount.data
            
        else:
            t_out = Transaction(amount = -form.amount.data, type = "payment_external", description = f"To External {form.external_account.data}: {form.description.data}", account_id=id)
            db.session.add(t_out)
            account.balance -= form.amount.data
            
        try:
            db.session.commit()
            flash("Payment completed correctly")
            return redirect(url_for('account', id=id))
        except:
            db.session.rollback()
            flash("Payment failed")
            return redirect(url_for('payment', id=id))
            
    return render_template("payment.html", user = user, account = account, form = form)