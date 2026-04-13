from customer_management.db import Base
from customer_management import models  # noqa: F401
from customer_management.models import TagGroup, TagOption


DEFAULT_TAG_GROUPS = [
    {
        "name": "客户等级",
        "code": "customer_level",
        "selection_mode": "single",
        "sort_order": 10,
        "options": [
            {"label": "一般", "value": "general", "sort_order": 10},
            {"label": "重要", "value": "important", "sort_order": 20},
        ],
    },
    {
        "name": "客户类型",
        "code": "customer_type",
        "selection_mode": "single",
        "sort_order": 20,
        "options": [
            {"label": "已成交", "value": "converted", "sort_order": 10},
            {"label": "未成交", "value": "not_converted", "sort_order": 20},
        ],
    },
    {
        "name": "品牌",
        "code": "brand",
        "selection_mode": "multiple",
        "sort_order": 30,
        "options": [
            {"label": "壳牌", "value": "shell", "sort_order": 10},
            {"label": "美孚", "value": "mobil", "sort_order": 20},
            {"label": "长城", "value": "greatwall", "sort_order": 30},
            {"label": "昆仑", "value": "kunlun", "sort_order": 40},
        ],
    },
    {
        "name": "油品",
        "code": "oil_type",
        "selection_mode": "multiple",
        "sort_order": 40,
        "options": [
            {"label": "工业油", "value": "industrial_oil", "sort_order": 10},
            {"label": "车油", "value": "vehicle_oil", "sort_order": 20},
        ],
    },
    {
        "name": "授权代理商",
        "code": "authorized_dealer",
        "selection_mode": "single",
        "sort_order": 50,
        "options": [
            {"label": "代理商", "value": "dealer", "sort_order": 10},
            {"label": "非代理商", "value": "non_dealer", "sort_order": 20},
        ],
    },
    {
        "name": "其他",
        "code": "other",
        "selection_mode": "multiple",
        "sort_order": 60,
        "options": [
            {"label": "其他国产", "value": "other_domestic", "sort_order": 10},
            {"label": "其他进口", "value": "other_imported", "sort_order": 20},
        ],
    },
]


def create_schema(engine) -> None:
    Base.metadata.create_all(engine)


def seed_default_metadata(session) -> None:
    for group_data in DEFAULT_TAG_GROUPS:
        group = (
            session.query(TagGroup)
            .filter(TagGroup.code == group_data["code"])
            .one_or_none()
        )
        if group is None:
            group = TagGroup(
                name=group_data["name"],
                code=group_data["code"],
                selection_mode=group_data["selection_mode"],
                sort_order=group_data["sort_order"],
                is_active=True,
            )
            session.add(group)
            session.flush()

        for option_data in group_data["options"]:
            option = (
                session.query(TagOption)
                .filter(
                    TagOption.group_id == group.id,
                    TagOption.value == option_data["value"],
                )
                .one_or_none()
            )
            if option is None:
                session.add(
                    TagOption(
                        group_id=group.id,
                        label=option_data["label"],
                        value=option_data["value"],
                        sort_order=option_data["sort_order"],
                        is_active=True,
                    )
                )

    session.commit()
