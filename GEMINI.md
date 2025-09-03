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

## User Interface (UI)

The UI is designed to be modern, accessible, and user-friendly, adhering to the following principles:

*   **Framework:**
    *   Built on the latest version of the **Bootstrap** library for a responsive, mobile-first design.
    *   Ensures a consistent and clean layout across all devices, from desktops to mobile phones.
*   **Theme & Aesthetics:**
    *   **Dark Mode:** The application uses a dark theme by default, utilizing a palette of dark grays and off-blacks to reduce eye strain and provide a contemporary look.
    *   **Accent Colors:** A limited and carefully selected palette of accent colors will be used for interactive elements like buttons and links to guide the user's attention.
*   **Accessibility:**
    *   **High Contrast:** All text, icons, and UI elements are designed with sufficient color contrast against the background to meet WCAG 2.1 AA standards, ensuring readability for users with visual impairments.
    *   **Clear Focus States:** Interactive elements will have clear and visible focus indicators, making keyboard navigation straightforward.
    *   **Semantic HTML:** The application will use semantic HTML5 tags and ARIA (Accessible Rich Internet Applications) attributes where necessary to provide context to screen readers.
