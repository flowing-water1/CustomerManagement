from customer_management.models import AdminUser
from customer_management.security import hash_password, verify_password


def create_admin_user(
    session,
    *,
    username: str,
    password: str,
    display_name: str,
    is_active: bool = True,
):
    admin_user = AdminUser(
        username=username.strip(),
        password_hash=hash_password(password),
        display_name=display_name.strip(),
        is_active=is_active,
    )
    session.add(admin_user)
    session.commit()
    session.refresh(admin_user)
    return admin_user


def authenticate_admin_user(session, username: str, password: str):
    admin_user = (
        session.query(AdminUser)
        .filter(AdminUser.username == username.strip(), AdminUser.is_active.is_(True))
        .one_or_none()
    )
    if admin_user is None:
        return None
    if not verify_password(password, admin_user.password_hash):
        return None
    return admin_user


def list_admin_users(session):
    return session.query(AdminUser).order_by(AdminUser.username.asc()).all()


def get_admin_user_by_id(session, admin_user_id: int):
    return session.get(AdminUser, admin_user_id)


def set_admin_user_active(session, admin_user_id: int, is_active: bool):
    admin_user = session.get(AdminUser, admin_user_id)
    if admin_user is None:
        raise ValueError("Admin user not found")
    admin_user.is_active = is_active
    session.add(admin_user)
    session.commit()
    session.refresh(admin_user)
    return admin_user
