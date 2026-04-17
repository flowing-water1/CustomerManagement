from customer_management.repositories.sales_users import (
    authenticate_sales_user,
    change_sales_password,
    create_sales_user,
    list_active_sales_users,
    list_sales_users,
    set_sales_user_test_flag,
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


def test_sales_user_lists_can_exclude_test_users(db_session):
    create_sales_user(
        db_session,
        name="Alice",
        password="alice-pass",
        must_change_password=False,
    )
    create_sales_user(
        db_session,
        name="Tester",
        password="tester-pass",
        must_change_password=False,
        is_test_user=True,
    )

    assert {user.name for user in list_sales_users(db_session)} == {"Alice", "Tester"}
    assert {user.name for user in list_sales_users(db_session, is_test_user=False)} == {
        "Alice"
    }
    assert {user.name for user in list_sales_users(db_session, is_test_user=True)} == {
        "Tester"
    }
    assert {
        user.name for user in list_active_sales_users(db_session, is_test_user=False)
    } == {"Alice"}
    assert {
        user.name for user in list_active_sales_users(db_session, is_test_user=True)
    } == {"Tester"}


def test_sales_user_can_be_marked_as_test_user(db_session):
    sales_user = create_sales_user(
        db_session,
        name="Alice",
        password="alice-pass",
        must_change_password=False,
    )

    updated_user = set_sales_user_test_flag(db_session, sales_user.id, True)

    assert updated_user.is_test_user is True
