# Customer Management Design

## Overview

This document defines the first implementation of a Streamlit-based customer information management system backed by PostgreSQL.

The system serves two roles:

- Sales users: select their name from a dropdown, authenticate with a password, and manage only their own customer records.
- Admin users: log in with username and password, manage users and dynamic metadata, and view system-wide records and statistics.

The primary goals of the first version are:

- Rapid delivery with Streamlit
- Dynamic admin-managed tags and custom fields
- Clear ownership boundaries between sales and admin workflows
- Practical reporting for daily business use

## Confirmed Scope

### Included

- PostgreSQL as the only database
- Streamlit as the frontend and application runtime
- Admin login with username and password
- Sales login with name selection plus password
- Admin-created users only; no registration flow
- Sales can create, view, edit, and delete only their own records
- Admin can view all records and system-wide statistics
- Admin can manage sales users, admin users, tag groups, tag options, and custom fields
- Fixed customer fields for v1:
  - customer name
  - contact name
  - phone
  - remark
- Dynamic tag groups and options
- Dynamic custom fields
- Dashboard statistics including:
  - overall totals
  - time-based trends
  - sales rankings
  - tag distributions
  - conversion-related views based on tag values
  - limited cross-statistics

### Excluded

- Sales self-registration
- Password recovery flow
- Attachment upload
- Audit log
- Soft delete or recycle bin
- Approval workflows
- Notification system
- Complex export/report engine

## Product Decisions

### Database Choice

PostgreSQL is the chosen database. MongoDB is not required for this use case because dynamic tags and custom fields are modeled as metadata and relational records rather than schema changes.

### Authentication Model

- Admin users authenticate with `username + password`
- Sales users authenticate with `name selection + password`
- Sales users do not type names manually
- New sales users receive an initial password and may be forced to change it on first login
- Forgotten passwords are handled manually through direct database changes, not through product UI

### Record Ownership and Deletion

- Each customer record belongs to exactly one sales user
- Sales users can only view and modify their own records
- Deletion is hard delete
- Deleted records disappear from lists and statistics immediately

## System Structure

The application is organized into three functional areas.

### 1. Sales Area

Pages:

- Login
- My Records
- New/Edit Record
- Change My Password

Responsibilities:

- Authenticate the current sales user
- Render personal record list
- Render dynamic entry form from admin-managed metadata
- Enforce ownership on edit and delete

### 2. Admin Area

Pages:

- Admin Login
- Dashboard
- Records Overview
- Sales User Management
- Admin User Management
- Tag Configuration
- Custom Field Configuration

Responsibilities:

- Authenticate admin users
- View global records and statistics
- Manage users and metadata
- Provide operational oversight

### 3. Shared Application Layer

Responsibilities:

- Session management
- Authorization checks
- Database access
- Dynamic form rendering
- Validation
- Statistics queries

## Role and Permission Model

### Admin

Can:

- Log in to the admin area
- View all customer records
- View all statistics
- Create and manage admin accounts
- Create and manage sales users
- Set initial sales passwords
- Configure tag groups and options
- Configure custom fields

Cannot:

- Use public or self-registration flows, because none exist in v1

### Sales

Can:

- Log in by selecting their own name and entering a password
- View only their own records
- Create their own records
- Edit their own records
- Delete their own records
- Change their own password

Cannot:

- View other sales users' records
- Access admin pages
- Manage metadata

### Unauthenticated Visitor

Cannot access business data.

## Database Design

The recommended schema for v1 is relational core data plus dynamic metadata.

### `admin_users`

Purpose: admin authentication and lifecycle management.

Suggested columns:

- `id`
- `username`
- `password_hash`
- `display_name`
- `is_active`
- `created_at`
- `updated_at`

Constraints:

- unique `username`

### `sales_users`

Purpose: sales identity, login selection source, and password storage.

Suggested columns:

- `id`
- `name`
- `password_hash`
- `is_active`
- `must_change_password`
- `created_at`
- `updated_at`

