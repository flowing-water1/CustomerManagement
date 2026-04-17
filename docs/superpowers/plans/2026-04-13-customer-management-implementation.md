# Customer Management Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working Streamlit + PostgreSQL customer management app with admin-managed dynamic tags/custom fields, sales self-service record CRUD, and admin dashboard/reporting.

**Architecture:** The app uses Streamlit as the UI shell and a small Python package for config, database access, security, repositories, and page rendering. PostgreSQL is the production database, while tests use isolated SQLite databases and Streamlit `AppTest` to keep feedback fast and deterministic.

**Tech Stack:** Python 3.11+, Streamlit, SQLAlchemy 2.x, psycopg, pytest, streamlit.testing.v1, passlib[bcrypt], python-dotenv, pandas

---

## File Structure

### Application Entry

- Create: `app.py`
  - Streamlit entrypoint, session bootstrap, top-level page routing
- Create: `README.md`
  - Local setup, database bootstrap, and run/test instructions
- Create: `.streamlit/config.toml`
  - Streamlit UI defaults for local development
- Create: `requirements.txt`
  - Runtime and test dependencies
- Create: `.env.example`
  - Document required database and app settings

### Package Layout

- Create: `customer_management/__init__.py`
- Create: `customer_management/config.py`
  - Environment loading and typed app settings
- Create: `customer_management/db.py`
  - SQLAlchemy engine, session factory, and testable helpers
- Create: `customer_management/models.py`
  - ORM models for admins, sales users, records, tags, and custom fields
- Create: `customer_management/security.py`
  - Password hashing and verification helpers
- Create: `customer_management/auth.py`
  - Session helpers and login/logout flows for admin and sales
- Create: `customer_management/bootstrap.py`
  - Schema creation and initial tag seed helpers

### Repositories and Services

- Create: `customer_management/repositories/admin_users.py`
  - Admin CRUD and login lookup
- Create: `customer_management/repositories/sales_users.py`
  - Sales CRUD, password updates, and lookup by selected name
- Create: `customer_management/repositories/records.py`
  - Record CRUD, ownership filtering, tag/value persistence
- Create: `customer_management/repositories/metadata.py`
  - Tag group/option and custom field management
- Create: `customer_management/services/forms.py`
  - Build dynamic input descriptors from active metadata
- Create: `customer_management/services/dashboard.py`
  - Aggregate queries for totals, trends, rankings, and cross-statistics

### UI Modules

- Create: `customer_management/ui/shared.py`
  - Shared layout, flash messages, auth guards
- Create: `customer_management/ui/sales.py`
  - Sales login, password change, record list, record editor
- Create: `customer_management/ui/admin.py`
  - Admin login, dashboard, records overview, metadata management

### Scripts

- Create: `scripts/init_db.py`
  - Initialize schema and seed default tag metadata

### Tests

- Create: `tests/conftest.py`
  - Shared SQLite engine/session fixtures and sample session state helpers
- Create: `tests/test_config.py`
- Create: `tests/test_security.py`
- Create: `tests/test_bootstrap.py`
- Create: `tests/repositories/test_sales_users.py`
- Create: `tests/repositories/test_records.py`
- Create: `tests/services/test_forms.py`
- Create: `tests/services/test_dashboard.py`
- Create: `tests/ui/test_sales_app.py`
- Create: `tests/ui/test_admin_app.py`

## Task 1: Bootstrap Project Skeleton

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.streamlit/config.toml`
- Create: `customer_management/__init__.py`
- Create: `tests/test_config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing config test**

```python
from customer_management.config import Settings


def test_settings_reads_required_database_values(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://streamlit:streamlit@localhost:5432/customer")

    settings = Settings.from_env()

    assert settings.database_url.endswith("/customer")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError` or missing `Settings`

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass
import os


@dataclass(slots=True)
class Settings:
    database_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            database_url=os.environ["DATABASE_URL"],
        )
