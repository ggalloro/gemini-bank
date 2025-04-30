from app import app, db, login
from flask import request, render_template, redirect, url_for, flash
from models import User, Account, Transaction
from forms import RegisterForm, LoginForm, CreateAccountForm, TransactionForm
from flask_login import login_required, login_user, logout_user, current_user


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

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
        user = User.query.filter_by(email=form.email.data).first()
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
    accounts = User.query.get(current_user.id).accounts.all()
    form = CreateAccountForm()
    if form.validate_on_submit():
        account = Account(balance=0,number=(160000+(Account.query.count())+1),user_id=current_user.id)
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
    account = Account.query.get(id)
    transactions = Transaction.query.filter_by(account_id=id).all()
    return render_template("account.html", user = user, account = account, transactions = transactions)

@app.route("/<int:id>/transaction", methods = ["GET","POST"])
@login_required
def transaction(id):
    if current_user.is_authenticated:
        user = current_user
    else:
        user = "anonymous"
    form = TransactionForm()
    account = Account.query.get(id)
    if form.validate_on_submit():
        if form.type.data == "deposit":
            transaction = Transaction(amount = form.amount.data, type = form.type.data, description = form.description.data, account_id=id)
        else:
            transaction = Transaction(amount = -(form.amount.data), type = form.type.data, description = form.description.data, account_id=id)
        db.session.add(transaction)
        account.balance += transaction.amount
        try:
            flash(f"{form.type.data } completed correctly")
            db.session.commit()
            return redirect(url_for('account', id=id))
        except:
            flash(f"{form.type.data } failed")
            db.session.rollback()           
            return redirect(url_for('transaction', id=id))
    return render_template("transaction.html", user = user, account = account, form = form)