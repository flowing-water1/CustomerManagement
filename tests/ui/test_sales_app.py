from pathlib import Path

from streamlit.testing.v1 import AppTest

from customer_management.bootstrap import create_schema, seed_default_metadata
from customer_management.db import make_engine, make_session_factory
from customer_management.repositories.records import create_record
from customer_management.repositories.metadata import create_custom_field
from customer_management.repositories.sales_users import create_sales_user


def test_sales_login_page_shows_name_selector(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")

    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run()

    assert any(widget.label == "选择销售姓名" for widget in app.selectbox)


def test_sales_user_can_log_in_create_record_and_see_it_in_list(tmp_path, monkeypatch):
    database_path = tmp_path / "sales-app.db"
    database_url = f"sqlite:///{database_path.as_posix()}"

    engine = make_engine(database_url)
    create_schema(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        seed_default_metadata(session)
        create_sales_user(
            session,
            name="Alice",
            password="next-pass",
            must_change_password=False,
        )

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")

    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run()

    app.selectbox(key="sales_user_name").select("Alice")
    app.text_input(key="sales_password").input("next-pass")
    next(button for button in app.button if button.label == "销售登录").click()
    app.run()

    app.text_input(key="customer_name").input("ACME")
    app.text_input(key="contact_name").input("Bob")
    app.text_input(key="phone").input("13800000000")
    next(button for button in app.button if button.label == "保存记录").click()
    app.run()

    assert "ACME" in app.dataframe[0].value.to_string()


def test_sales_page_renders_number_custom_field_without_state_errors(
    tmp_path, monkeypatch
):
    database_path = tmp_path / "sales-number-field.db"
    database_url = f"sqlite:///{database_path.as_posix()}"

    engine = make_engine(database_url)
    create_schema(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        seed_default_metadata(session)
        create_sales_user(
            session,
            name="Alice",
            password="next-pass",
            must_change_password=False,
        )
        create_custom_field(
            session,
            name="测试",
            field_type="number",
            is_required=False,
        )

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")

    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run()

    app.selectbox(key="sales_user_name").select("Alice")
    app.text_input(key="sales_password").input("next-pass")
    next(button for button in app.button if button.label == "销售登录").click()
    app.run()

    assert len(app.exception) == 0
    assert any(widget.key == "custom_field_custom_field" for widget in app.number_input)


def test_sales_user_can_start_new_record_from_record_actions(tmp_path, monkeypatch):
    database_path = tmp_path / "sales-edit-new.db"
    database_url = f"sqlite:///{database_path.as_posix()}"

    engine = make_engine(database_url)
    create_schema(engine)
    session_factory = make_session_factory(engine)
    with session_factory() as session:
        seed_default_metadata(session)
        sales_user = create_sales_user(
            session,
            name="Alice",
            password="next-pass",
            must_change_password=False,
        )
        create_record(
            session,
            sales_user_id=sales_user.id,
            customer_name="测试客户123",
            contact_name="123",
            phone="13712199955",
            remark="测试备注",
            selected_option_ids=[],
            custom_field_values={},
        )

    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("APP_SECRET_KEY", "dev-secret")

    app = AppTest.from_file(str(Path(__file__).resolve().parents[2] / "app.py"))
    app.run()

    app.selectbox(key="sales_user_name").select("Alice")
    app.text_input(key="sales_password").input("next-pass")
    next(button for button in app.button if button.label == "销售登录").click()
    app.run()

    assert any(button.label == "新建记录" for button in app.button)

    next(button for button in app.button if button.label == "加载编辑").click()
    app.run()

    assert any("当前正在编辑记录" in widget.value for widget in app.caption)

    next(button for button in app.button if button.label == "新建记录").click()
    app.run()

    assert not any("当前正在编辑记录" in widget.value for widget in app.caption)
    assert app.text_input(key="customer_name").value == ""
    assert app.text_input(key="contact_name").value == ""
    assert app.text_input(key="phone").value == ""
