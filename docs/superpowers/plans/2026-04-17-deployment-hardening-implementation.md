# Deployment Hardening Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the app safer to publish and deploy by aligning database driver usage and reducing runtime setup to a single required database URL.

**Architecture:** Keep the current Streamlit entrypoint and repository structure, but harden the configuration boundary and startup path. Settings become the single place that resolves `DATABASE_URL` from environment variables or Streamlit secrets, database URL normalization targets `psycopg`, and schema bootstrap continues to run automatically on startup.

**Tech Stack:** Python 3.9+, Streamlit, SQLAlchemy 2.x, psycopg, pytest, python-dotenv

---

### Task 1: Harden Configuration Resolution

**Files:**
- Modify: `customer_management/config.py`
- Modify: `tests/test_config.py`
- Test: `tests/test_config.py`

- [ ] **Step 1: Write the failing tests**

Add tests for:
- environment variables overriding secrets
- fallback when Streamlit secrets are unavailable

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_config.py -q`
Expected: FAIL because `Settings` does not yet support the new precedence and fallback behavior

- [ ] **Step 3: Write minimal implementation**

In `customer_management/config.py`:
- keep only `DATABASE_URL`
- add a source-aware settings constructor
- prefer environment variables over secrets
- fall back cleanly when secrets are unavailable

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_config.py -q`
Expected: PASS

### Task 2: Align Database URL Handling With `psycopg`

**Files:**
- Modify: `customer_management/db.py`
- Modify: `tests/test_db.py`
- Test: `tests/test_db.py`

- [ ] **Step 1: Write the failing tests**

Add tests for:
- `postgresql://...` normalizing to `postgresql+psycopg://...`
- `postgres://...` normalizing to `postgresql+psycopg://...`
- existing `postgresql+psycopg://...` staying unchanged

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_db.py -q`
Expected: FAIL because the code rewrites `psycopg` URLs to `psycopg2`

- [ ] **Step 3: Write minimal implementation**

In `customer_management/db.py`:
- normalize plain PostgreSQL URLs to the `psycopg` dialect
- remove the `psycopg2` fallback behavior

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_db.py -q`
Expected: PASS

### Task 3: Keep App Bootstrap Automatic

**Files:**
- Modify: `customer_management/ui/shared.py`
- Modify: `app.py`
- Modify: `scripts/init_db.py`
- Modify: `tests/test_bootstrap.py`
- Test: `tests/test_bootstrap.py`

- [ ] **Step 1: Write the failing tests**

Add tests covering:
- startup session factory always runs schema bootstrap and metadata seed

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_bootstrap.py -q`
Expected: FAIL because the tests still assume bootstrap is conditional

- [ ] **Step 3: Write minimal implementation**

In the startup path:
- remove the bootstrap flag from the cached session factory
- always run schema creation and metadata seed during startup
- keep `scripts/init_db.py` aligned with the same initialization behavior

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_bootstrap.py -q`
Expected: PASS

### Task 4: Document Secrets and Publishing Hygiene

**Files:**
- Add: `.streamlit/secrets.toml.example`
- Modify: `README.md`
- Modify: `.gitignore`

- [ ] **Step 1: Add documentation updates**

Document:
- local `.env` usage
- Streamlit Cloud secrets usage
- the single required `DATABASE_URL` setting
- repository files that should stay local only

- [ ] **Step 2: Verify docs are consistent**

Check the examples and paths manually in the updated files.

### Task 5: Run Final Verification

**Files:**
- Verify only: `customer_management/config.py`
- Verify only: `customer_management/db.py`
- Verify only: `customer_management/ui/shared.py`
- Verify only: `app.py`
- Verify only: `scripts/init_db.py`
- Verify only: `tests/test_config.py`
- Verify only: `tests/test_db.py`
- Verify only: `tests/test_bootstrap.py`

- [ ] **Step 1: Run focused tests**

Run: `python -m pytest tests/test_config.py tests/test_db.py tests/test_bootstrap.py -q`
Expected: PASS

- [ ] **Step 2: Run full suite**

Run: `python -m pytest -q`
Expected: PASS
