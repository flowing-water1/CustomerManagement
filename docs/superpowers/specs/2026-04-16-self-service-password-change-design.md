# Self-Service Password Change Design

## Overview

This document defines a small self-service password change feature for both logged-in sales users and logged-in admin users.

Currently, sales users can change their password only during the first-login forced password change flow. Admin users do not have a self-service password change flow at all. This creates an operational gap: users who know their current password still need outside help if they want to update it later.

The new feature adds a simple “change my own password” entry point for both roles.

## Confirmed Scope

### Included

- sales users can change their own password after logging in
- admin users can change their own password after logging in
- both flows require the current password
- both flows require entering the new password twice
- successful change keeps the user logged in
- successful change shows a clear success message
- failed current-password validation shows a clear error message
- mismatched or empty new password shows a clear error message

### Excluded

- password reset by email
- forgotten-password flow
- admin resetting another admin’s password
- admin resetting sales passwords
- password strength policy beyond the existing non-empty confirmation check
- forced logout after password change

## UX Decisions

### Entry Points

Both roles should see the password action in the top-right account area.

Sales area:

- `修改密码`
- `退出登录`

Admin area:

- `修改密码`
- `退出管理员登录`

This keeps the action close to account/session controls and avoids adding another page.

### Form Behavior

Clicking `修改密码` opens a compact form on the current page.

The form contains:

- `当前密码`
- `新密码`
- `确认新密码`
- `保存新密码`
- `取消`

Only one self-service password form should be visible per role at a time.

### Success Behavior

After saving successfully:

- keep the user logged in
- close the password form
- show: `密码已更新，下次登录请使用新密码`

This avoids interrupting the user’s current workflow.

### Error Behavior

Use clear plain-language messages:

- empty or mismatched new password: `新密码为空或两次输入不一致`
- invalid current password:
  - sales: existing repository error can remain user-facing
  - admin: use the same meaning, e.g. `当前密码不正确`

## Data and Implementation Decisions

### Sales Users

Reuse the existing `change_sales_password(...)` repository function.

The current first-login password form should continue to work unchanged.

### Admin Users

Add a matching repository function:

- `change_admin_password(session, admin_user_id, old_password, new_password)`

It should:

- load the admin user by id
- reject missing users
- verify the old password
- hash and save the new password
- commit and refresh the admin user

### UI State

Use separate session-state flags:

- sales password form visibility
- admin password form visibility

The cancel button should hide the form without modifying the password.

## Testing

Add tests for:

- admin repository password change succeeds with the old password and allows login with the new password
- admin repository password change rejects an invalid old password
- sales logged-in page exposes `修改密码`
- sales can change password from the logged-in workspace
- admin logged-in page exposes `修改密码`
- admin can change password from the logged-in workspace

## Summary

This feature closes a basic account-management gap while keeping the UI small and predictable.

It gives each user control over their own password without adding complex reset workflows or expanding admin permissions.
