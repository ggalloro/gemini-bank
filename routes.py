from app import app, db, login
from flask import request, render_template, redirect, url_for, flash
from models import User, Account, Transaction
from forms import RegisterForm, LoginForm, CreateAccountForm, TransactionForm, DepositForm, PaymentForm
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

@app.route("/<int:id>/deposit", methods=["GET", "POST"])
@login_required
def deposit(id):
    if current_user.is_authenticated:
        user = current_user
    else:
        user = "anonymous"
    account = Account.query.get(id)
    if not account or account.user_id != current_user.id:
        flash("Unauthorized access to account.")
        return redirect(url_for('mybank'))
    
    form = DepositForm()
    if form.validate_on_submit():
        amount = form.amount.data
        description = form.description.data
        
        transaction = Transaction(
            amount=amount,
            type="deposit",
            description=description,
            account_id=id
        )
        db.session.add(transaction)
        account.balance += amount
        
        try:
            db.session.commit()
            flash("Deposit completed correctly")
            return redirect(url_for('account', id=id))
        except Exception as e:
            db.session.rollback()
            flash("Deposit failed")
            return redirect(url_for('deposit', id=id))
            
    return render_template("deposit.html", user=user, account=account, form=form)

@app.route("/<int:id>/payment", methods=["GET", "POST"])
@login_required
def payment(id):
    if current_user.is_authenticated:
        user = current_user
    else:
        user = "anonymous"
    account = Account.query.get(id)
    if not account or account.user_id != current_user.id:
        flash("Unauthorized access to account.")
        return redirect(url_for('mybank'))
    
    form = PaymentForm()
    
    # Populate the internal accounts choices
    other_accounts = Account.query.filter(Account.user_id != current_user.id).all()
    form.internal_account.choices = [(0, "Select an account...")] + [
        (acc.id, f"Account {acc.number} - {acc.owner.firstname} {acc.owner.lastname}")
        for acc in other_accounts
    ]
    
    if form.validate_on_submit():
        amount = form.amount.data
        description = form.description.data
        
        # Check if sufficient funds
        if account.balance < amount:
            flash("Insufficient funds for this payment.")
            return redirect(url_for('payment', id=id))
            
        if form.recipient_type.data == 'internal':
            dest_id = form.internal_account.data
            dest_account = Account.query.get(dest_id)
            if not dest_account:
                flash("Invalid destination account selected.")
                return redirect(url_for('payment', id=id))
            
            # Source account transaction (negative amount)
            source_tx = Transaction(
                amount=-amount,
                type="payment",
                description=f"To: {dest_account.owner.firstname} {dest_account.owner.lastname} (Acc {dest_account.number}) - {description}",
                account_id=id
            )
            # Destination account transaction (positive amount)
            dest_tx = Transaction(
                amount=amount,
                type="payment",
                description=f"From: {current_user.firstname} {current_user.lastname} (Acc {account.number}) - {description}",
                account_id=dest_id
            )
            
            account.balance -= amount
            dest_account.balance += amount
            
            db.session.add(source_tx)
            db.session.add(dest_tx)
        else:
            ext_acc_num = form.external_account.data
            source_tx = Transaction(
                amount=-amount,
                type="payment",
                description=f"External to {ext_acc_num} - {description}",
                account_id=id
            )
            account.balance -= amount
            db.session.add(source_tx)
            
        try:
            db.session.commit()
            flash("Payment completed correctly")
            return redirect(url_for('account', id=id))
        except Exception as e:
            db.session.rollback()
            flash("Payment failed")
            return redirect(url_for('payment', id=id))
            
    return render_template("payment.html", user=user, account=account, form=form)