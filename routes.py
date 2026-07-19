from app import app, db, login
from flask import request, render_template, redirect, url_for, flash
from models import User, Account, Transaction
from forms import RegisterForm, LoginForm, CreateAccountForm, DepositForm, PaymentForm
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

@app.route("/accounts/<int:id>/deposit", methods=["GET", "POST"])
@login_required
def deposit(id):
    if current_user.is_authenticated:
        user = current_user
    else:
        user = "anonymous"
    
    account = Account.query.get(id)
    if not account:
        flash("Account not found.")
        return redirect(url_for('mybank'))
        
    # Security check: verify logged in user owns this account
    if account.user_id != current_user.id:
        flash("You are not authorized to view or modify this account.")
        return redirect(url_for('mybank'))
        
    form = DepositForm()
    if form.validate_on_submit():
        transaction = Transaction(
            amount=form.amount.data,
            type="deposit",
            description=form.description.data,
            account_id=id
        )
        db.session.add(transaction)
        account.balance += form.amount.data
        try:
            db.session.commit()
            flash("Deposit completed successfully.")
            return redirect(url_for('account', id=id))
        except Exception as e:
            db.session.rollback()
            flash("Deposit failed. Please try again.")
            return redirect(url_for('deposit', id=id))
            
    return render_template("deposit.html", user=user, account=account, form=form)


@app.route("/accounts/<int:id>/payment", methods=["GET", "POST"])
@login_required
def payment(id):
    if current_user.is_authenticated:
        user = current_user
    else:
        user = "anonymous"
        
    account = Account.query.get(id)
    if not account:
        flash("Account not found.")
        return redirect(url_for('mybank'))
        
    # Security check: verify logged in user owns this account
    if account.user_id != current_user.id:
        flash("You are not authorized to view or modify this account.")
        return redirect(url_for('mybank'))
        
    form = PaymentForm()
    
    # Populate the internal recipients choice list with all other registered accounts
    all_accounts = Account.query.filter(Account.id != id).all()
    form.internal_recipient.choices = [
        (acc.id, f"Account {acc.number} - {acc.owner.firstname} {acc.owner.lastname}")
        for acc in all_accounts
    ] if all_accounts else [(-1, "No other internal accounts available")]

    if form.validate_on_submit():
        amount = form.amount.data
        
        # Check sufficient funds
        if account.balance < amount:
            flash("Payment failed: Insufficient funds.")
            return render_template("payment.html", user=user, account=account, form=form)
            
        if form.recipient_type.data == "internal":
            dest_acc_id = form.internal_recipient.data
            if dest_acc_id == -1 or not dest_acc_id:
                flash("Payment failed: No valid internal recipient account selected.")
                return render_template("payment.html", user=user, account=account, form=form)
                
            dest_account = Account.query.get(dest_acc_id)
            if not dest_account:
                flash("Payment failed: Destination account does not exist.")
                return render_template("payment.html", user=user, account=account, form=form)
                
            # Perform transfer to internal account
            sender_tx = Transaction(
                amount=-amount,
                type="payment",
                description=form.description.data,
                account_id=id
            )
            
            sender_name = f"{current_user.firstname} {current_user.lastname}"
            dest_tx = Transaction(
                amount=amount,
                type="payment",
                description=f"Payment from {sender_name} with description: {form.description.data}",
                account_id=dest_account.id
            )
            
            db.session.add(sender_tx)
            db.session.add(dest_tx)
            
            account.balance -= amount
            dest_account.balance += amount
            
        else: # "external"
            ext_recipient = form.external_recipient.data
            if not ext_recipient or ext_recipient.strip() == "":
                flash("Payment failed: External recipient details are required.")
                return render_template("payment.html", user=user, account=account, form=form)
                
            # Perform external payment
            sender_tx = Transaction(
                amount=-amount,
                type="payment",
                description=f"Payment to {ext_recipient.strip()}: {form.description.data}",
                account_id=id
            )
            db.session.add(sender_tx)
            account.balance -= amount
            
        try:
            db.session.commit()
            flash("Payment completed successfully.")
            return redirect(url_for('account', id=id))
        except Exception as e:
            db.session.rollback()
            flash("Payment failed. Please try again.")
            return redirect(url_for('payment', id=id))
            
    return render_template("payment.html", user=user, account=account, form=form)