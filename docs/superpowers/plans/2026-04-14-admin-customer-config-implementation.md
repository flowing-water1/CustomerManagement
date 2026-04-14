# Admin Customer Configuration Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the separate admin `标签配置` / `字段配置` tabs with a unified `客户资料配置` page that shows a business-facing configuration summary first, then supports summary-driven quick edits plus detailed tag and field editing below.

**Architecture:** Keep the existing SQLAlchemy metadata model and repository layer, but add focused update helpers and a small admin metadata summary service so the new page can be tested independently from the Streamlit layout. Refactor the current admin UI by extracting customer-configuration rendering into its own UI module, leaving `customer_management/ui/admin.py` responsible for workspace routing only.

**Tech Stack:** Python 3.11+, Streamlit 1.50, SQLAlchemy 2.x, pandas, pytest, streamlit.testing.v1

---

## File Structure

### Existing Files to Modify

- Modify: `customer_management/repositories/metadata.py`
  - Add update helpers for tag groups, tag options, custom fields, and custom field options so the new quick-edit and detailed-edit surfaces can reuse one repository API.
- Modify: `customer_management/ui/admin.py`
  - Replace the old `标签配置` / `字段配置` tabs with a single `客户资料配置` entry and delegate rendering to a focused module.
- Modify: `tests/ui/test_admin_app.py`
  - Add reusable admin-login setup and cover the new customer configuration summary plus summary-triggered edit flows.

### New Files to Create

- Create: `customer_management/services/admin_metadata.py`
  - Build a business-facing snapshot for the unified customer configuration page, including active + inactive visibility and overflow handling.
- Create: `customer_management/ui/admin_customer_config.py`
  - Render the `客户资料配置` page, summary card, summary quick-edit focus, and detailed `标签区` / `字段区`.
- Create: `tests/repositories/test_metadata.py`
  - Cover the new repository update helpers before the UI depends on them.
- Create: `tests/services/test_admin_metadata.py`
  - Cover snapshot shaping and inactive-item visibility rules without involving Streamlit.

### Existing Files to Read While Implementing

- Read: `docs/superpowers/specs/2026-04-14-admin-customer-config-ux-design.md`
  - Approved UX contract for this feature.
- Read: `customer_management/ui/sales.py`
  - Use the current sales record form as the reference output surface for helper copy and summary wording.
- Read: `tests/conftest.py`
  - Reuse the existing SQLite fixture setup and seeding patterns.

## Execution Notes

- Follow @test-driven-development for each task: test first, verify failure, minimal code, verify pass.
- Follow @verification-before-completion before claiming the redesign is finished.
- Do not introduce schema changes or new frontend technology.
- Keep quick edit narrow; put structural changes in the lower detailed sections.
- Prefer explicit keys for new Streamlit controls so `AppTest` can target them reliably.

## Task 1: Add Metadata Update Helpers

**Files:**
- Modify: `customer_management/repositories/metadata.py`
- Create: `tests/repositories/test_metadata.py`
- Test: `tests/repositories/test_metadata.py`

- [ ] **Step 1: Write the failing repository tests**

```python
from customer_management.repositories.metadata import (
    create_custom_field,
    create_custom_field_option,
    create_tag_group,
    create_tag_option,
    update_custom_field,
    update_custom_field_option,
    update_tag_group,
    update_tag_option,
)


def test_update_tag_group_and_option_persists_business_labels(db_session):
    group = create_tag_group(db_session, name="品牌", selection_mode="single")
    option = create_tag_option(db_session, group_id=group.id, label="壳牌")

    updated_group = update_tag_group(
        db_session,
        group_id=group.id,
        name="客户品牌",
        selection_mode="multiple",
    )
    updated_option = update_tag_option(
        db_session,
        option_id=option.id,
        label="美孚",
    )

    assert updated_group.name == "客户品牌"
    assert updated_group.selection_mode == "multiple"
    assert updated_option.label == "美孚"


def test_update_custom_field_and_option_persists_required_state(db_session):
    field = create_custom_field(
        db_session,
        name="采购周期",
        field_type="select",
        is_required=False,
    )
    option = create_custom_field_option(db_session, field_id=field.id, label="月结")

    updated_field = update_custom_field(
        db_session,
        field_id=field.id,
        name="采购周期（月）",
        field_type="select",
        is_required=True,
    )
    updated_option = update_custom_field_option(
        db_session,
        option_id=option.id,
        label="现结",
    )

    assert updated_field.name == "采购周期（月）"
    assert updated_field.is_required is True
    assert updated_option.label == "现结"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/repositories/test_metadata.py -v`