```

Also create:

- `requirements.txt` with:
  - `streamlit>=1.40`
  - `sqlalchemy>=2.0`
  - `psycopg[binary]>=3.1`
  - `passlib[bcrypt]>=1.7`
  - `python-dotenv>=1.0`
  - `pandas>=2.0`
  - `pytest>=8.0`
- `.env.example` with placeholder `DATABASE_URL`
- `.streamlit/config.toml` with a basic wide layout and development theme

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .env.example .streamlit/config.toml customer_management/__init__.py customer_management/config.py tests/test_config.py
git commit -m "chore: bootstrap project configuration"
```

## Task 2: Add Password Security Helpers

**Files:**
- Create: `customer_management/security.py`
- Create: `tests/test_security.py`
- Test: `tests/test_security.py`

- [ ] **Step 1: Write the failing security test**

```python
from customer_management.security import hash_password, verify_password


def test_password_hash_round_trip():
    password_hash = hash_password("streamlit123")

    assert password_hash != "streamlit123"
    assert verify_password("streamlit123", password_hash) is True
    assert verify_password("wrong-pass", password_hash) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_security.py -v`
Expected: FAIL because the security helpers do not exist

- [ ] **Step 3: Write minimal implementation**

```python
from passlib.context import CryptContext

_PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _PWD_CONTEXT.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _PWD_CONTEXT.verify(password, password_hash)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_security.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add customer_management/security.py tests/test_security.py requirements.txt
git commit -m "feat: add password hashing helpers"
```

## Task 3: Add Database Core and ORM Models

**Files:**
- Create: `customer_management/db.py`
- Create: `customer_management/models.py`
- Create: `tests/conftest.py`
- Create: `tests/test_bootstrap.py`
- Test: `tests/test_bootstrap.py`

- [ ] **Step 1: Write the failing schema bootstrap test**

```python
from sqlalchemy import inspect

from customer_management.bootstrap import create_schema


def test_create_schema_creates_core_tables(db_engine):
    create_schema(db_engine)

    tables = set(inspect(db_engine).get_table_names())

    assert {"admin_users", "sales_users", "customer_records", "tag_groups", "tag_options", "record_tags", "custom_fields", "custom_field_options", "record_field_values"} <= tables
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_bootstrap.py -v`
Expected: FAIL because `create_schema` and models are missing

- [ ] **Step 3: Write minimal implementation**

Create:

- `customer_management/db.py` with `create_engine`, `sessionmaker`, and `Base = DeclarativeBase`
- `customer_management/models.py` with the v1 ORM models
- `customer_management/bootstrap.py` with:

```python
from customer_management.db import Base


def create_schema(engine) -> None:
    Base.metadata.create_all(engine)
```

- `tests/conftest.py` with a temporary SQLite `db_engine` fixture and `db_session` fixture

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_bootstrap.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add customer_management/db.py customer_management/models.py customer_management/bootstrap.py tests/conftest.py tests/test_bootstrap.py
git commit -m "feat: add database models and bootstrap"
```

## Task 4: Seed Default Metadata from the Confirmed Tag Set

**Files:**
- Modify: `customer_management/bootstrap.py`
- Modify: `customer_management/models.py`
- Create: `scripts/init_db.py`
- Test: `tests/test_bootstrap.py`

- [ ] **Step 1: Write the failing seed test**

```python
from sqlalchemy import select

from customer_management.bootstrap import create_schema, seed_default_metadata
from customer_management.models import TagGroup, TagOption


