# 🏦 Gemini Bank

A secure, intuitive, and lightweight local banking web application built with **Python**, **Flask**, and **SQLite**. Gemini Bank allows users to register secure accounts, manage their balances, and perform standard banking transactions like deposits and transfers in a clean, responsive environment.

---

## 🌟 Core Principles

As outlined in the core guidelines of the application:
*   **Simplicity:** A clean, minimal, and intuitive interface designed for hassle-free navigation and ease of use.
*   **Security:** High security standards with robust password hashing using industry-standard libraries (`werkzeug.security`) and protected user sessions.
*   **Reliability:** Built on Flask and SQLAlchemy to ensure smooth, robust database transactions and state persistence.

---

## 🛠️ Features

*   **User Registration & Authentication**: 
    *   Sign up with secure fields (First Name, Last Name, Email, Password).
    *   Passwords are securely encrypted before storing.
    *   Persistent user sessions with a "Remember Me" option during login.
*   **Account Management**:
    *   Instantaneous bank account provisioning upon registering.
    *   View all your associated bank accounts from a centralized dashboard.
    *   Real-time balance computation in Euros (EUR).
*   **Split Transactions**:
    *   **Deposit**: Easily deposit funds directly to your own account.
    *   **Payment**: Send money to either an internal user's bank account or an external destination.
    *   **Dynamic Dropdown Selection**: For internal payments, a dynamic dropdown list populated with account numbers and their owner's full names is presented to ensure accuracy.
    *   **Custom Audit Descriptions**: Internal transfer transactions automatically register symmetrical records in both the sender's ledger and the recipient's ledger, using custom audit descriptions like `"payment from [sender owner] with description: [original description]"`.
*   **Diagnostic Utilities**:
    *   Includes developer-friendly CLI commands in `utils.py` to inspect existing users and account statuses instantly.

---

## 💻 Tech Stack

*   **Backend**: [Flask](https://flask.palletsprojects.com/) (Python micro-framework)
*   **Database ORM**: [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
*   **Database**: SQLite (Local, lightweight database file: `mybank.db`)
*   **Authentication**: [Flask-Login](https://flask-login.readthedocs.io/)
*   **Forms & Validation**: [Flask-WTF](https://flask-wtf.readthedocs.io/) & [WTForms](https://wtforms.readthedocs.io/) (including email format validation)
*   **Security**: [Werkzeug](https://werkzeug.palletsprojects.com/) (PBKDF2 password hashing)
*   **Frontend**: [Bootstrap 5](https://getbootstrap.com/), Bootstrap Icons, Semantic HTML5, Jinja2 Templating, Vanilla CSS3 & JS (`static/style.css`)

---

## 📂 Codebase Structure

The application's design separates concerns between models, routes, forms, templates, and static assets:

```text
gemini-bank/
├── app.py                # Main application entry point; initializes Flask, SQLAlchemy & LoginManager
├── models.py             # Defines database schema (User, Account, Transaction) & auto-creates SQLite tables
├── routes.py             # Contains all application routes (login, register, mybank, deposit, payment, etc.)
├── forms.py              # Declares Flask-WTF validation forms (RegisterForm, LoginForm, DepositForm, PaymentForm)
├── utils.py              # Helper utility to list registered users and accounts in the console
├── requirements.txt      # Python dependencies file
├── GEMINI.md             # Core architecture and development rules
├── static/
│   ├── style.css         # Styling for layout, tables, forms, and custom buttons
│   └── img/              # Folder for visual assets
└── templates/            # Jinja2 HTML templates
    ├── base.html         # Base layout containing the navigation header and alert flash messages
    ├── index.html        # Landing page welcoming visitors
    ├── register.html     # User registration form
    ├── login.html        # Secure user login form
    ├── mybank.html       # Client dashboard showing account list / creation triggers
    ├── account.html      # Account details showing balance and transaction ledger with Deposit & Payment buttons
    ├── deposit.html      # Form to deposit funds
    └── payment.html      # Form to send a payment (with automatic toggle between internal/external types)
```

---

## 🚀 Local Installation & Setup

Follow these simple steps to run Gemini Bank locally on your machine:

### Prerequisites
Make sure you have **Python 3.8+** installed on your system.

### 1. Clone or Navigate to the Directory
Open your terminal and navigate to the application root directory:
```bash
cd /Users/galloro/gemini-bank
```

### 2. Set Up a Virtual Environment
It is highly recommended to isolate your dependencies using a virtual environment (`venv` folder):

*   **macOS / Linux**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
*   **Windows**:
    ```cmd
    python -m venv venv
    venv\Scripts\activate
    ```

### 3. Install Dependencies
Install all the required Python packages specified in `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 4. Run the Application
Start the local development server:
```bash
python app.py
```

The application will initialize the database schema in `instance/mybank.db` or `mybank.db` automatically and run on:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)** (or `localhost:5000`)

---

## 🕹️ How to Interact with the App

Once the development server is running, follow this walk-through to test the functionalities:

1.  **Register a New User**: 
    *   Navigate to the home page and click on **Register** in the top right corner.
    *   Fill in your First Name, Last Name, Email, and Password. Click **Register user**.
2.  **Log In**:
    *   Click **Login**, enter your credentials, and check "Remember Me" if desired.
    *   Upon a successful login, you will be redirected to the secure **My Bank** dashboard (`/mybank`).
3.  **Create Your Bank Account**:
    *   If you don't have an account yet, you will be prompted with a **Create Account** button.
    *   Clicking it assigns a unique 6-digit account number (starting with `160001`) with a starting balance of `0.00 EUR`.
4.  **Perform Deposits**:
    *   Click on your account link on the dashboard to access its details and ledger page (`/accounts/<id>`).
    *   Click the **Deposit Money** button.
    *   Enter an amount (minimum `0.01`) and a description, then click **Deposit**. The balance updates instantly.
5.  **Make Payments**:
    *   On the account details page, click the **Make a Payment** button.
    *   Select your recipient type:
        *   **Internal User**: This displays a dynamic dropdown listing all other bank accounts on the system, showing their account number and owner names. Select the recipient, specify the amount and description, and click **Send Payment**. This transfers funds, creating a debit transaction on your account and a credit transaction on the destination account with a structured note: `payment from [Sender Name] with description: [Original Note]`.
        *   **External User**: Hides the dropdown and shows an external account identifier/reference field. Type the reference, the amount, and the description, and click **Send Payment**.
6.  **View Transaction Ledger**:
    *   The balance recalculates and the table displays all transactions chronologically with details.
7.  **Log Out**:
    *   Click **Logout** in the top-right corner to securely clear your session.

---

## 🔧 Developer Quick-Look (CLI Utility)

To inspect database records directly via the console without browsing the UI, you can run the provided utility script:
```bash
python utils.py
```
This prints a clean list of all registered users and active bank accounts in your console.
