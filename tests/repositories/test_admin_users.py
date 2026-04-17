from customer_management.repositories.admin_users import (
    authenticate_admin_user,
    change_admin_password,
    create_admin_user,
    delete_admin_user,
    get_admin_user_by_id,
    set_admin_user_active,
)


def test_admin_user_auth_and_password_change(db_session):
    admin_user = create_admin_user(
        db_session,
        username="hr-admin",
        password="temp-pass",
        display_name="HR",
    )

    authenticated = authenticate_admin_user(db_session, "hr-admin", "temp-pass")

    assert authenticated.id == admin_user.id

    change_admin_password(db_session, admin_user.id, "temp-pass", "next-pass")

    reauthenticated = authenticate_admin_user(db_session, "hr-admin", "next-pass")
    assert reauthenticated.id == admin_user.id


def test_admin_password_change_rejects_invalid_old_password(db_session):
    admin_user = create_admin_user(
        db_session,
        username="hr-admin",
        password="temp-pass",
        display_name="HR",
    )

    try:
        change_admin_password(db_session, admin_user.id, "wrong-pass", "next-pass")
    except ValueError as exc:
        assert str(exc) == "Old password is invalid"
    else:
        raise AssertionError("Expected ValueError for invalid old password")


def test_admin_user_can_be_deleted(db_session):
    admin_user = create_admin_user(
        db_session,
        username="ops-admin",
        password="temp-pass",
        display_name="OPS",
    )

    delete_admin_user(db_session, admin_user.id)

    assert get_admin_user_by_id(db_session, admin_user.id) is None
    assert authenticate_admin_user(db_session, "ops-admin", "temp-pass") is None


def test_core_admin_user_cannot_be_deleted(db_session):
    admin_user = create_admin_user(
        db_session,
        username="admin",
        password="temp-pass",
        display_name="Admin",
    )

    try:
        delete_admin_user(db_session, admin_user.id)
    except ValueError as exc:
        assert str(exc) == "Core admin user cannot be deleted"
    else:
        raise AssertionError("Expected ValueError for core admin deletion")

    assert get_admin_user_by_id(db_session, admin_user.id) is not None


def test_core_admin_user_cannot_be_deactivated(db_session):
    admin_user = create_admin_user(
        db_session,
        username="admin",
        password="temp-pass",
        display_name="Admin",
    )

    try:
        set_admin_user_active(db_session, admin_user.id, False)
    except ValueError as exc:
        assert str(exc) == "Core admin user cannot be deactivated"
    else:
        raise AssertionError("Expected ValueError for core admin deactivation")

    assert get_admin_user_by_id(db_session, admin_user.id).is_active is True