Expected: FAIL because the `update_*` repository helpers do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Add to `customer_management/repositories/metadata.py`:

```python
def update_tag_group(session, *, group_id: int, name: str, selection_mode: str):
    group = session.get(TagGroup, group_id)
    if group is None:
        raise ValueError("Tag group not found")
    group.name = name.strip()
    group.selection_mode = selection_mode
    session.add(group)
    session.commit()
    session.refresh(group)
    return group


def update_tag_option(session, *, option_id: int, label: str):
    option = session.get(TagOption, option_id)
    if option is None:
        raise ValueError("Tag option not found")
    option.label = label.strip()
    session.add(option)
    session.commit()
    session.refresh(option)
    return option


def update_custom_field(
    session,
    *,
    field_id: int,
    name: str,
    field_type: str,
    is_required: bool,
):
    field = session.get(CustomField, field_id)
    if field is None:
        raise ValueError("Custom field not found")
    field.name = name.strip()
    field.field_type = field_type
    field.is_required = is_required
    session.add(field)
    session.commit()
    session.refresh(field)
    return field


def update_custom_field_option(session, *, option_id: int, label: str):
    option = session.get(CustomFieldOption, option_id)
    if option is None:
        raise ValueError("Custom field option not found")
    option.label = label.strip()
    session.add(option)
    session.commit()
    session.refresh(option)
    return option
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/repositories/test_metadata.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add customer_management/repositories/metadata.py tests/repositories/test_metadata.py
git commit -m "feat: add admin metadata update helpers"
```

## Task 2: Add Admin Metadata Summary Service

**Files:**
- Create: `customer_management/services/admin_metadata.py`
- Create: `tests/services/test_admin_metadata.py`
- Test: `tests/services/test_admin_metadata.py`

- [ ] **Step 1: Write the failing summary-service tests**

```python
from customer_management.bootstrap import seed_default_metadata
from customer_management.repositories.metadata import (
    create_custom_field,
    set_tag_option_active,
)
from customer_management.services.admin_metadata import build_customer_config_snapshot
from customer_management.models import TagOption


def test_build_customer_config_snapshot_includes_inactive_tag_items(db_session):
    seed_default_metadata(db_session)
    kunlun = (
        db_session.query(TagOption)
        .filter(TagOption.value == "kunlun")
        .one()
    )
    set_tag_option_active(db_session, kunlun.id, False)

    snapshot = build_customer_config_snapshot(db_session)
    brand_row = next(row for row in snapshot.tag_rows if row.code == "brand")

    assert any(item.label == "昆仑" and item.is_active is False for item in brand_row.items)


def test_build_customer_config_snapshot_includes_field_rows_and_examples(db_session):
    seed_default_metadata(db_session)
    create_custom_field(
        db_session,
        name="采购周期",
        field_type="text",
        is_required=False,
    )

    snapshot = build_customer_config_snapshot(db_session)

    assert snapshot.summary_title == "当前配置情况"
    assert snapshot.field_rows
    assert snapshot.field_helper_examples == ["采购周期", "月需求量", "下次回访时间"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/services/test_admin_metadata.py -v`
Expected: FAIL because `customer_management/services/admin_metadata.py` does not exist.

- [ ] **Step 3: Write minimal implementation**

Create `customer_management/services/admin_metadata.py` with lightweight dataclasses and one builder:

