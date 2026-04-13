from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_sales_login_page_shows_name_selector(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")

    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run()

    assert any(widget.label == "选择销售姓名" for widget in app.selectbox)
