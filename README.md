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
DATABASE_URL=postgresql+psycopg://<db_user>:<db_password>@<db_host>:5432/customer
APP_SECRET_KEY=replace-with-a-real-secret
```

## Initialize Database

Run the schema bootstrap and default metadata seed:

```bash
python scripts/init_db.py
```

This creates the tables and seeds the default tag groups/options from the confirmed business requirements.
If the database already exists, startup also backfills the `sales_users.is_test_user` column automatically.

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

Or create one through the repository layer:

```bash
python -c "from sqlalchemy import create_engine; from customer_management.db import make_session_factory; from customer_management.repositories.admin_users import create_admin_user; engine=create_engine('postgresql+psycopg://<db_user>:<db_password>@<db_host>:5432/customer'); session_factory=make_session_factory(engine); session=session_factory(); create_admin_user(session, username='admin', password='change-me', display_name='Admin'); session.close()"
```

## Run the App

```bash
streamlit run app.py
```

Sales users always see production data only.
Admins can switch between `生产数据` and `测试数据` inside the admin workspace.
Admins also have a `测试入口` page that opens the sales workspace with a test account, without exposing test accounts in the normal sales login.

## Admin Metadata Workflow

Admin customer metadata now lives under `客户资料配置`.

- The page begins with a `当前配置情况` summary card.
- Active and inactive classification items remain visible there.
- Changes made in that area flow through to the sales record form.

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
