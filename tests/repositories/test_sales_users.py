from customer_management.repositories.sales_users import (
    authenticate_sales_user,
    change_sales_password,
    create_sales_user,
)


def test_sales_user_auth_and_password_change(db_session):
    sales_user = create_sales_user(
        db_session,
        name="Alice",
        password="temp-pass",
        must_change_password=True,
    )

    authenticated = authenticate_sales_user(db_session, "Alice", "temp-pass")

    assert authenticated.id == sales_user.id
    assert authenticated.must_change_password is True

    change_sales_password(db_session, sales_user.id, "temp-pass", "next-pass")

    reauthenticated = authenticate_sales_user(db_session, "Alice", "next-pass")
    assert reauthenticated.must_change_password is False
