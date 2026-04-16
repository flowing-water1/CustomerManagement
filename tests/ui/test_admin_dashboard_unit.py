from types import SimpleNamespace

import customer_management.ui.admin as admin_ui


class _DummyContext:
    def metric(self, *args, **kwargs):
        return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_dashboard_overview_renders_titled_charts_without_cross_statistics(monkeypatch):
    markdowns = []
    altair_calls = []
    dataframe_calls = []
    expander_calls = []

    snapshot = SimpleNamespace(
        total_records=3,
        records_today=1,
        records_this_week=3,
        records_this_month=3,
        active_sales_count=2,
        trend_points=[SimpleNamespace(bucket="2026-04-16", count=1)],
        sales_rankings=[SimpleNamespace(label="Alice", count=2)],
        tag_distributions=[
            SimpleNamespace(group_name="客户类型", option_label="已成交", count=2),
        ],
        customer_level_distribution=[
            SimpleNamespace(label="一般", count=2),
            SimpleNamespace(label="重要", count=1),
        ],
        customer_type_distribution=[
            SimpleNamespace(label="已成交", count=2),
            SimpleNamespace(label="未成交", count=1),
        ],
    )

    monkeypatch.setattr(admin_ui, "build_dashboard_snapshot", lambda session: snapshot)
    monkeypatch.setattr(
        admin_ui.st,
        "columns",
        lambda spec: [_DummyContext() for _ in range(spec if isinstance(spec, int) else len(spec))],
    )
    monkeypatch.setattr(admin_ui.st, "markdown", lambda value, **kwargs: markdowns.append(value))
    monkeypatch.setattr(admin_ui.st, "line_chart", lambda *args, **kwargs: None)
    monkeypatch.setattr(admin_ui.st, "bar_chart", lambda *args, **kwargs: None)
    monkeypatch.setattr(admin_ui.st, "altair_chart", lambda *args, **kwargs: altair_calls.append(args))
    monkeypatch.setattr(admin_ui.st, "dataframe", lambda *args, **kwargs: dataframe_calls.append(args))
    monkeypatch.setattr(admin_ui.st, "metric", lambda *args, **kwargs: None)
    monkeypatch.setattr(admin_ui.st, "info", lambda *args, **kwargs: None)
    monkeypatch.setattr(admin_ui.st, "expander", lambda *args, **kwargs: expander_calls.append(args))

    admin_ui._render_dashboard_overview(None)

    assert any("新增客户记录趋势" in value for value in markdowns)
    assert any("各销售提交客户数" in value for value in markdowns)
    assert any("客户等级分布" in value for value in markdowns)
    assert any("已成交 / 未成交占比" in value for value in markdowns)
    assert any("各标签使用情况" in value for value in markdowns)
    assert len(altair_calls) == 2
    assert len(dataframe_calls) == 1
    assert expander_calls == []
