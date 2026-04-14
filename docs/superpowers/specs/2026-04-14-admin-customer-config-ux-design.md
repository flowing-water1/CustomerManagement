# Admin Customer Configuration UX Design

## Overview

This document defines the admin UX redesign for metadata management in the Streamlit customer management app.

The current admin experience is technically usable for operators who already understand the system model, but it performs poorly for first-time or non-technical admins because the UI exposes backend concepts before it explains the current business-facing configuration state.

The redesign replaces the separate `标签配置` and `字段配置` tabs with a single `客户资料配置` page that first shows the current configuration in business language, then supports both quick edits and detailed edits from the same page.

## Problem Statement

The current admin UI in `customer_management/ui/admin.py` has two main UX problems:

- It separates metadata into `标签配置` and `字段配置` before the admin understands what those areas mean.
- It presents configuration as tables and forms instead of as the current state that sales users actually work with.

As a result, a new admin must already know:

- what a tag group is
- what a custom field is
- which area should be used for a new business requirement
- how the configuration affects the sales record form

This is too much system knowledge to require from an HR or operations user who only wants to maintain customer classification and data-entry items.

## Design Goals

- Let a first-time admin understand the current metadata state within the first screen.
- Use business-facing language before system-facing language.
- Make the admin page answer “what is configured now?” before “how do I edit it?”
- Preserve access to both quick edits and detailed edits.
- Keep disabled items visible in a weaker visual state instead of hiding them.
- Stay within Streamlit-native interaction patterns so the redesign remains testable and maintainable.

## Non-Goals

- No metadata model rewrite.
- No custom frontend outside the current Streamlit app architecture.
- No major schema changes.
- No admin-side redesign of the sales record editor in this phase.

## Confirmed Product Decisions

The following decisions were confirmed during the design conversation:

- Replace separate `标签配置` and `字段配置` tabs with one `客户资料配置` page.
- The page should begin with a top summary card instead of backend tables.
- The summary should show both active and inactive items.
- Inactive items should remain visible but visually weakened.
- Admins should be able to start editing from both the summary card and the detailed sections below.
- The summary should prioritize business grouping over technical metadata structure.
- The page should avoid “empty state” language such as `暂无数据` and instead use example-driven helper copy.
- The UX should explain current customer-facing configuration, not abstract system concepts.

## Page Information Architecture

### Page Name

`客户资料配置`

### Top-Level Structure

The page is organized into three vertical sections:

1. page intro
2. current configuration summary
3. detailed editing workspace

### 1. Page Intro

The top of the page should use short business-facing copy instead of metadata terminology.

Recommended copy:

- `这里展示销售当前会用到的客户分类和补充资料。你在这里修改后，销售录入页会同步变化。`

This sets the mental model immediately:

- tags and fields are not abstract admin objects
- they are the sales team’s current customer information template

### 2. Current Configuration Summary

This is the primary orientation surface for the admin.

It should appear as a large summary card titled:

- `当前配置情况`

Helper copy:

- `先看现在怎么配，再决定改哪里。`

The summary must show the current state in business grouping form.

Example rows:

- `客户等级：一般 / 重要`
- `客户类型：已成交 / 未成交`
- `品牌：壳牌 / 美孚 / 昆仑`
- `补充字段：采购周期 / 月需求量 / 下次回访时间`

Each row should include:

- business label
- currently visible values or fields
- secondary metadata hints when useful
- direct action entry

The summary is a business snapshot, not a data table.

### 3. Detailed Editing Workspace

Below the summary, the page should split into two detailed sections:

- `标签区`
- `字段区`

These sections are still needed because some edits are too structural for the summary area alone.

The summary gives orientation.
The lower sections provide the full editor.

## Summary Card Design

### Row Structure

Each summary row should follow the same pattern:

- group name
- current contents
- lightweight status hints
- action button

Example:

- `客户类型`
- `已成交 / 未成交`
- secondary note: `单选`
- action: `修改`

For fields:

- `月需求量`
- secondary note: `数字 / 必填`
- action: `修改`

### What to Show Prominently

Show first:

- business labels
- current active values
- current field names

Show as secondary hints:

- single vs multiple
- field type
- required flag
- inactive status

Do not prioritize:

- internal codes
- stored values
- database-oriented identifiers

### Handling Long Lists

If a tag group or field list becomes long:

- show only the first few items by default
- then append a compact overflow hint such as `还有 3 项`
- reveal the full list in edit mode

This keeps the summary readable while still proving that more configuration exists.

### Disabled Items

Disabled items must remain visible.

Recommended behavior:

- active items render normally
- inactive items render in a muted style
- inactive items may use a descriptive label such as `已停用，销售录入时不会再看到`

The redesign should avoid the current pattern where admins might assume a removed-looking item no longer exists.

## Editing Interaction Model

### Primary Principle

The page supports two layers of editing:

- quick edit from the summary row
- detailed edit in the lower workspace

### Summary-Initiated Editing

Every summary row should expose a direct action:

- `修改`
- `新增选项`
- `新增字段`

When the admin clicks a summary-row action:

1. expand a lightweight inline editor near that row
2. scroll or highlight the matching detailed editor below

This creates a strong “I clicked here, the system is editing this exact thing” relationship.

### What Belongs in Quick Edit

Quick edit should include common, low-risk operations.