def test_seed_default_metadata_inserts_confirmed_tag_options(db_engine, db_session):
    create_schema(db_engine)
    seed_default_metadata(db_session)

    groups = {group.code for group in db_session.scalars(select(TagGroup)).all()}
    options = {option.value for option in db_session.scalars(select(TagOption)).all()}

    assert {"customer_level", "customer_type", "brand", "oil_type", "authorized_dealer", "other"} <= groups
    assert {"general", "important", "converted", "not_converted", "shell", "mobil", "greatwall", "kunlun"} <= options
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_bootstrap.py::test_seed_default_metadata_inserts_confirmed_tag_options -v`
Expected: FAIL because `seed_default_metadata` does not exist

- [ ] **Step 3: Write minimal implementation**

Add to `customer_management/bootstrap.py`:

- a `seed_default_metadata(session)` helper
- idempotent inserts for the confirmed tag groups and options based on `img.png` and `img_1.png`

Create `scripts/init_db.py` to:

- load `.env`
- create the production engine
- run `create_schema`
- run `seed_default_metadata`

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_bootstrap.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add customer_management/bootstrap.py customer_management/models.py scripts/init_db.py tests/test_bootstrap.py
git commit -m "feat: seed default metadata"
```

## Task 5: Implement Sales User Repository and Password Change Flow

**Files:**
- Create: `customer_management/repositories/sales_users.py`
- Create: `customer_management/auth.py`
- Create: `tests/repositories/test_sales_users.py`
- Test: `tests/repositories/test_sales_users.py`

- [ ] **Step 1: Write the failing sales auth test**

```python
from customer_management.repositories.sales_users import create_sales_user, authenticate_sales_user, change_sales_password


def test_sales_user_auth_and_password_change(db_session):
    sales_user = create_sales_user(
        db_session,
        name="Alice",
        password="temp-pass",
        must_change_password=True,
    )

    authenticated = authenticate_sales_user(db_session, "Alice", "temp-pass")

    assert authenticated.id == sales_user.id
    assert authenticated.must_change_password is True

    change_sales_password(db_session, sales_user.id, "temp-pass", "next-pass")

    reauthenticated = authenticate_sales_user(db_session, "Alice", "next-pass")
    assert reauthenticated.must_change_password is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/repositories/test_sales_users.py -v`
Expected: FAIL because the repository functions do not exist

- [ ] **Step 3: Write minimal implementation**

Implement in `customer_management/repositories/sales_users.py`:

- `create_sales_user`
- `authenticate_sales_user`
- `change_sales_password`
- active-user checks

Add session helper utilities to `customer_management/auth.py` for storing:

- actor type (`admin` or `sales`)
- actor id
- actor display name

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/repositories/test_sales_users.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add customer_management/repositories/sales_users.py customer_management/auth.py tests/repositories/test_sales_users.py
git commit -m "feat: add sales authentication flow"
```

## Task 6: Implement Dynamic Metadata Reader and Form Builder

**Files:**
- Create: `customer_management/repositories/metadata.py`
- Create: `customer_management/services/forms.py`
- Create: `tests/services/test_forms.py`
- Test: `tests/services/test_forms.py`

- [ ] **Step 1: Write the failing dynamic form test**

```python
from customer_management.services.forms import build_record_form_schema


def test_build_record_form_schema_returns_active_tags_and_fields(db_session, seeded_metadata):
    schema = build_record_form_schema(db_session)

    assert schema.tag_groups
    assert any(group.code == "customer_level" for group in schema.tag_groups)
    assert schema.custom_fields == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/services/test_forms.py -v`
Expected: FAIL because the form builder does not exist

- [ ] **Step 3: Write minimal implementation**

Implement:

- metadata repository readers for active groups/options/fields
- a `build_record_form_schema` service returning typed descriptors
- a reusable `seeded_metadata` fixture in `tests/conftest.py`

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/services/test_forms.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add customer_management/repositories/metadata.py customer_management/services/forms.py tests/services/test_forms.py tests/conftest.py
git commit -m "feat: add dynamic metadata form builder"
```

## Task 7: Implement Record Repository with Ownership and Hard Delete

**Files:**
- Create: `customer_management/repositories/records.py`
- Create: `tests/repositories/test_records.py`
- Test: `tests/repositories/test_records.py`

- [ ] **Step 1: Write the failing record CRUD test**

