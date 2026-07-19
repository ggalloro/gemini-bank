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
        flash("Account not found or access denied.")
        return redirect(url_for('mybank'))
        
    form = DepositForm()
    if form.validate_on_submit():
        transaction = Transaction(amount=form.amount.data, type="deposit", description=form.description.data, account_id=id)
        db.session.add(transaction)
        account.balance += form.amount.data
        try:
            db.session.commit()
            flash("Deposit completed successfully")
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
    sender_account = Account.query.get(id)
    if not sender_account or sender_account.user_id != current_user.id:
        flash("Account not found or access denied.")
        return redirect(url_for('mybank'))
        
    form = PaymentForm()
    
    # Populate internal accounts choices (excluding sender's own accounts)
    other_accounts = Account.query.filter(Account.user_id != current_user.id).all()
    form.internal_account.choices = [(0, "Select an internal account...")] + [
        (acc.id, f"Account {acc.number} - {acc.owner.firstname} {acc.owner.lastname}")
        for acc in other_accounts
    ]
    
    if form.validate_on_submit():
        amount = form.amount.data
        
        # Check sufficient funds
        if sender_account.balance < amount:
            flash("Insufficient funds for this payment.")
            return redirect(url_for('payment', id=id))
            
        recipient_type = form.recipient_type.data
        description = form.description.data
        
        if recipient_type == "internal":
            if not form.internal_account.data or form.internal_account.data == 0:
                flash("Please select a valid internal recipient account.")
                return redirect(url_for('payment', id=id))
                
            recipient_account = Account.query.get(form.internal_account.data)
            if not recipient_account:
                flash("Recipient account not found.")
                return redirect(url_for('payment', id=id))
                
            # Perform internal transfer
            # 1. Sender Side
            sender_tx = Transaction(
                amount=-amount,
                type="payment",
                description=f"Payment to {recipient_account.owner.firstname} {recipient_account.owner.lastname} (Account {recipient_account.number}) - {description}",
                account_id=id
            )
            sender_account.balance -= amount
            db.session.add(sender_tx)
            
            # 2. Recipient Side
            dest_desc = f"payment from {current_user.firstname} {current_user.lastname} with description: {description}"
            recipient_tx = Transaction(
                amount=amount,
                type="payment",
                description=dest_desc,
                account_id=recipient_account.id
            )
            recipient_account.balance += amount
            db.session.add(recipient_tx)
            
            try:
                db.session.commit()
                flash("Internal payment completed successfully")
                return redirect(url_for('account', id=id))
            except Exception as e:
                db.session.rollback()
                flash("Payment failed")
                return redirect(url_for('payment', id=id))
                
        else: # External User
            external_dest = form.external_account.data
            if not external_dest:
                flash("Please provide external recipient account / reference details.")
                return redirect(url_for('payment', id=id))
                
            # Perform external transfer (only affects sender's account)
            sender_tx = Transaction(
                amount=-amount,
                type="payment",
                description=f"External payment to {external_dest} - {description}",
                account_id=id
            )
            sender_account.balance -= amount
            db.session.add(sender_tx)
            
            try:
                db.session.commit()
                flash("External payment completed successfully")
                return redirect(url_for('account', id=id))
            except Exception as e:
                db.session.rollback()
                flash("Payment failed")
                return redirect(url_for('payment', id=id))
                
    return render_template("payment.html", user=user, account=sender_account, form=form)