```python
from dataclasses import dataclass, field

from customer_management.repositories.metadata import (
    list_custom_field_options,
    list_custom_fields,
    list_tag_groups,
    list_tag_options,
)


@dataclass
class SummaryItem:
    label: str
    is_active: bool


@dataclass
class SummaryRow:
    id: int
    code: str
    name: str
    subtitle: str
    items: list[SummaryItem] = field(default_factory=list)


@dataclass
class CustomerConfigSnapshot:
    summary_title: str
    tag_rows: list[SummaryRow]
    field_rows: list[SummaryRow]
    field_helper_examples: list[str]


def build_customer_config_snapshot(session) -> CustomerConfigSnapshot:
    ...
```

Implementation rules:

- use `list_tag_groups`, `list_tag_options`, `list_custom_fields`, `list_custom_field_options`
- include both active and inactive items
- keep tag and field rows separate
- emit human-facing subtitles such as `单选`, `多选`, `文本`, `数字 / 必填`
- hardcode `["采购周期", "月需求量", "下次回访时间"]` as the initial field helper examples to keep copy deterministic

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/services/test_admin_metadata.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add customer_management/services/admin_metadata.py tests/services/test_admin_metadata.py
git commit -m "feat: add customer config summary service"
```

## Task 3: Replace Metadata Tabs with Unified Customer Configuration Page

**Files:**
- Modify: `customer_management/ui/admin.py`
- Create: `customer_management/ui/admin_customer_config.py`
- Modify: `tests/ui/test_admin_app.py`
- Test: `tests/ui/test_admin_app.py`

- [ ] **Step 1: Write the failing admin UI test for the new page shell**

```python
from pathlib import Path

from streamlit.testing.v1 import AppTest

from customer_management.bootstrap import create_schema, seed_default_metadata
from customer_management.db import make_engine, make_session_factory
from customer_management.repositories.admin_users import create_admin_user


