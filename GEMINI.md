## Core Principles

* **Simplicity:** The application is designed to be simple and intuitive to use.
* **Security:** All passwords are encrypted and user data is stored securely.
* **Reliability:** The application is built on a robust and reliable framework.

## Development

* **Coding Standards** Code should follow the PEP 8 coding standard.
* **Dependency Management** This application uses Python Venv in the `venv` folder.

## Partial Code Overview

Consider the following existing file structure when adding code and before creating new files:

*   **app.py:** The main Flask application file. It initializes the Flask app, database, and login manager.
*   **routes.py:** Defines the application's routes and view functions.
*   **models.py:** Defines the database models
*   **forms.py:** Defines the application's forms using Flask-WTF.
*   **utils.py:** Contains utility functions for the application.
# Gemini Coding Style Guide

This document outlines the coding conventions to be followed by the Gemini agent when interacting with this project.

## Database (SQLAlchemy)

All database models and queries must adhere to the modern **SQLAlchemy 2.0** style. The legacy query API from `Flask-SQLAlchemy` (`Model.query`) is forbidden.

### 1. Model Definition

Models must be defined using `sqlalchemy.orm.Mapped` and `sqlalchemy.orm.mapped_column` with type annotations.

**Bad (Legacy Style):**
```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(40), unique=True, nullable=False)
```

**Good (Modern SQLAlchemy 2.0 Style):**
```python
import sqlalchemy as sa
import sqlalchemy.orm as so

class User(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(40), unique=True)
```

### 2. Database Queries

All queries must be constructed using the `sqlalchemy.select()` function. Do not use the `Model.query` object.

**Bad (Legacy `Model.query`):**
```python
# Get by primary key
user = User.query.get(1)

# Filter and get first
user = User.query.filter_by(email="test@example.com").first()

# Get all
users = User.query.all()
```

**Good (Modern `select()` construct):**
```python
import sqlalchemy as sa

# Get by primary key
user = db.session.get(User, 1)

# Filter and get first
stmt = sa.select(User).where(User.email == "test@example.com")
user = db.session.scalars(stmt).first()

# Get all
stmt = sa.select(User)
users = db.session.scalars(stmt).all()
```
