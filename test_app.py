import unittest
from app import app, db
from models import User, Account, Transaction
import sqlalchemy as sa

class BankAppTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def register(self, firstname, lastname, email, password):
        return self.app.post('/register', data=dict(
            firstname=firstname,
            lastname=lastname,
            email=email,
            password1=password,
            password2=password
        ), follow_redirects=True)

    def login(self, email, password):
        return self.app.post('/login', data=dict(
            email=email,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def test_user_registration(self):
        response = self.register('John', 'Doe', 'john@example.com', 'password123')
        self.assertEqual(response.status_code, 200)
        user = db.session.scalar(sa.select(User).where(User.email == 'john@example.com'))
        self.assertIsNotNone(user)
        self.assertEqual(user.firstname, 'John')

    def test_user_login(self):
        self.register('Jane', 'Doe', 'jane@example.com', 'password123')
        response = self.login('jane@example.com', 'password123')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Logout', response.data)

    def test_create_account(self):
        self.register('Alice', 'Smith', 'alice@example.com', 'password123')
        self.login('alice@example.com', 'password123')
        response = self.app.post('/mybank', data=dict(
            submit="Create Account"
        ), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        account = db.session.scalar(sa.select(Account).join(User).where(User.email == 'alice@example.com'))
        self.assertIsNotNone(account)
        self.assertEqual(account.balance, 0)

    def test_deposit(self):
        self.register('Bob', 'Brown', 'bob@example.com', 'password123')
        self.login('bob@example.com', 'password123')
        self.app.post('/mybank', data=dict(submit="Create Account"), follow_redirects=True)
        account = db.session.scalar(sa.select(Account).join(User).where(User.email == 'bob@example.com'))
        
        response = self.app.post(f'/{account.id}/deposit', data=dict(
            amount=100.00,
            description="Initial deposit"
        ), follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        # Refresh account from db
        db.session.refresh(account)
        self.assertEqual(account.balance, 100.00)
        
        transaction = db.session.scalar(sa.select(Transaction).where(Transaction.account_id == account.id))
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.amount, 100.00)
        self.assertEqual(transaction.type, "deposit")

    def test_internal_payment(self):
        # Create User 1 (Sender)
        self.register('Sender', 'One', 'sender@example.com', 'password123')
        self.login('sender@example.com', 'password123')
        self.app.post('/mybank', data=dict(submit="Create Account"), follow_redirects=True)
        account1 = db.session.scalar(sa.select(Account).join(User).where(User.email == 'sender@example.com'))
        
        # Deposit money to Sender
        self.app.post(f'/{account1.id}/deposit', data=dict(amount=500.00, description="Dep"), follow_redirects=True)
        self.logout()

        # Create User 2 (Recipient)
        self.register('Recipient', 'Two', 'recipient@example.com', 'password123')
        self.login('recipient@example.com', 'password123')
        self.app.post('/mybank', data=dict(submit="Create Account"), follow_redirects=True)
        account2 = db.session.scalar(sa.select(Account).join(User).where(User.email == 'recipient@example.com'))
        self.logout()

        # Log back in as Sender to make payment
        self.login('sender@example.com', 'password123')
        response = self.app.post(f'/{account1.id}/payment', data=dict(
            payment_type='internal',
            internal_account=account2.id,
            amount=100.00,
            description="Payment for dinner"
        ), follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        db.session.refresh(account1)
        db.session.refresh(account2)
        
        self.assertEqual(account1.balance, 400.00) # 500 - 100
        self.assertEqual(account2.balance, 100.00) # 0 + 100

    def test_external_payment(self):
        self.register('Ext', 'User', 'ext@example.com', 'password123')
        self.login('ext@example.com', 'password123')
        self.app.post('/mybank', data=dict(submit="Create Account"), follow_redirects=True)
        account = db.session.scalar(sa.select(Account).join(User).where(User.email == 'ext@example.com'))
        
        self.app.post(f'/{account.id}/deposit', data=dict(amount=200.00, description="Dep"), follow_redirects=True)
        
        response = self.app.post(f'/{account.id}/payment', data=dict(
            payment_type='external',
            external_account='EXT123456',
            amount=50.00,
            description="Utility bill"
        ), follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        db.session.refresh(account)
        self.assertEqual(account.balance, 150.00)

if __name__ == '__main__':
    unittest.main()