```python
from customer_management.repositories.records import create_record, list_records_for_sales_user, update_record, delete_record


def test_sales_user_crud_only_returns_owned_records(db_session, sales_user, seeded_metadata):
    created = create_record(
        db_session,
        sales_user_id=sales_user.id,
        customer_name="ACME",
        contact_name="Bob",
        phone="13800000000",
        remark="first",
        selected_option_ids=[],
        custom_field_values={},
    )

    records = list_records_for_sales_user(db_session, sales_user.id, query="ACME")
    assert [record.id for record in records] == [created.id]

    update_record(
        db_session,
        record_id=created.id,
        sales_user_id=sales_user.id,
        customer_name="ACME Updated",
        contact_name="Bob",
        phone="13800000000",
        remark="changed",
        selected_option_ids=[],
        custom_field_values={},
    )

    delete_record(db_session, record_id=created.id, sales_user_id=sales_user.id)
    assert list_records_for_sales_user(db_session, sales_user.id) == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/repositories/test_records.py -v`
Expected: FAIL because record repository methods are missing

- [ ] **Step 3: Write minimal implementation**

Implement:

- create, list, get-by-id, update, and delete for owned records
- tag link persistence in `record_tags`
- custom field persistence in `record_field_values`
- ownership checks before update/delete

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/repositories/test_records.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add customer_management/repositories/records.py tests/repositories/test_records.py tests/conftest.py
git commit -m "feat: add owned customer record repository"
```

## Task 8: Build Sales Streamlit Workflow

**Files:**
- Create: `customer_management/ui/shared.py`
- Create: `customer_management/ui/sales.py`
- Create: `app.py`
- Create: `tests/ui/test_sales_app.py`
- Test: `tests/ui/test_sales_app.py`

- [ ] **Step 1: Write the failing sales UI test**

```python
from streamlit.testing.v1 import AppTest


