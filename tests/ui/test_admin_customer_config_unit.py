from types import SimpleNamespace

import customer_management.ui.admin_customer_config as admin_customer_config


class _DummyContext:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _fail_on_rerun():
    raise AssertionError("st.rerun should not be called")


def test_summary_focus_button_does_not_force_rerun(monkeypatch):
    snapshot = SimpleNamespace(
        summary_title="当前配置情况",
        tag_rows=[
            SimpleNamespace(code="brand", name="品牌", items=[], subtitle=""),
        ],
        field_rows=[],
    )

    monkeypatch.setattr(admin_customer_config.st, "markdown", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        admin_customer_config.st,
        "columns",
        lambda spec: (_DummyContext(), _DummyContext()),
    )
    monkeypatch.setattr(
        admin_customer_config.st,
        "button",
        lambda *args, **kwargs: kwargs.get("key") == "admin_summary_focus_tag_brand",
    )
    monkeypatch.setattr(admin_customer_config, "_set_focus", lambda *args, **kwargs: None)
    monkeypatch.setattr(admin_customer_config, "_is_focused", lambda *args, **kwargs: False)
    monkeypatch.setattr(admin_customer_config.st, "rerun", _fail_on_rerun)

    admin_customer_config._render_summary_card(None, snapshot)


def test_quick_tag_submit_does_not_force_rerun(monkeypatch):
    row = SimpleNamespace(id=1, code="brand", name="品牌", items=[])
    created = []

    monkeypatch.setattr(admin_customer_config.st, "markdown", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        admin_customer_config.st,
        "form",
        lambda *args, **kwargs: _DummyContext(),
    )
    monkeypatch.setattr(admin_customer_config.st, "text_input", lambda *args, **kwargs: None)
    monkeypatch.setattr(admin_customer_config.st, "form_submit_button", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        admin_customer_config.st,
        "session_state",
        {"admin_quick_tag_option_label_brand": "VIP"},
        raising=False,
    )
    monkeypatch.setattr(
        admin_customer_config,
        "create_tag_option",
        lambda session, group_id, label: created.append((group_id, label)),
    )
    monkeypatch.setattr(admin_customer_config, "list_tag_options", lambda *args, **kwargs: [])
    monkeypatch.setattr(admin_customer_config.st, "rerun", _fail_on_rerun)

    admin_customer_config._render_tag_quick_edit(None, row)

    assert created == [(1, "VIP")]
