# Gemini Bank

Gemini Bank is a simple Flask-based web application that allows users to create accounts, manage their funds, and track transactions. It demonstrates a basic implementation of a banking system using Python and SQLite.

## Features

- **User Authentication**: Secure registration and login functionality.
- **Account Management**:
  - Users can create multiple bank accounts.
  - View a list of all owned accounts.
- **Transactions**:
  - Perform deposits and withdrawals on specific accounts.
  - View transaction history for each account.
- **Responsive Design**: Basic styling for a clean user interface.

## Tech Stack

- **Backend**: Python, Flask
- **Database**: SQLite, SQLAlchemy
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF

## Project Structure

```
gemini-bank/
├── app.py              # Application entry point and configuration
├── routes.py           # Route definitions and view logic
├── models.py           # Database models (User, Account, Transaction)
├── forms.py            # WTForms definitions
├── utils.py            # Utility functions
├── requirements.txt    # Project dependencies
├── templates/          # HTML templates
└── static/             # Static assets (CSS, images)
```

## Installation & Setup

### Prerequisites

- Python 3.x
- pip (Python package manager)

### Steps

1.  **Clone the repository** (if applicable) or navigate to the project directory:
    ```bash
    cd gemini-bank
    ```

2.  **Create a virtual environment** (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize the Database**:
    The application is configured to automatically create the database tables (`mybank.db`) when it starts if they don't exist.

## Running the Application

1.  Start the Flask development server:
    ```bash
    python app.py
    ```

2.  Open your web browser and navigate to:
    ```
    http://127.0.0.1:5000/
    ```

## Usage

1.  **Register**: Create a new user account via the registration page.
2.  **Login**: specific user credentials to access the "My Bank" dashboard.
3.  **Create Account**: On the dashboard, use the form to open a new bank account.
4.  **Manage Account**: Click on an account ID to view details.
5.  **Transactions**: Inside an account view, use the "New Transaction" button to deposit or withdraw funds.

## License

This project is for educational purposes.