Constraints:

- unique `name`

### `customer_records`

Purpose: fixed customer record data and ownership.

Suggested columns:

- `id`
- `sales_user_id`
- `customer_name`
- `contact_name`
- `phone`
- `remark`
- `created_at`
- `updated_at`

Constraints:

- foreign key `sales_user_id -> sales_users.id`

### `tag_groups`

Purpose: admin-managed tag categories such as customer level, customer type, brand, oil type, authorized dealer, and future categories.

Suggested columns:

- `id`
- `name`
- `code`
- `selection_mode`
- `sort_order`
- `is_active`
- `created_at`
- `updated_at`

Rules:

- `selection_mode` is `single` or `multiple`
- unique `code`

### `tag_options`

Purpose: selectable options within a tag group.

Suggested columns:

- `id`
- `group_id`
- `label`
- `value`
- `sort_order`
- `is_active`
- `created_at`
- `updated_at`

Constraints:

- foreign key `group_id -> tag_groups.id`

### `record_tags`

Purpose: selected tag options for a customer record.

Suggested columns:

- `id`
- `record_id`
- `group_id`
- `option_id`
- `created_at`

Constraints:

- foreign key `record_id -> customer_records.id`
- foreign key `group_id -> tag_groups.id`
- foreign key `option_id -> tag_options.id`
- unique pair to prevent duplicate links for the same record and option

Business rule:

- for `single` groups, one record may only have one option within the group

### `custom_fields`

Purpose: admin-managed dynamic fields.

Suggested columns:

- `id`
- `name`
- `code`
- `field_type`
- `is_required`
- `sort_order`
- `is_active`
- `created_at`
- `updated_at`

Supported field types in v1:

- `text`
- `textarea`
- `number`
- `date`
- `select`

Constraints:

- unique `code`

### `custom_field_options`

Purpose: option values for `select` custom fields.

Suggested columns:

- `id`
- `field_id`
- `label`
- `value`
- `sort_order`
- `is_active`

Constraints:

- foreign key `field_id -> custom_fields.id`

### `record_field_values`

Purpose: values of dynamic custom fields per record.

Suggested columns:

- `id`
- `record_id`
- `field_id`
- `value_text`
- `created_at`
- `updated_at`

Constraints:

- foreign key `record_id -> customer_records.id`
- foreign key `field_id -> custom_fields.id`

Note:

- `value_text` is acceptable for v1 to simplify dynamic rendering and storage
- typed expansion can be added later if numeric/date querying becomes more demanding

## UI and Interaction Design

### Sales Login

Flow:

1. Sales user selects their name from a dropdown
2. Sales user enters password
3. On success:
   - if `must_change_password = true`, redirect to password change page
   - otherwise open `My Records`

### My Records

Purpose:

- personal work area for sales users

Features:

- list only the current user's records
- default sort by `updated_at DESC`
- search by customer name, contact name, or phone
- per-row actions:
  - edit
  - delete

### New/Edit Record

Form content:

- fixed fields:
  - customer name
  - contact name
  - phone
  - remark
- dynamic tag groups rendered from active metadata
- dynamic custom fields rendered from active metadata

Validation:

- required fixed fields
- active required custom fields
- single-select vs multi-select rules for tag groups

Authorization:

- create: record owner is always the logged-in sales user
- edit: only if the current sales user owns the record

### Delete Record

Behavior:

- confirmation required
- hard delete cascades related tag and custom field values

### Change My Password

Flow:

- input old password
- input new password
- confirm new password
- update password hash
- clear `must_change_password` when successful

### Admin Dashboard

KPIs:

- total record count
- records added today
- records added this week
- active sales count within current filter window

Charts and views:

- time trend of new records
- ranking by sales user
- tag distribution by group
- conversion views based on configured tags
- limited cross-statistics

### Records Overview

Features:

- global record list
- filter by date range
- filter by sales user
- filter by tag values
- inspect record details

