from typing import Optional

from sqlalchemy import or_

from customer_management.models import (
    CustomerRecord,
    RecordFieldValue,
    RecordTag,
    TagOption,
)


def create_record(
    session,
    *,
    sales_user_id: int,
    customer_name: str,
    contact_name: str,
    phone: str,
    remark: str,
    selected_option_ids: list,
    custom_field_values: dict,
):
    record = CustomerRecord(
        sales_user_id=sales_user_id,
        customer_name=customer_name,
        contact_name=contact_name,
        phone=phone,
        remark=remark,
    )
    session.add(record)
    session.flush()
    _replace_record_tags(session, record.id, selected_option_ids)
    _replace_record_field_values(session, record.id, custom_field_values)
    session.commit()
    session.refresh(record)
    return record


def list_records_for_sales_user(session, sales_user_id: int, query: Optional[str] = None):
    statement = session.query(CustomerRecord).filter(
        CustomerRecord.sales_user_id == sales_user_id
    )
    if query:
        like_value = f"%{query}%"
        statement = statement.filter(
            or_(
                CustomerRecord.customer_name.like(like_value),
                CustomerRecord.contact_name.like(like_value),
                CustomerRecord.phone.like(like_value),
            )
        )
    return statement.order_by(CustomerRecord.updated_at.desc()).all()


def update_record(
    session,
    *,
    record_id: int,
    sales_user_id: int,
    customer_name: str,
    contact_name: str,
    phone: str,
    remark: str,
    selected_option_ids: list,
    custom_field_values: dict,
):
    record = _get_owned_record(session, record_id, sales_user_id)
    record.customer_name = customer_name
    record.contact_name = contact_name
    record.phone = phone
    record.remark = remark
    _replace_record_tags(session, record.id, selected_option_ids)
    _replace_record_field_values(session, record.id, custom_field_values)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def get_record_details(session, *, record_id: int, sales_user_id: int):
    record = _get_owned_record(session, record_id, sales_user_id)
    selected_option_ids = [
        item.option_id
        for item in session.query(RecordTag)
        .filter(RecordTag.record_id == record.id)
        .all()
    ]
    custom_field_values = {
        item.field_id: item.value_text
        for item in session.query(RecordFieldValue)
        .filter(RecordFieldValue.record_id == record.id)
        .all()
    }
    return {
        "record": record,
        "selected_option_ids": selected_option_ids,
        "custom_field_values": custom_field_values,
    }


def delete_record(session, *, record_id: int, sales_user_id: int):
    record = _get_owned_record(session, record_id, sales_user_id)
    session.delete(record)
    session.commit()


def _get_owned_record(session, record_id: int, sales_user_id: int):
    record = session.get(CustomerRecord, record_id)
    if record is None or record.sales_user_id != sales_user_id:
        raise ValueError("Record not found")
    return record


def _replace_record_tags(session, record_id: int, selected_option_ids: list):
    session.query(RecordTag).filter(RecordTag.record_id == record_id).delete()
    if not selected_option_ids:
        return

    options = (
        session.query(TagOption).filter(TagOption.id.in_(selected_option_ids)).all()
    )
    for option in options:
        session.add(
            RecordTag(record_id=record_id, group_id=option.group_id, option_id=option.id)
        )


def _replace_record_field_values(session, record_id: int, custom_field_values: dict):
    session.query(RecordFieldValue).filter(
        RecordFieldValue.record_id == record_id
    ).delete()
    for field_id, value in custom_field_values.items():
        if value is None or value == "":
            continue
        session.add(
            RecordFieldValue(
                record_id=record_id,
                field_id=int(field_id),
                value_text=str(value),
            )
        )
