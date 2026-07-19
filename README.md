# 🏦 Gemini Bank

A simple, secure, and reliable web-based banking application built using Python, Flask, and SQLite. Gemini Bank allows users to register, securely log in, open multiple bank accounts, and perform real-time transactions (deposits and transfers) while maintaining a complete transaction history.

---

## 🚀 Key Features

- **Secure User Authentication**:
  - Robust sign-up and login mechanism.
  - Password encryption using industry-standard hashing (`werkzeug.security`).
  - Session handling and protected routes with `Flask-Login`.

- **Flexible Account Management**:
  - Open multiple bank accounts under a single user profile.
  - Auto-generated 6-digit unique account numbers starting from `160001`.
  - Real-time balance updates calculated instantly upon transactions.

- **Dynamic Transaction Processing**:
  - **Deposits**: Instantly add funds to any of your accounts.
  - **Transfers**: Deduct funds from your account with detailed descriptions.
  - Fully recorded transaction histories including timestamp, amount, type, and description.

- **Clean and Intuitive Interface**:
  - Streamlined UI built with semantic HTML and CSS.
  - Informative feedback messages using Flask's flash messaging system.

---

## 📁 Project Structure

Here is an overview of the application's file structure and the role of each component:

```text
gemini-bank/
├── app.py              # Main entry point. Initializes Flask, database connection, and login manager.
├── models.py           # Defines Database Schemas (User, Account, Transaction) using SQLAlchemy.
├── routes.py           # Implements the URL endpoints and application controller logic.
├── forms.py            # Form validation logic using WTForms & Flask-WTF (Register, Login, Transactions).
├── utils.py            # Diagnostic utility scripts for querying current users and accounts in the CLI.
├── requirements.txt    # Declares all Python package dependencies.
├── GEMINI.md           # Documentation highlighting core project principles and design standards.
├── static/             # Client-side static assets.
│   ├── style.css       # Core stylesheet managing layouts, typography, tables, and buttons.
│   └── img/            # Repository for visual media (logos, banners).
│       ├── logo.png
│       └── hero.png
└── templates/          # Jinja2 HTML templates.
    ├── base.html       # The root template with navbar, profile controls, and flash messaging structure.
    ├── index.html      # Landing page / home view.
    ├── login.html      # User login form.
    ├── register.html   # User registration form.
    ├── mybank.html     # User dashboard showing accounts overview and account creation form.
    ├── account.html    # Detailed account view containing balance and list of transactions.
    └── transaction.html# Form to make deposits or transfer adjustments.
```

---

## 🛠️ Technology Stack

- **Backend**: Python, [Flask](https://flask.palletsprojects.com/)
- **Database / ORM**: SQLite, [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
- **Security & Sessions**: [Flask-Login](https://flask-login.readthedocs.io/), [Werkzeug Security](https://werkzeug.palletsprojects.com/)
- **Forms & Validation**: [Flask-WTF](https://flask-wtf.readthedocs.io/), [WTForms](https://wtforms.readthedocs.io/)
- **Frontend**: Jinja2, HTML5, CSS3 (Vanilla CSS)

---

## 💻 Local Setup & Installation

Follow these steps to set up and run Gemini Bank on your local computer:

### 1. Prerequisites
Ensure you have **Python 3.8+** installed on your system. You can check your Python version by running:
```bash
python3 --version
```

### 2. Clone the Repository
Navigate to your workspace directory and open your terminal.

### 3. Set Up Virtual Environment
Create and activate a virtual environment (`.venv` or `venv`) to isolate dependencies:
```bash
# Create virtual environment
python3 -m venv venv

# Activate on macOS / Linux
source venv/bin/activate

# Activate on Windows
venv\Scripts\activate
```

### 4. Install Dependencies
Install all required libraries specified in the `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 5. Run the Application
Start the Flask development server:
```bash
python app.py
```
By default, the server will launch in **Debug Mode** and will be accessible at:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

*(Note: On first run, the SQLite database `instance/mybank.db` will be initialized automatically in the background).*

---

## 🕹️ Interactive Walkthrough

Here's how to interact with the application once it is running locally:

### Phase 1: User Onboarding & Access
1. Open your browser and navigate to `http://127.0.0.1:5000`.
2. Click on **Register** to create a new profile (First Name, Last Name, Email, and Password).
3. Once registered, click **Login** and enter your credentials.

### Phase 2: Manage Your Accounts
1. Upon logging in, you will be redirected to the **My Bank** dashboard (`/mybank`).
2. If you are a new user, your account list will be empty. Click **Create Account** to open your first bank account.
3. This creates an account with a unique number (e.g., `160001`) and a starting balance of `$0.00`.

### Phase 3: Making Transactions
1. From the dashboard, click on any of your active accounts to go to its details view.
2. Inside the account view, click the **Make Transaction** button.
3. Fill out the transaction form:
   - **Type**: Select **Deposit** to add money, or **Transfer** to withdraw/move money.
   - **Amount**: Enter the transaction value (positive decimal).
   - **Description**: Enter a brief summary of the purpose (e.g., *Salary*, *Rent*, *Groceries*).
4. Click **Make Transaction** to confirm. You will see a flash message confirming completion and will be redirected back to the account details page showing your updated balance and updated transaction history table.