def _build_logged_in_admin_app(tmp_path, monkeypatch):
    database_path = tmp_path / "admin-ui.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    engine = make_engine(database_url)
    create_schema(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        seed_default_metadata(session)
        create_admin_user(
            session,
            username="hr-admin",
            display_name="HR",
            password="admin-pass",
        )

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")

    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run()
    app.text_input(key="admin_username").input("hr-admin")
    app.text_input(key="admin_password").input("admin-pass")
    next(button for button in app.button if button.label == "管理员登录").click()
    app.run()
    return app


def test_admin_workspace_shows_customer_config_summary(tmp_path, monkeypatch):
    app = _build_logged_in_admin_app(tmp_path, monkeypatch)

    markdown_values = [widget.value for widget in app.markdown]

    assert any("#### 客户资料配置" in value for value in markdown_values)
    assert any("#### 当前配置情况" in value for value in markdown_values)
    assert any("客户等级" in value for value in markdown_values)
    assert any("品牌" in value for value in markdown_values)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/ui/test_admin_app.py::test_admin_workspace_shows_customer_config_summary -v`
Expected: FAIL because the admin workspace still renders separate `标签配置` / `字段配置` tabs.

- [ ] **Step 3: Write minimal implementation**

Create `customer_management/ui/admin_customer_config.py` with:

- `render_customer_config(session)`
- `_render_page_intro()`
- `_render_summary_card(snapshot)`
- placeholder `_render_tag_section(session, snapshot)`
- placeholder `_render_field_section(session, snapshot)`

Implementation details:

- use `build_customer_config_snapshot(session)`
- render `#### 客户资料配置`
- render intro copy from the approved spec
- render `#### 当前配置情况`
- show business rows before the detailed sections
- remove the old `标签配置` and `字段配置` tabs from `customer_management/ui/admin.py`
- replace them with one `客户资料配置` tab that calls `render_customer_config(session)`

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/ui/test_admin_app.py::test_admin_workspace_shows_customer_config_summary -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add customer_management/ui/admin.py customer_management/ui/admin_customer_config.py tests/ui/test_admin_app.py
git commit -m "feat: add unified customer config page shell"
```

## Task 4: Add Summary-Driven Tag Quick Edit Flow

**Files:**
- Modify: `customer_management/ui/admin_customer_config.py`
- Modify: `tests/ui/test_admin_app.py`
- Test: `tests/ui/test_admin_app.py`

- [ ] **Step 1: Write the failing UI test for tag quick edit**

```python
from customer_management.models import TagOption
from customer_management.repositories.metadata import set_tag_option_active


def test_customer_config_summary_shows_inactive_tag_and_opens_tag_quick_edit(
    tmp_path, monkeypatch
):
    database_path = tmp_path / "admin-tag-quick-edit.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    engine = make_engine(database_url)
    create_schema(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        seed_default_metadata(session)
        create_admin_user(
            session,
            username="hr-admin",
            display_name="HR",
            password="admin-pass",
        )
        kunlun = (
            session.query(TagOption)
            .filter(TagOption.value == "kunlun")
            .one()
        )
        set_tag_option_active(session, kunlun.id, False)

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")

    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run()
    app.text_input(key="admin_username").input("hr-admin")
    app.text_input(key="admin_password").input("admin-pass")
    next(button for button in app.button if button.label == "管理员登录").click()
    app.run()

    markdown_values = [widget.value for widget in app.markdown]
    assert any("昆仑（已停用）" in value for value in markdown_values)

    app.button(key="admin_summary_focus_tag_brand").click()
    app.run()

    assert any(widget.key == "admin_quick_tag_option_label_brand" for widget in app.text_input)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/ui/test_admin_app.py::test_customer_config_summary_shows_inactive_tag_and_opens_tag_quick_edit -v`
Expected: FAIL because the summary rows do not yet expose focus state or quick-edit controls.

- [ ] **Step 3: Write minimal implementation**

In `customer_management/ui/admin_customer_config.py`:

- add session-state focus keys:
  - `admin_customer_config_focus_kind`
  - `admin_customer_config_focus_code`
- render one `修改` button per tag summary row with a unique key like `admin_summary_focus_tag_<code>`
- when focused, render one inline quick-edit form directly under that row
- include:
  - one text input keyed `admin_quick_tag_option_label_<code>`
  - one submit button to create a new option
  - one selectbox + toggle button to activate/deactivate an existing option
- render inactive summary items as `标签（已停用）` so state is testable through text
- keep only one focused editor open at a time

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/ui/test_admin_app.py::test_customer_config_summary_shows_inactive_tag_and_opens_tag_quick_edit -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add customer_management/ui/admin_customer_config.py tests/ui/test_admin_app.py
git commit -m "feat: add tag summary quick edit flow"
```

## Task 5: Add Field Quick Edit and Detailed Guidance Copy

**Files:**
- Modify: `customer_management/ui/admin_customer_config.py`
- Modify: `tests/ui/test_admin_app.py`
- Test: `tests/ui/test_admin_app.py`

- [ ] **Step 1: Write the failing UI test for field quick edit and helper copy**

```python
from customer_management.repositories.metadata import create_custom_field


def test_customer_config_field_section_shows_examples_and_opens_field_quick_edit(
    tmp_path, monkeypatch
):
    database_path = tmp_path / "admin-field-quick-edit.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    engine = make_engine(database_url)
    create_schema(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        seed_default_metadata(session)
        create_admin_user(
            session,
            username="hr-admin",
            display_name="HR",
            password="admin-pass",
        )
        create_custom_field(
            session,
            name="采购周期",
            field_type="text",
            is_required=False,
        )

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")

    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run()
    app.text_input(key="admin_username").input("hr-admin")
    app.text_input(key="admin_password").input("admin-pass")
    next(button for button in app.button if button.label == "管理员登录").click()
    app.run()

    markdown_values = [widget.value for widget in app.markdown]
    assert any("字段用于补充客户资料" in value for value in markdown_values)
    assert any("采购周期" in value for value in markdown_values)

    app.button(key="admin_summary_focus_field_custom_field").click()
    app.run()

    assert any(widget.key == "admin_quick_field_name_custom_field" for widget in app.text_input)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/ui/test_admin_app.py::test_customer_config_field_section_shows_examples_and_opens_field_quick_edit -v`
Expected: FAIL because the field section does not yet expose helper copy or summary-driven quick edit.

- [ ] **Step 3: Write minimal implementation**

In `customer_management/ui/admin_customer_config.py`:

- render the approved helper copy for `字段区`
- render example-driven helper text using `snapshot.field_helper_examples`
- add summary-row focus buttons for field rows with keys `admin_summary_focus_field_<code>`
- when focused, render an inline form with:
  - field name input keyed `admin_quick_field_name_<code>`
  - required checkbox keyed `admin_quick_field_required_<code>`
  - save button that calls `update_custom_field(...)`
- keep the lower detailed `字段区` visible with:
  - existing create-field flow
  - existing create-option flow for `select` fields
  - existing activate/deactivate controls
  - new business-facing copy and headings

- [ ] **Step 4: Run targeted UI verification**

Run: `python -m pytest tests/ui/test_admin_app.py -v`
Expected: PASS, including the existing login test plus the new customer-configuration tests.

- [ ] **Step 5: Commit**

```bash
git add customer_management/ui/admin_customer_config.py tests/ui/test_admin_app.py
git commit -m "feat: add field quick edit and guidance copy"
```

## Task 6: Run Full Verification and Update Operator Docs

**Files:**
- Modify: `README.md`
- Test: `tests/repositories/test_metadata.py`
- Test: `tests/services/test_admin_metadata.py`
- Test: `tests/ui/test_admin_app.py`
- Test: `tests/ui/test_sales_app.py`

- [ ] **Step 1: Write the failing documentation test expectation**

No code test is required here. Instead, verify the operator docs are missing the new admin workflow description before updating them.

Run: `rg -n "客户资料配置|当前配置情况" README.md`
Expected: no matches

- [ ] **Step 2: Update the docs minimally**

Add one short admin workflow note to `README.md` describing:

- admin metadata management now lives under `客户资料配置`
- the page begins with a `当前配置情况` summary
- changes there affect the sales record form

- [ ] **Step 3: Run targeted verification**

Run: `python -m pytest tests/repositories/test_metadata.py tests/services/test_admin_metadata.py tests/ui/test_admin_app.py -v`
Expected: PASS

- [ ] **Step 4: Run full verification**

Run: `python -m pytest -v`
Expected: PASS across the repository test suite

- [ ] **Step 5: Commit**

```bash
git add README.md tests/repositories/test_metadata.py tests/services/test_admin_metadata.py tests/ui/test_admin_app.py customer_management/repositories/metadata.py customer_management/services/admin_metadata.py customer_management/ui/admin.py customer_management/ui/admin_customer_config.py
git commit -m "feat: redesign admin customer configuration ux"
```

## Manual Smoke Checklist

- [ ] Log in as admin and confirm the old `标签配置` / `字段配置` split no longer appears.
- [ ] Open `客户资料配置` and confirm the top `当前配置情况` summary lists seeded groups such as `客户等级`, `客户类型`, and `品牌`.
- [ ] Confirm a disabled tag option remains visible in the summary with an `已停用` indicator.
- [ ] Add one tag option from the summary quick edit and confirm it appears in the summary immediately after rerun.
- [ ] Add one custom field from the field section and confirm it appears in the summary and later on the sales form.
- [ ] Log in as a sales user and confirm the new/updated metadata appears in the record form.

## Notes

- Keep the implementation DRY by reusing the existing create/toggle repository helpers in the new detailed sections.
- Do not reintroduce `st.data_editor` as the primary metadata UX.
- If `st.popover` proves hard to verify in `AppTest`, prefer inline containers for summary quick edit so the behavior remains deterministic and testable.
