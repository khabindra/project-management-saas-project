# Django SaaS Backend API

A production-ready SaaS backend API built with Python, Django, and Django REST Framework. Follow the steps below to set up and run this project locally for development.

## 🚀 Prerequisites

Ensure you have the following installed on your local machine:
* **Python** (version 3.10 or higher recommended)
* **Git**

---

## 🛠️ Local Installation Steps

### 1. Clone the Repository
Clone the project to your local machine and navigate into the project directory:
```bash
git clone <YOUR_REPOSITORY_URL>
cd django-saas
```

### 2. Create a Virtual Environment
Isolate the project dependencies by creating a Python virtual environment:
```bash
# Windows
python -m venv venv

# macOS / Linux
python3 -m venv venv
```

### 3. Activate the Virtual Environment
Activate the environment before installing packages:
```bash
# Windows (PowerShell)
.\venv\Scripts\activate

# Windows (Command Prompt)
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```
*(You will see `(venv)` appear at the beginning of your terminal line).*

### 4. Install Local Development Dependencies
Install the basic packages alongside local development-specific tools:
```bash
pip install --upgrade pip
pip install -r requirements/dev.txt
```

### 5. Set Up Environment Variables
Your root folder contains a `.env` file. If cloning fresh, you should create it using your template:
1. Create a new file named `.env` in the root `django-saas` directory.
2. Ensure it contains your local variables (e.g., `DEBUG=True`, `SECRET_KEY`, and database settings).

### 6. Run Database Migrations
Initialize or update your local SQLite database configuration (`db.sqlite3`):
```bash
python manage.py migrate
```

### 7. Create a Superuser (Optional)
Create an admin account to access the Django Admin dashboard:
```bash
python manage.py createsuperuser
```
Follow the terminal prompts to set up your username, email, and password.

### 8. Start the Development Server
Launch the local Django development server:
```bash
python manage.py runserver
```

Open your browser and navigate to:
* **API Root:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Admin Dashboard:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 📂 Project Structure Overview

* **`config/`**: Main project configurations, settings, and root URL routing.
* **`apps/`**: Custom Django applications containing the core business logic.
* **`common/`**: Shared helper functions, mixins, or reusable backend utilities.
* **`requirements/`**: Environment-splitted dependency files (`base.txt`, `dev.txt`, `prod.txt`).
* **`templates/`**: HTML views or email templates.

---

## 🧪 Running Tests

To run the automated test suite, execute:
```bash
python manage.py test
```
