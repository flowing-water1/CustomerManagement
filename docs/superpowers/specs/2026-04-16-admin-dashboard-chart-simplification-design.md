# Admin Dashboard Chart Simplification Design

## Overview

This document defines a focused UX simplification for the admin dashboard statistics page.

The current dashboard includes three expandable `交叉统计` tables. These tables are technically correct, but they read like backend analysis output instead of a business dashboard. For non-technical admin users, they add cognitive load and compete with the more useful high-level charts.

The new direction is:

- remove the three cross-statistic tables entirely
- keep the top KPI metrics
- keep the existing trend and sales comparison charts
- add explicit titles to the existing charts
- add two more intuitive donut charts for customer structure

The goal is to make the page readable at a glance for office/admin staff without requiring explanation.

## Confirmed Scope

### Included

- keep the existing five KPI metrics:
  - total records
  - records added today
  - records added this week
  - records added this month
  - active sales count
- keep the existing line chart for record creation trend
- keep the existing bar chart for sales submission comparison
- add clear chart titles for the two existing charts
- add a donut chart for customer level distribution
- add a donut chart for customer type distribution (`已成交 / 未成交`)
- keep the tag distribution table as a lower-priority detail section below the main charts

### Excluded

- no cross-statistic tables
- no expander sections for cross-statistic output
- no new filtering controls
- no export/report changes
- no redesign of the records overview tab

## UX Decisions

### Dashboard Hierarchy

The page should have three visual layers:

1. KPI summary metrics
2. four primary charts
3. one lower-priority detail table

This keeps the most understandable information in the main visual area and pushes more detailed reporting lower on the page.

### Main Chart Grid

The main chart area should be arranged as two rows with two charts per row:

- Row 1:
  - `新增客户记录趋势`
  - `各销售提交客户数`
- Row 2:
  - `客户等级分布`
  - `已成交 / 未成交占比`

### Chart Titles

Every chart must have a visible heading directly above it.

The current trend and sales charts are hard to interpret because they render without labels. The new version should explicitly title them so users do not need to infer what the chart means.

### Lower-Priority Detail Table

The existing tag distribution table should remain, but it should no longer compete with the core charts.

Its title should be simplified to something business-readable such as:

- `各标签使用情况`

This keeps detail available without leading the user into analyst-style views.

## Data and Implementation Decisions

### Remove Cross Statistics From the UI

The dashboard should stop rendering the following comparisons:

- sales x customer type
- brand x customer type
- customer level x customer type

These sections should be fully removed from the visible dashboard.

### Remove Cross Statistics From the Snapshot

The preferred implementation is to remove cross-statistic aggregation from `build_dashboard_snapshot(...)`, not just hide it in the UI.

Reasons:

- reduces query cost
- removes dead data from the dashboard model
- keeps the snapshot aligned with what the page actually presents

### Add Distribution Data For Donut Charts

The dashboard snapshot should expose two simple distribution datasets:

- customer level distribution
- customer type distribution

Each dataset only needs:

- label
- count

This matches donut chart needs and avoids extra transformation logic in the UI layer.

### Chart Technology

Use a chart type that supports donut/pie visualization cleanly in Streamlit.

The repository environment already supports `altair`, so the simplest approach is:

- keep `st.line_chart` for the trend chart
- keep `st.bar_chart` for the sales comparison chart
- use `st.altair_chart` for the two donut charts

This keeps the implementation lightweight and avoids introducing new dependencies.

## Empty-State Behavior

If one of the donut chart datasets is empty:

- do not render an empty chart
- show a short info message in that chart slot, such as:
  - `暂无客户等级数据`
  - `暂无成交状态数据`

This avoids blank visual blocks.

## Testing

Add or update dashboard tests to verify:

- cross-statistic data is no longer required by the snapshot/UI path
- the new customer level distribution is present when seed data includes those tags
- the customer type distribution is present when seed data includes those tags
- the dashboard rendering path still succeeds with the simplified structure

## Summary

This change intentionally makes the statistics page less “analytical” and more “administrative.”

The new dashboard should help a non-technical admin answer these questions quickly:

- how many records do we have
- are records growing
- which sales are submitting more customers
- what customer levels are we holding
- what share is already成交 vs 未成交

Anything deeper than that should not be the default first-screen experience.
