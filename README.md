# Gemini Bank

A simple banking web application built with Flask, allowing users to manage accounts and perform transactions.

## Features

- **User Authentication:** Secure registration and login system.
- **Account Management:** Users can create multiple bank accounts.
- **Dashboard:** Overview of all user accounts.
- **Transactions:** Perform deposits and withdrawals on specific accounts.
- **Transaction History:** View detailed history of transactions for each account.

## Project Structure

- `app.py`: Application entry point and configuration.
- `models.py`: Database models (`User`, `Account`, `Transaction`) and database initialization.
- `routes.py`: URL routing and view functions.
- `forms.py`: Form definitions using Flask-WTF.
- `templates/`: HTML templates for the user interface.
- `static/`: Static assets (CSS, images).
- `requirements.txt`: List of Python dependencies.

## Installation and Setup

1.  **Clone the repository** (if applicable) or navigate to the project directory.

2.  **Create a virtual environment** (recommended):
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Run the application:**
    ```bash
    python app.py
    ```
    The application will automatically create the SQLite database (`mybank.db`) if it doesn't exist.

5.  **Access the application:**
    Open your web browser and go to `http://127.0.0.1:5000`.

## Usage

1.  **Register:** Create a new user account via the registration page.
2.  **Login:** Log in with your credentials.
3.  **My Bank:** Go to the "My Bank" section to view your accounts.
4.  **Create Account:** Click on the option to create a new bank account.
5.  **View Account:** Click on an account number to view its details and transaction history.
6.  **New Transaction:** Within an account view, you can record new deposits or withdrawals.

## Technologies Used

- **Python**
- **Flask** (Web Framework)
- **Flask-SQLAlchemy** (ORM)
- **Flask-Login** (Authentication)
- **Flask-WTF** (Forms)
- **SQLite** (Database)
