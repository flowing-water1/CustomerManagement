from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from customer_management.db import Base


class TimestampMixin:
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AdminUser(TimestampMixin, Base):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SalesUser(TimestampMixin, Base):
    __tablename__ = "sales_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    must_change_password: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )


class CustomerRecord(TimestampMixin, Base):
    __tablename__ = "customer_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sales_user_id: Mapped[int] = mapped_column(
        ForeignKey("sales_users.id", ondelete="CASCADE"), nullable=False
    )
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    contact_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    remark: Mapped[str] = mapped_column(Text, default="", nullable=False)


class TagGroup(TimestampMixin, Base):
    __tablename__ = "tag_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    selection_mode: Mapped[str] = mapped_column(String(20), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class TagOption(TimestampMixin, Base):
    __tablename__ = "tag_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("tag_groups.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class RecordTag(Base):
    __tablename__ = "record_tags"
    __table_args__ = (UniqueConstraint("record_id", "option_id", name="uq_record_tag"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    record_id: Mapped[int] = mapped_column(
        ForeignKey("customer_records.id", ondelete="CASCADE"), nullable=False
    )
    group_id: Mapped[int] = mapped_column(
        ForeignKey("tag_groups.id", ondelete="CASCADE"), nullable=False
    )
    option_id: Mapped[int] = mapped_column(
        ForeignKey("tag_options.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CustomField(TimestampMixin, Base):
    __tablename__ = "custom_fields"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    field_type: Mapped[str] = mapped_column(String(30), nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class CustomFieldOption(Base):
    __tablename__ = "custom_field_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    field_id: Mapped[int] = mapped_column(
        ForeignKey("custom_fields.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class RecordFieldValue(TimestampMixin, Base):
    __tablename__ = "record_field_values"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    record_id: Mapped[int] = mapped_column(
        ForeignKey("customer_records.id", ondelete="CASCADE"), nullable=False
    )
    field_id: Mapped[int] = mapped_column(
        ForeignKey("custom_fields.id", ondelete="CASCADE"), nullable=False
    )
    value_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
