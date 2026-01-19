import pytest
from app import db
from models import User, Account, Transaction
import sqlalchemy as sa

def register_user(client, email="test@example.com", password="password"):
    return client.post("/register", data={
        "firstname": "Test",
        "lastname": "User",
        "email": email,
        "password1": password,
        "password2": password
    }, follow_redirects=True)

def login_user(client, email="test@example.com", password="password"):
    return client.post("/login", data={
        "email": email,
        "password": password
    }, follow_redirects=True)

def create_account(client):
    return client.post("/mybank", data={}, follow_redirects=True)

def test_index_anonymous(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Welcome to Gemini Bank" in response.data or b"Login" in response.data # Check for content present in index.html

def test_register(client, test_app):
    response = register_user(client)
    assert response.status_code == 200
    with test_app.app_context():
        user = db.session.scalar(sa.select(User).where(User.email == "test@example.com"))
        assert user is not None
        assert user.firstname == "Test"

def test_login_logout(client, test_app):
    register_user(client)
    response = login_user(client)
    assert response.status_code == 200
    # Check if we are logged in - index page should show user name or "mybank" link
    assert b"Logout" in response.data
    
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data

def test_mybank_create_account(client, test_app):
    register_user(client)
    login_user(client)
    
    response = client.get("/mybank")
    assert response.status_code == 200
    
    # Create account
    response = create_account(client)
    assert response.status_code == 200
    assert b"Account Details" in response.data or b"Balance" in response.data
    
    with test_app.app_context():
        user = db.session.scalar(sa.select(User).where(User.email == "test@example.com"))
        assert len(user.accounts) == 1
        assert user.accounts[0].balance == 0

def test_deposit(client, test_app):
    register_user(client)
    login_user(client)
    create_account(client)
    
    with test_app.app_context():
        account = db.session.scalar(sa.select(Account))
        account_id = account.id

    response = client.post(f"/{account_id}/deposit", data={
        "amount": "100.50",
        "description": "Initial deposit"
    }, follow_redirects=True)
    assert response.status_code == 200
    
    with test_app.app_context():
        account = db.session.get(Account, account_id)
        assert account.balance == 100.50
        assert len(account.transactions) == 1
        assert account.transactions[0].type == "deposit"

def test_payment_external(client, test_app):
    register_user(client)
    login_user(client)
    create_account(client)
    
    with test_app.app_context():
        account = db.session.scalar(sa.select(Account))
        account_id = account.id
        
    # Deposit first
    client.post(f"/{account_id}/deposit", data={"amount": "200.00", "description": "Dep"}, follow_redirects=True)
    
    # Payment external
    response = client.post(f"/{account_id}/payment", data={
        "amount": "50.00",
        "description": "Rent",
        "payment_type": "external",
        "external_account": "IBAN12345"
    }, follow_redirects=True)
    assert response.status_code == 200
    
    with test_app.app_context():
        account = db.session.get(Account, account_id)
        assert account.balance == 150.00
        # Check transaction
        # The last transaction should be the payment
        t = account.transactions[-1]
        assert t.type == "payment"
        assert t.amount == -50.00

def test_payment_internal(client, test_app):
    # Setup: 2 users, each with 1 account
    # User 1
    register_user(client, email="u1@test.com", password="p1")
    login_user(client, email="u1@test.com", password="p1")
    create_account(client)
    client.get("/logout")
    
    # User 2
    register_user(client, email="u2@test.com", password="p2")
    login_user(client, email="u2@test.com", password="p2")
    create_account(client)
    
    with test_app.app_context():
        u1 = db.session.scalar(sa.select(User).where(User.email == "u1@test.com"))
        u2 = db.session.scalar(sa.select(User).where(User.email == "u2@test.com"))
        acc1 = u1.accounts[0]
        acc2 = u2.accounts[0]
        acc1_id = acc1.id
        acc2_id = acc2.id
    
    # Login as User 1 again to transfer to User 2
    login_user(client, email="u1@test.com", password="p1")
    
    # Deposit to User 1
    client.post(f"/{acc1_id}/deposit", data={"amount": "100.00", "description": "Init"}, follow_redirects=True)
    
    # Transfer from U1 to U2
    response = client.post(f"/{acc1_id}/payment", data={
        "amount": "30.00",
        "description": "Transfer to U2",
        "payment_type": "internal",
        "internal_account": acc2_id
    }, follow_redirects=True)
    assert response.status_code == 200
    
    with test_app.app_context():
        acc1 = db.session.get(Account, acc1_id)
        acc2 = db.session.get(Account, acc2_id)
        assert acc1.balance == 70.00
        assert acc2.balance == 30.00
        
        # Check U2 received "transfer_in"
        t_in = acc2.transactions[0] # assuming created_at order or check list
        # Actually U2 has no other transactions
        assert t_in.type == "transfer_in"
        assert t_in.amount == 30.00

def test_insufficient_funds(client, test_app):
    register_user(client)
    login_user(client)
    create_account(client)
    
    with test_app.app_context():
        account = db.session.scalar(sa.select(Account))
        account_id = account.id
    
    # Balance is 0
    response = client.post(f"/{account_id}/payment", data={
        "amount": "10.00",
        "description": "Fail",
        "payment_type": "external",
        "external_account": "EXT"
    }, follow_redirects=True)
    
    # Should probably flash an error and redirect back to payment or account
    assert b"Insufficient funds" in response.data
    
    with test_app.app_context():
        account = db.session.get(Account, account_id)
        assert account.balance == 0
