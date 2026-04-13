# Customer Management

Streamlit-based customer information management system backed by PostgreSQL.

## Requirements

- Python 3.9+
- PostgreSQL

## Setup

1. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

2. Create a local environment file:

```bash
copy .env.example .env
```

3. Update `.env` with your real settings:

```env
DATABASE_URL=postgresql://streamlit:streamlit@117.72.54.192:5432/customer
APP_SECRET_KEY=replace-with-a-real-secret
```

## Initialize Database

Run the schema bootstrap and default metadata seed:

```bash
python scripts/init_db.py
```

This creates the tables and seeds the default tag groups/options from the confirmed business requirements.

## Create the First Admin User

The product does not provide self-registration. Create the first admin user directly in the database.

Use Python to generate a password hash:

```bash
python -c "from customer_management.security import hash_password; print(hash_password('your-admin-password'))"
```

Then insert a row into `admin_users` with:

- `username`
- `password_hash`
- `display_name`
- `is_active = true`

## Run the App

```bash
streamlit run app.py
```

## Run Tests

```bash
python -m pytest -v
```

## Current Scope

- Sales login with name selection + password
- Sales create, edit, delete, and list their own records
- Admin login with username + password
- Admin management of sales users, admin users, tags, and custom fields
- Admin dashboard metrics and record overview

## Current Limitations

- No attachment upload
- No password recovery
- No soft delete
- No audit log
- First admin must be created directly in the database
