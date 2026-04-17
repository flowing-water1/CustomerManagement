# Deployment Hardening Design

## Overview

This document defines a small deployment-hardening pass for the existing Streamlit customer management app before publishing to GitHub and deploying on Streamlit Community Cloud.

The goal is to remove environment-specific surprises without changing product behavior for admins or sales users, while keeping runtime setup simple and obvious.

## Confirmed Scope

### Included

- unify PostgreSQL driver handling around `psycopg`
- support configuration from both Streamlit secrets and local environment variables
- keep local `.env` setup working for development
- initialize schema and default metadata automatically on app startup
- add a checked-in secrets example file for local and cloud setup guidance
- improve `.gitignore` so local IDE and scratch files are less likely to be pushed accidentally

### Excluded

- database migrations framework adoption
- auth/session redesign
- UI redesign
- production observability or logging changes
- refactoring unrelated repository or service code

## Key Decisions

### Configuration Source Order

The app should accept configuration from both Streamlit secrets and environment variables.

When both are present, environment variables should win.

This keeps Streamlit Community Cloud deployment straightforward while preserving the current local workflow and making tests predictable:

- local development can still use `.env`
- Streamlit Cloud can use `.streamlit/secrets.toml`
- tests can inject explicit values without being overridden by a local secrets file

### PostgreSQL Driver Normalization

The app should normalize plain PostgreSQL URLs to SQLAlchemy's `psycopg` dialect instead of rewriting them to `psycopg2`.

This avoids the current mismatch where:

- `requirements.txt` installs `psycopg`
- runtime code rewrites URLs to `psycopg2`
- deployment works only if both drivers happen to be present

Accepted PostgreSQL inputs should become `postgresql+psycopg://...`:

- `postgresql://...`
- `postgres://...`
- already-correct `postgresql+psycopg://...` should remain unchanged

### Startup Bootstrap Policy

The app should continue to create tables and seed metadata on every startup.

This keeps setup simple for local development, tests, and first deployments:

- no extra bootstrap toggle
- no second config value to explain
- no extra manual initialization step before first run

## Implementation Shape

### Configuration Layer

Keep `Settings` focused on one required value:

- read `DATABASE_URL` from a provided secrets mapping plus environment mapping
- prefer environment variables when both sources exist

### Database Layer

Update database URL normalization to target `psycopg`, not `psycopg2`.

### App Startup Layer

Keep the cached session-factory builder eager so startup always initializes schema and default metadata.

### Documentation and Deployment Layer

Add:

- `.streamlit/secrets.toml.example`
- README instructions for local setup and Streamlit Cloud secrets
- simple single-setting deployment guidance

## Testing

Add or update tests for:

- config reading from environment
- config preferring environment values over Streamlit secrets
- config falling back cleanly when secrets are unavailable
- PostgreSQL URL normalization to `psycopg`
- startup session factory always bootstrapping schema and metadata

## Summary

This change keeps the product behavior stable while making deployment behavior simple, reproducible, and aligned with the dependencies declared in the repository.