V1 decision:

- admins view records but do not edit them in product UI
- admin-side editing can be added later if needed

### Sales User Management

Features:

- create sales users
- activate/deactivate sales users
- set initial password
- set first-login password change requirement

### Admin User Management

Features:

- create admin users
- activate/deactivate admin users

### Tag Configuration

Features:

- create and edit tag groups
- choose single or multiple selection mode
- create and edit tag options
- sort and activate/deactivate groups and options

### Custom Field Configuration

Features:

- create and edit custom fields
- choose field type
- set required flag
- sort and activate/deactivate fields
- manage options for `select` fields

## Statistics Design

All statistics in v1 are based on records that currently exist in the database. Because deletion is permanent, deleted records do not contribute to any statistic.

### Total Metrics

- total records
- records created today
- records created this week
- records created this month
- active sales count within selected time range

### Trend Metrics

- daily created-record trend
- weekly trend can be added later if useful

### Sales Metrics

- records per sales user
- ranking by volume
- tag distribution by sales user

### Tag Metrics

- distribution of options within each tag group

Examples:

- customer level: normal vs important
- customer type: converted vs not converted
- brand distribution

### Conversion Metrics

V1 uses the business tag group that represents converted vs not converted as the conversion source.

Examples:

- converted count
- not converted count
- converted count by sales user
- conversion ratio by sales user

### Cross-Statistics

V1 should support a limited set of practical combinations instead of arbitrary pivot exploration.

Recommended combinations:

- sales user x customer type
- brand x customer type
- customer level x customer type

## Streamlit Implementation Notes

Streamlit official capabilities are sufficient for v1.

Recommended primitives:

- `st.form` for login and record input
- `st.selectbox` for sales user selection
- `st.pills`, `st.segmented_control`, or `st.multiselect` for tags depending on widget behavior and installed Streamlit version
- `st.data_editor` for admin metadata maintenance
- `st.metric`, `st.line_chart`, `st.bar_chart`, `st.altair_chart`, or `st.plotly_chart` for dashboard reporting
- `st.session_state` for session management

Important note:

- Streamlit official authentication helpers target OIDC flows
- This project needs application-managed credentials stored in PostgreSQL
- Therefore authentication and authorization are implemented inside the app

## Key Business Rules

- Sales users must select names from a dropdown, not free text
- Sales users only access their own records
- Admin users have global access
- Inactive users cannot authenticate
- Disabled tag groups/options are hidden from new edits but historical data remains queryable
- Disabled custom fields are hidden from new edits but stored values remain queryable
- V1 should prefer deactivation instead of destructive metadata deletion

## Risks and Tradeoffs

### Hard Delete

Pros:

- simple user model
- simple storage model

Cons:

- no audit trail
- statistics change immediately after deletion
- accidental deletion cannot be recovered in product UI

### Sales Name Selection

Pros:

- fast login flow
- easy for business users

Cons:

- sales identity depends on password secrecy
- name uniqueness is required

### Dynamic Metadata

Pros:

- avoids repeated schema changes
- supports admin-managed evolution

Cons:

- more tables than a single-table design
- requires a metadata-driven form renderer

## Suggested Non-Goals for V1

To keep implementation tight, avoid adding the following during initial build:

- attachment support
- self-service password reset
- soft delete
- audit history
- arbitrary report builder
- admin-side record editing

## Open Follow-Up Items

These are intentionally deferred, not blockers for v1:

- whether admins should later edit all records
- whether some dynamic fields should later become fixed columns
- whether export should be added
- whether deletion should later become soft delete

## Implementation Direction

Recommended implementation direction for the first build:

1. Set up the app skeleton and PostgreSQL connection
2. Implement schema and seed metadata from the provided tag examples
3. Implement shared auth/session layer
4. Implement sales workflow
5. Implement admin metadata management
6. Implement dashboard and statistics
7. Add app-level tests for core flows

