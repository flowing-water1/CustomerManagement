# Admin Config Delete And Separators Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add clearer visual separation to the unified `客户资料配置` page and add delete actions for tag groups, tag options, custom fields, and custom field options when they have never been referenced by sales data.

**Architecture:** Keep the existing unified admin customer configuration page, but extend the metadata repository with explicit “can delete” and “delete” helpers so the UI never guesses. The UI should only surface delete buttons when repository checks say the target is safe to delete, and otherwise continue to offer only enable/disable actions.

**Tech Stack:** Python 3.9+, Streamlit 1.50, SQLAlchemy 2.x, pytest, streamlit.testing.v1

---

## File Structure

- Modify: `customer_management/repositories/metadata.py`
  - Add delete guards and delete helpers for tag groups, tag options, custom fields, and custom field options.
- Modify: `customer_management/ui/admin_customer_config.py`
  - Add stronger section separators and conditionally render delete actions.
- Modify: `tests/repositories/test_metadata.py`
  - Cover deletable vs. used metadata behavior.
- Modify: `tests/ui/test_admin_app.py`
  - Cover delete-button visibility and preserve the quick-add bugfix.

## Task 1: Add Safe-Delete Repository Helpers

**Files:**
- Modify: `customer_management/repositories/metadata.py`
- Modify: `tests/repositories/test_metadata.py`
- Test: `tests/repositories/test_metadata.py`

- [ ] **Step 1: Write the failing repository tests**

```python
def test_unused_tag_group_and_option_can_be_deleted(db_session):
    group = create_tag_group(db_session, name="临时分类", selection_mode="single")
    option = create_tag_option(db_session, group_id=group.id, label="临时选项")

    assert can_delete_tag_group(db_session, group.id) is True
    assert can_delete_tag_option(db_session, option.id) is True

    delete_tag_option(db_session, option.id)
    delete_tag_group(db_session, group.id)


def test_used_metadata_cannot_be_deleted(db_session):
    ...
    assert can_delete_tag_option(db_session, used_option.id) is False
    with pytest.raises(ValueError):
        delete_tag_option(db_session, used_option.id)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/repositories/test_metadata.py -v`
Expected: FAIL because the `can_delete_*` and `delete_*` helpers do not exist yet.

- [ ] **Step 3: Write minimal implementation**

Add to `customer_management/repositories/metadata.py`:

- `can_delete_tag_group`
- `can_delete_tag_option`
- `can_delete_custom_field`
- `can_delete_custom_field_option`
- `delete_tag_group`
- `delete_tag_option`
- `delete_custom_field`
- `delete_custom_field_option`

Implementation rules:

- used `tag_groups` / `tag_options` are determined by `record_tags`
- used `custom_fields` are determined by `record_field_values`
- used `custom_field_options` are determined by matching `record_field_values.value_text` against the option value for the same field
- `delete_*` must raise `ValueError` when the target has been used

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/repositories/test_metadata.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add customer_management/repositories/metadata.py tests/repositories/test_metadata.py
git commit -m "feat: add safe delete guards for admin metadata"
```

## Task 2: Add Delete Actions and Stronger Visual Separation

**Files:**
- Modify: `customer_management/ui/admin_customer_config.py`
- Modify: `tests/ui/test_admin_app.py`
- Test: `tests/ui/test_admin_app.py`

- [ ] **Step 1: Write the failing UI tests**

```python
def test_used_tag_option_only_shows_disable_not_delete(...):
    ...
    assert not any(button.key == "admin_delete_tag_option_button" for button in app.button)


def test_unused_tag_group_shows_delete_action(...):
    ...
    assert any(button.key == "admin_delete_tag_group_button" for button in app.button)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/ui/test_admin_app.py -v`
Expected: FAIL because the customer-config UI does not yet expose delete visibility rules.

- [ ] **Step 3: Write minimal implementation**

In `customer_management/ui/admin_customer_config.py`:

- add `st.divider()` between:
  - intro and summary
  - summary and `标签区`
  - `标签区` and `字段区`
- wrap summary rows and quick-edit blocks in bordered containers where practical
- import and use the new repository delete helpers
- show delete buttons only when the selected object is deletable:
  - tag group
  - tag option
  - custom field
  - custom field option
- keep delete hidden entirely when the object has been used
- keep existing enable/disable controls for used objects
- preserve the existing quick-add form behavior and session-state fix

- [ ] **Step 4: Run targeted UI verification**

Run: `python -m pytest tests/ui/test_admin_app.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add customer_management/ui/admin_customer_config.py tests/ui/test_admin_app.py
git commit -m "feat: add admin metadata delete actions"
```

## Task 3: Run Full Verification

**Files:**
- Test: `tests/repositories/test_metadata.py`
- Test: `tests/ui/test_admin_app.py`
- Test: `tests/ui/test_sales_app.py`

- [ ] **Step 1: Run targeted verification**

Run: `python -m pytest tests/repositories/test_metadata.py tests/ui/test_admin_app.py -v`
Expected: PASS

- [ ] **Step 2: Run full verification**

Run: `python -m pytest -v`
Expected: PASS

- [ ] **Step 3: Commit final branch state**

```bash
git add customer_management/repositories/metadata.py customer_management/ui/admin_customer_config.py tests/repositories/test_metadata.py tests/ui/test_admin_app.py docs/superpowers/plans/2026-04-15-admin-config-delete-and-separators-implementation.md
git commit -m "feat: add admin config delete actions and separators"
```

## Manual Smoke Checklist

- [ ] Open `客户资料配置` and confirm there are clearer separators between the summary, `标签区`, and `字段区`.
- [ ] Pick an unused tag group or tag option and confirm a delete button appears.
- [ ] Pick a used tag option and confirm only enable/disable appears, with no delete button.
- [ ] Pick an unused field or field option and confirm a delete button appears.
- [ ] Confirm the quick-add tag option flow still works without any Streamlit session-state exception.
