from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func

from customer_management.models import (
    CustomerRecord,
    RecordTag,
    SalesUser,
    TagGroup,
    TagOption,
)


@dataclass
class CountItem:
    label: str
    count: int


@dataclass
class TrendPoint:
    bucket: str
    count: int


@dataclass
class TagDistributionItem:
    group_code: str
    group_name: str
    option_label: str
    count: int


@dataclass
class DistributionItem:
    label: str
    count: int


@dataclass
class DashboardSnapshot:
    total_records: int
    records_today: int
    records_this_week: int
    records_this_month: int
    active_sales_count: int
    trend_points: list = field(default_factory=list)
    sales_rankings: list = field(default_factory=list)
    tag_distributions: list = field(default_factory=list)
    customer_level_distribution: list = field(default_factory=list)
    customer_type_distribution: list = field(default_factory=list)


def _build_dashboard_snapshot(session, *, is_test_user: Optional[bool]) -> DashboardSnapshot:
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = datetime(now.year, now.month, 1)

    record_query = _build_record_query(session, is_test_user=is_test_user)

    total_records = record_query.count()
    records_today = (
        _build_record_query(session, is_test_user=is_test_user)
        .filter(CustomerRecord.created_at >= today_start)
        .count()
    )
    records_this_week = (
        _build_record_query(session, is_test_user=is_test_user)
        .filter(CustomerRecord.created_at >= week_start)
        .count()
    )
    records_this_month = (
        _build_record_query(session, is_test_user=is_test_user)
        .filter(CustomerRecord.created_at >= month_start)
        .count()
    )
    active_sales_count = (
        _build_record_query(session, is_test_user=is_test_user)
        .with_entities(func.count(func.distinct(CustomerRecord.sales_user_id)))
        .scalar()
        or 0
    )

    trend_rows = (
        _build_record_query(session, is_test_user=is_test_user)
        .with_entities(func.date(CustomerRecord.created_at), func.count(CustomerRecord.id))
        .group_by(func.date(CustomerRecord.created_at))
        .order_by(func.date(CustomerRecord.created_at))
        .all()
    )
    trend_points = [TrendPoint(bucket=str(bucket), count=count) for bucket, count in trend_rows]

    ranking_rows = (
        session.query(SalesUser.name, func.count(CustomerRecord.id))
        .join(CustomerRecord, CustomerRecord.sales_user_id == SalesUser.id)
        .filter(*_build_test_user_filters(is_test_user=is_test_user))
        .group_by(SalesUser.name)
        .order_by(func.count(CustomerRecord.id).desc(), SalesUser.name.asc())
        .all()
    )
    sales_rankings = [CountItem(label=label, count=count) for label, count in ranking_rows]

    distribution_rows = (
        session.query(TagGroup.code, TagGroup.name, TagOption.label, func.count(RecordTag.id))
        .join(TagOption, TagOption.group_id == TagGroup.id)
        .join(RecordTag, RecordTag.option_id == TagOption.id)
        .join(CustomerRecord, CustomerRecord.id == RecordTag.record_id)
        .join(SalesUser, SalesUser.id == CustomerRecord.sales_user_id)
        .filter(*_build_test_user_filters(is_test_user=is_test_user))
        .group_by(TagGroup.code, TagGroup.name, TagOption.label)
        .order_by(TagGroup.code.asc(), func.count(RecordTag.id).desc())
        .all()
    )
    tag_distributions = [
        TagDistributionItem(
            group_code=group_code,
            group_name=group_name,
            option_label=option_label,
            count=count,
        )
        for group_code, group_name, option_label, count in distribution_rows
    ]
    customer_level_distribution = _build_distribution(
        session,
        "customer_level",
        is_test_user=is_test_user,
    )
    customer_type_distribution = _build_distribution(
        session,
        "customer_type",
        is_test_user=is_test_user,
    )

    return DashboardSnapshot(
        total_records=total_records,
        records_today=records_today,
        records_this_week=records_this_week,
        records_this_month=records_this_month,
        active_sales_count=active_sales_count,
        trend_points=trend_points,
        sales_rankings=sales_rankings,
        tag_distributions=tag_distributions,
        customer_level_distribution=customer_level_distribution,
        customer_type_distribution=customer_type_distribution,
    )


def list_admin_records(
    session,
    *,
    sales_user_id: Optional[int] = None,
    tag_option_id: Optional[int] = None,
    start_date=None,
    end_date=None,
    is_test_user: Optional[bool] = None,
):
    query = (
        session.query(CustomerRecord, SalesUser.name)
        .join(SalesUser, SalesUser.id == CustomerRecord.sales_user_id)
        .filter(*_build_test_user_filters(is_test_user=is_test_user))
        .order_by(CustomerRecord.updated_at.desc())
    )
    if sales_user_id is not None:
        query = query.filter(CustomerRecord.sales_user_id == sales_user_id)
    if start_date is not None:
        query = query.filter(CustomerRecord.created_at >= start_date)
    if end_date is not None:
        query = query.filter(CustomerRecord.created_at <= end_date)
    if tag_option_id is not None:
        query = query.join(RecordTag, RecordTag.record_id == CustomerRecord.id).filter(
            RecordTag.option_id == tag_option_id
        )
    return [
        {
            "id": record.id,
            "sales_name": sales_name,
            "customer_name": record.customer_name,
            "contact_name": record.contact_name,
            "phone": record.phone,
            "remark": record.remark,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        }
        for record, sales_name in query.all()
    ]


def _build_distribution(session, group_code: str, *, is_test_user: Optional[bool]):
    rows = (
        session.query(TagOption.label, func.count(RecordTag.id))
        .join(TagGroup, TagGroup.id == TagOption.group_id)
        .join(RecordTag, RecordTag.option_id == TagOption.id)
        .join(CustomerRecord, CustomerRecord.id == RecordTag.record_id)
        .join(SalesUser, SalesUser.id == CustomerRecord.sales_user_id)
        .filter(TagGroup.code == group_code)
        .filter(*_build_test_user_filters(is_test_user=is_test_user))
        .group_by(TagOption.label)
        .order_by(func.count(RecordTag.id).desc(), TagOption.label.asc())
        .all()
    )
    return [DistributionItem(label=label, count=count) for label, count in rows]


def build_dashboard_snapshot(
    session, *, is_test_user: Optional[bool] = None
) -> DashboardSnapshot:
    return _build_dashboard_snapshot(session, is_test_user=is_test_user)


def _build_record_query(session, *, is_test_user: Optional[bool]):
    query = session.query(CustomerRecord)
    if is_test_user is None:
        return query
    return query.join(SalesUser, SalesUser.id == CustomerRecord.sales_user_id).filter(
        SalesUser.is_test_user.is_(is_test_user)
    )


def _build_test_user_filters(*, is_test_user: Optional[bool]):
    if is_test_user is None:
        return ()
    return (SalesUser.is_test_user.is_(is_test_user),)