For tags:

- add option
- rename option
- activate/deactivate option

For fields:

- rename field
- activate/deactivate field
- toggle required state

### What Belongs in Detailed Edit

Structural or higher-risk changes should stay in the lower sections.

For tags:

- single vs multiple selection mode
- tag-group ordering
- broader group-level settings

For fields:

- field type
- ordering
- select-field option management
- descriptive helper examples

### Single Focus Rule

Only one editing focus should be expanded at a time.

This prevents the page from turning into multiple simultaneous edit surfaces, which would be overwhelming for a non-technical admin.

## Detailed Workspace Design

### 标签区

Purpose:

- maintain customer classification dimensions
- maintain the available choices under each dimension

Helper copy:

- `标签用于给客户分类，方便销售选择，也方便后续筛选和统计。`

Expected actions:

- add tag group
- edit group name
- change selection mode
- add option
- rename option
- activate/deactivate option

### 字段区

Purpose:

- maintain extra customer information collected by sales

Helper copy:

- `字段用于补充客户资料，比如采购周期、月需求量、下次回访时间。`

Expected actions:

- add field
- rename field
- change type
- toggle required
- activate/deactivate field
- manage select-type options

### Empty-or-Light Configuration States

The system should avoid cold backend-style messages such as:

- `暂无数据`
- `暂无字段`

Instead, use example-driven helper copy.

Examples:

- `常见补充字段：采购周期 / 月需求量 / 下次回访时间`
- `这里通常会放销售录入时需要补充的信息`
- `你可以先从常见分类开始添加`

This better matches the user’s real need: understanding what kind of content belongs here.

## Copy and Terminology Rules

### Preferred Language

Use business language first.

Preferred:

- `客户资料配置`
- `当前配置情况`
- `新增分类`
- `新增选项`
- `新增字段`
- `销售录入页会同步变化`

Avoid leading with:

- `标签组`
- `字段选项`
- `selection_mode`
- `value`
- `code`

### Tone

The tone should feel like a business configuration workspace, not an engineering console.

The copy should follow this order:

1. what this area controls
2. where the change will show up
3. what action to take

## Streamlit Implementation Direction

The redesign should stay within Streamlit-native components rather than custom JavaScript-heavy UI.

Recommended building blocks:

- `st.container` for the summary card and each grouped section
- `st.columns` for row layout and action placement
- `st.segmented_control` for single-choice quick edits where appropriate
- `st.pills` for pill-style option display and possibly multi-select quick edits
- `st.popover` for compact quick-edit surfaces attached to summary actions
- explicit forms for detailed edits

Avoid using `st.data_editor` as the primary experience for this page.

Reason:

- it reads like a generic admin table
- it weakens the business-state snapshot model
- it is less aligned with the approved “summary card first” direction

`st.data_editor` can still be used selectively if a very specific batch-edit subproblem appears later, but it should not define the page architecture.

## Relationship to Existing UI

The current admin workspace in `customer_management/ui/admin.py` uses two tabs:

- `标签配置`
- `字段配置`

Both areas currently present:

- dataframe overviews
- create forms
- separate enable/disable controls

The redesign should consolidate those behaviors into one page while keeping the existing repository and service model intact.

The current sales record form in `customer_management/ui/sales.py` remains the target output surface for this configuration, so the new admin page should consistently frame metadata in terms of “what sales will see”.

## Testing Strategy

The redesign should include UI-oriented regression coverage.

Recommended tests:

- admin page renders `客户资料配置` instead of separate metadata tabs
- summary card renders known default tag groups
- summary card shows inactive items in a weakened state indicator
- summary-row action opens the expected quick-edit surface
- quick edit and detailed edit operate on the same underlying metadata target
- field helper copy appears in the detailed field section

Tests should stay compatible with Streamlit `AppTest` and existing repository-backed fixtures.

## Risks and Tradeoffs

### Risk: Too Much Editing in the Summary

If the summary becomes fully editable everywhere, the page will become visually noisy and cognitively heavy.

Mitigation:

- keep quick edit narrow
- keep structural changes in the lower workspace
- allow only one expanded editing focus at a time

### Risk: Ambiguity Between Tags and Fields

If the page removes all distinction between tag-based classification and field-based data entry, admins may again lose the mental model.

Mitigation:

- keep one unified page
- still maintain two clearly named sections below the summary
- use helper copy to explain the difference in plain language

### Risk: Overflow in Large Configurations

If tag groups and fields grow significantly, the summary may become tall and noisy.

Mitigation:

- use compact row patterns
- truncate long option lists
- show overflow counts
- preserve detailed editing below

## Recommended Implementation Sequence

1. Replace the existing two metadata tabs with a single `客户资料配置` entry in the admin workspace.
2. Build the top summary card using current repository data.
3. Add summary-row actions that connect to detailed sections.
4. Refactor the current tag-management UI into the lower `标签区`.
5. Refactor the current field-management UI into the lower `字段区`.
6. Add helper copy and example-driven guidance.
7. Add UI tests for summary rendering and summary-to-detail editing flow.

## Approval Outcome

This design reflects the user-approved direction:

- unified `客户资料配置` page
- top summary card first
- active and inactive items both visible
- quick edits from the summary
- detailed edits in lower tag and field sections
- business-state snapshot framing instead of backend metadata framing
