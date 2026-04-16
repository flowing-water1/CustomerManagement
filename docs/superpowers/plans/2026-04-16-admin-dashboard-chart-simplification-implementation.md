# Admin Dashboard Chart Simplification Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Simplify the admin dashboard by removing cross-stat tables, adding chart titles, and introducing two donut charts for customer level and customer type distribution.

**Architecture:** Keep the dashboard flow centered on `build_dashboard_snapshot(...)` plus `_render_dashboard_overview(...)`. Remove unused cross-stat aggregation from the snapshot layer, add two simple distribution datasets, and render them in the admin UI with lightweight Altair donut charts while preserving the existing KPI and trend/ranking visuals.

**Tech Stack:** Python, Streamlit, SQLAlchemy, Pandas, Altair, Pytest

---

### Task 1: Reshape Dashboard Snapshot Data

**Files:**
- Modify: `customer_management/services/dashboard.py`
- Modify: `tests/services/test_dashboard.py`
- Test: `tests/services/test_dashboard.py`

- [ ] **Step 1: Write the failing test**

Add assertions covering:
- customer level distribution exists
- customer type distribution exists
- cross statistics are no longer part of the snapshot contract

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda\python.exe -m pytest tests/services/test_dashboard.py -q`
Expected: FAIL because the snapshot does not yet expose the new distribution fields

- [ ] **Step 3: Write minimal implementation**

In `customer_management/services/dashboard.py`:
- remove `CrossStatItem`
- remove `cross_statistics` from `DashboardSnapshot`
- add a simple distribution item dataclass
- add snapshot fields for:
  - `customer_level_distribution`
  - `customer_type_distribution`
- implement aggregation helpers that count records by tag group code

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda\python.exe -m pytest tests/services/test_dashboard.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add customer_management/services/dashboard.py tests/services/test_dashboard.py
git commit -m "refactor: simplify dashboard snapshot data"
```

### Task 2: Render Simplified Dashboard Charts

**Files:**
- Modify: `customer_management/ui/admin.py`
- Add/Modify: `tests/ui/test_admin_dashboard_unit.py`
- Test: `tests/ui/test_admin_dashboard_unit.py`

- [ ] **Step 1: Write the failing test**

Add a focused UI/unit test covering:
- existing charts now render with titles
- cross-stat expanders are gone
- donut chart render path is invoked when distribution data exists

- [ ] **Step 2: Run test to verify it fails**

Run: `D:\Anaconda\python.exe -m pytest tests/ui/test_admin_dashboard_unit.py -q`
Expected: FAIL because the admin dashboard still renders the old table/expander layout

- [ ] **Step 3: Write minimal implementation**

In `customer_management/ui/admin.py`:
- import `altair`
- add a small donut chart helper
- render chart titles above trend and sales charts
- render a two-column row for:
  - customer level donut
  - customer type donut
- keep tag distribution table below, but rename its heading to `各标签使用情况`
- remove all cross-stat expander rendering

- [ ] **Step 4: Run test to verify it passes**

Run: `D:\Anaconda\python.exe -m pytest tests/ui/test_admin_dashboard_unit.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add customer_management/ui/admin.py tests/ui/test_admin_dashboard_unit.py
git commit -m "feat: simplify admin dashboard charts"
```

### Task 3: Run End-to-End Verification

**Files:**
- Verify only: `customer_management/services/dashboard.py`
- Verify only: `customer_management/ui/admin.py`
- Verify only: `tests/services/test_dashboard.py`
- Verify only: `tests/ui/test_admin_dashboard_unit.py`

- [ ] **Step 1: Run focused dashboard tests**

Run:
`$env:NUMEXPR_MAX_THREADS='1'; $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; D:\Anaconda\python.exe -m pytest tests/services/test_dashboard.py tests/ui/test_admin_dashboard_unit.py -q`

Expected: PASS

- [ ] **Step 2: Run full suite**

Run:
`$env:NUMEXPR_MAX_THREADS='1'; $env:PYTEST_DISABLE_PLUGIN_AUTOLOAD='1'; D:\Anaconda\python.exe -m pytest -q`

Expected: PASS

- [ ] **Step 3: Commit if needed**

If verification required tiny cleanup edits:

```bash
git add customer_management/services/dashboard.py customer_management/ui/admin.py tests/services/test_dashboard.py tests/ui/test_admin_dashboard_unit.py
git commit -m "test: cover simplified admin dashboard"
```
