from customer_management.models import SalesUser
from customer_management.security import hash_password, verify_password


def create_sales_user(
    session,
    *,
    name: str,
    password: str,
    must_change_password: bool = True,
    is_active: bool = True,
):
    sales_user = SalesUser(
        name=name,
        password_hash=hash_password(password),
        is_active=is_active,
        must_change_password=must_change_password,
    )
    session.add(sales_user)
    session.commit()
    session.refresh(sales_user)
    return sales_user


def list_active_sales_users(session):
    return (
        session.query(SalesUser)
        .filter(SalesUser.is_active.is_(True))
        .order_by(SalesUser.name.asc())
        .all()
    )


def get_sales_user_by_id(session, sales_user_id: int):
    return session.get(SalesUser, sales_user_id)


def authenticate_sales_user(session, name: str, password: str):
    sales_user = (
        session.query(SalesUser)
        .filter(SalesUser.name == name, SalesUser.is_active.is_(True))
        .one_or_none()
    )
    if sales_user is None:
        return None
    if not verify_password(password, sales_user.password_hash):
        return None
    return sales_user


def change_sales_password(session, sales_user_id: int, old_password: str, new_password: str):
    sales_user = session.get(SalesUser, sales_user_id)
    if sales_user is None:
        raise ValueError("Sales user not found")
    if not verify_password(old_password, sales_user.password_hash):
        raise ValueError("Old password is invalid")
    sales_user.password_hash = hash_password(new_password)
    sales_user.must_change_password = False
    session.add(sales_user)
    session.commit()
    session.refresh(sales_user)
    return sales_user