def test_sales_login_page_shows_name_selector(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://")

    app = AppTest.from_file("app.py")
    app.run()

    assert any(widget.label == "选择销售姓名" for widget in app.selectbox)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/ui/test_sales_app.py -v`
Expected: FAIL because `app.py` and the sales UI do not exist

- [ ] **Step 3: Write minimal implementation**

Implement:

- top-level app router in `app.py`
- sales login form
- first-login password change screen
- "My Records" list
- record editor form backed by `build_record_form_schema`
- delete confirmation and logout button

Keep rendering logic in `customer_management/ui/sales.py` and shared helpers in `customer_management/ui/shared.py`

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/ui/test_sales_app.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app.py customer_management/ui/shared.py customer_management/ui/sales.py tests/ui/test_sales_app.py
git commit -m "feat: add sales streamlit workflow"
```

## Task 9: Build Admin User and Metadata Management UI

**Files:**
- Create: `customer_management/repositories/admin_users.py`
- Create: `customer_management/ui/admin.py`
- Create: `tests/ui/test_admin_app.py`
- Test: `tests/ui/test_admin_app.py`

- [ ] **Step 1: Write the failing admin UI test**

```python
from streamlit.testing.v1 import AppTest


def test_admin_login_page_shows_username_and_password(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://")

    app = AppTest.from_file("app.py")
    app.run()

    assert any(input_widget.label == "管理员用户名" for input_widget in app.text_input)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/ui/test_admin_app.py -v`
Expected: FAIL because the admin workflow does not exist

- [ ] **Step 3: Write minimal implementation**

Implement:

- admin repository create/auth helpers
- admin login form
- sales user management UI
- admin user management UI
- tag group and tag option management UI
- custom field and custom field option management UI

Prefer `st.data_editor` only where it improves admin batch editing; otherwise use explicit forms to keep behavior testable

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/ui/test_admin_app.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add customer_management/repositories/admin_users.py customer_management/ui/admin.py tests/ui/test_admin_app.py
git commit -m "feat: add admin management workflow"
```

## Task 10: Add Dashboard Aggregations and Records Overview

**Files:**
- Create: `customer_management/services/dashboard.py`
- Modify: `customer_management/ui/admin.py`
- Create: `tests/services/test_dashboard.py`
- Test: `tests/services/test_dashboard.py`

- [ ] **Step 1: Write the failing dashboard service test**

```python
from customer_management.services.dashboard import build_dashboard_snapshot


def test_build_dashboard_snapshot_returns_totals_rankings_and_distributions(db_session, dashboard_seed_data):
    snapshot = build_dashboard_snapshot(db_session)

    assert snapshot.total_records == 3
    assert snapshot.sales_rankings[0].count >= snapshot.sales_rankings[-1].count
    assert any(item.group_code == "customer_type" for item in snapshot.tag_distributions)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/services/test_dashboard.py -v`
Expected: FAIL because dashboard aggregation logic does not exist

- [ ] **Step 3: Write minimal implementation**

Implement:

- total metrics
- date trend series
- sales ranking aggregation
- tag distribution aggregation
- limited cross-statistics for:
  - sales user x customer type
  - brand x customer type
  - customer level x customer type

Render the dashboard and records overview filters in `customer_management/ui/admin.py`

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/services/test_dashboard.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add customer_management/services/dashboard.py customer_management/ui/admin.py tests/services/test_dashboard.py tests/conftest.py
git commit -m "feat: add admin dashboard reporting"
```

## Task 11: Add End-to-End Smoke Coverage and Run Full Verification

**Files:**
- Modify: `tests/ui/test_sales_app.py`
- Modify: `tests/ui/test_admin_app.py`
- Create: `README.md`
- Test: `tests/ui/test_sales_app.py`
- Test: `tests/ui/test_admin_app.py`

- [ ] **Step 1: Write one failing smoke test for a complete flow**

```python
def test_sales_user_can_log_in_create_record_and_see_it_in_list(app_fixture):
    app = app_fixture()
    app.run()

    app.selectbox(key="sales_user_name").select("Alice")
    app.text_input(key="sales_password").input("next-pass")
    app.form_submit_button("销售登录").click()
    app.run()

    app.text_input(key="customer_name").input("ACME")
    app.form_submit_button("保存记录").click()
    app.run()

    assert "ACME" in app.dataframe[0].value.to_string()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/ui/test_sales_app.py tests/ui/test_admin_app.py -v`
Expected: FAIL because the full workflow is not yet wired together correctly

- [ ] **Step 3: Write minimal implementation**

Fix integration gaps only:

- stable widget keys
- session transitions
- success/error messaging
- records list refresh after save/delete
- admin dashboard rendering on authenticated state

Add `README.md` with:

- environment setup
- `.env` instructions
- `python scripts/init_db.py`
- `streamlit run app.py`
- `pytest`

- [ ] **Step 4: Run full verification**

Run: `python -m pytest -v`
Expected: PASS across repository tests

Run: `python scripts/init_db.py`
Expected: schema creation and default metadata seed complete without exception

Run: `streamlit run app.py`
Expected: local app starts successfully

- [ ] **Step 5: Commit**

```bash
git add README.md tests/ui/test_sales_app.py tests/ui/test_admin_app.py app.py customer_management
git commit -m "test: add smoke coverage and docs"
```

## Manual Smoke Checklist

- [ ] Create `.env` from `.env.example` and set the real PostgreSQL URL
- [ ] Run `python scripts/init_db.py`
- [ ] Insert the first admin user directly in PostgreSQL with a hashed password
- [ ] Start the app with `streamlit run app.py`
- [ ] Log in as admin and create at least one sales user
- [ ] Log in as that sales user and change the initial password
- [ ] Create, edit, and delete one record as the sales user
- [ ] Confirm the admin dashboard updates after the record is recreated
- [ ] Deactivate a tag option and confirm it disappears from new edits while old data remains visible in reporting

## Notes

- Keep `main.py` untouched until the new Streamlit app is working; delete it only if it becomes noise
- Do not introduce attachments, audit logs, or password recovery while implementing this plan
- Prefer explicit forms and repository functions over hidden Streamlit state mutations

