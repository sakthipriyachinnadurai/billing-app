# Billing System

A full-stack billing application built with **Django REST Framework** and **React**.

## Features

- Product billing
- Cash drawer denominations
- Automatic change calculation
- Purchase history
- Invoice email with Celery
- PostgreSQL database

---

## Tech Stack

- Python 3.x
- Django
- Django REST Framework
- React
- PostgreSQL
- Redis
- Celery

---

## Backend Setup

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Create `.env`

Create a `.env` file in the project root (same level as `manage.py`).

Example:

```env
SECRET_KEY=your-secret-key
DEBUG=True

DB_NAME=your_db
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

### Run Migrations

```bash
python manage.py migrate
```

### Seed Products

```bash
python manage.py seed
```

### Start Backend

```bash
python manage.py runserver
```

---

## Celery Setup

Run in a separate terminal:

```bash
celery -A backend worker -l info
```

### Windows Only

```bash
celery -A backend worker -l info --pool=solo
```

---

## Email Setup

### Gmail SMTP Example

```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=yourmail@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
DEFAULT_FROM_EMAIL=yourmail@gmail.com
```

Restart Django and Celery after updating `.env`.

---

## Frontend Setup

```bash
cd frontend
npm install
npm start
```

---

## API Endpoints

| Method | Endpoint                   |
| ------ | -------------------------- |
| POST   | `/generate-bill/`          |
| GET    | `/bills/customer/<email>/` |
| GET    | `/bills/<invoice_id>/`     |

---

## Notes

- `amount_paid` must cover the bill total
- Drawer denominations are used for change
- Purchase history is saved in database
- Emails are sent asynchronously using Celery

---

## Git

`.env`, logs, cache files, and virtual environments are ignored using `.gitignore`.

Never commit secrets.

---

## Run Summary

```bash
python manage.py runserver
celery -A backend worker -l info
npm start
```

---
