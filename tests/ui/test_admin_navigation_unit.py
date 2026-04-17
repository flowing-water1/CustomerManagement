from types import SimpleNamespace

import customer_management.ui.admin as admin_ui


class _DummyContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_admin_workspace_only_renders_selected_page(monkeypatch):
    called = []

    monkeypatch.setattr(admin_ui.st, "caption", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        admin_ui.st,
        "columns",
        lambda spec: tuple(_DummyContext() for _ in range(spec if isinstance(spec, int) else len(spec))),
    )
    monkeypatch.setattr(admin_ui.st, "button", lambda *args, **kwargs: False)
    monkeypatch.setattr(
        admin_ui.st,
        "radio",
        lambda *args, **kwargs: "客户资料配置",
    )
    monkeypatch.setattr(admin_ui.st, "session_state", {}, raising=False)
    monkeypatch.setattr(admin_ui.st, "rerun", lambda: None)

    monkeypatch.setattr(
        admin_ui,
        "_render_dashboard_overview",
        lambda session: called.append("overview"),
    )
    monkeypatch.setattr(
        admin_ui,
        "_render_records_overview",
        lambda session: called.append("records"),
    )
    monkeypatch.setattr(
        admin_ui,
        "_render_sales_management",
        lambda session: called.append("sales"),
    )
    monkeypatch.setattr(
        admin_ui,
        "_render_admin_management",
        lambda session, admin_id: called.append("admins"),
    )
    monkeypatch.setattr(
        admin_ui,
        "render_customer_config",
        lambda session: called.append("customer_config"),
    )

    admin_ui._render_workspace(None, SimpleNamespace(id=1, display_name="HR"))

    assert called == ["customer_config"]
