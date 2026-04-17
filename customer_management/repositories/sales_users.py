from typing import Optional

from customer_management.models import SalesUser
from customer_management.security import hash_password, verify_password


def create_sales_user(
    session,
    *,
    name: str,
    password: str,
    must_change_password: bool = True,
    is_active: bool = True,
    is_test_user: bool = False,
):
    sales_user = SalesUser(
        name=name,
        password_hash=hash_password(password),
        is_active=is_active,
        is_test_user=is_test_user,
        must_change_password=must_change_password,
    )
    session.add(sales_user)
    session.commit()
    session.refresh(sales_user)
    return sales_user


def list_active_sales_users(session, *, is_test_user: Optional[bool] = None):
    query = session.query(SalesUser).filter(SalesUser.is_active.is_(True))
    query = _apply_test_user_filter(query, is_test_user=is_test_user)
    return query.order_by(SalesUser.name.asc()).all()


def list_sales_users(session, *, is_test_user: Optional[bool] = None):
    query = session.query(SalesUser)
    query = _apply_test_user_filter(query, is_test_user=is_test_user)
    return query.order_by(SalesUser.name.asc()).all()


def get_sales_user_by_id(session, sales_user_id: int):
    return session.get(SalesUser, sales_user_id)


def authenticate_sales_user(
    session, name: str, password: str, *, is_test_user: Optional[bool] = None
):
    query = session.query(SalesUser).filter(
        SalesUser.name == name, SalesUser.is_active.is_(True)
    )
    query = _apply_test_user_filter(query, is_test_user=is_test_user)
    sales_user = query.one_or_none()
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


def set_sales_user_active(session, sales_user_id: int, is_active: bool):
    sales_user = session.get(SalesUser, sales_user_id)
    if sales_user is None:
        raise ValueError("Sales user not found")
    sales_user.is_active = is_active
    session.add(sales_user)
    session.commit()
    session.refresh(sales_user)
    return sales_user


def set_sales_user_test_flag(session, sales_user_id: int, is_test_user: bool):
    sales_user = session.get(SalesUser, sales_user_id)
    if sales_user is None:
        raise ValueError("Sales user not found")
    sales_user.is_test_user = is_test_user
    session.add(sales_user)
    session.commit()
    session.refresh(sales_user)
    return sales_user


def _apply_test_user_filter(query, *, is_test_user: Optional[bool]):
    if is_test_user is None:
        return query
    return query.filter(SalesUser.is_test_user.is_(is_test_user))
