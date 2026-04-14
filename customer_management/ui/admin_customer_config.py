import streamlit as st

from customer_management.services.admin_metadata import build_customer_config_snapshot


def render_customer_config(session):
    snapshot = build_customer_config_snapshot(session)

    st.markdown("#### 客户资料配置")
    st.markdown(
        "这里展示销售当前会用到的客户分类和补充资料。你在这里修改后，销售录入页会同步变化。"
    )

    _render_summary_card(snapshot)
    _render_tag_section()
    _render_field_section(snapshot)


def _render_summary_card(snapshot):
    st.markdown(f"#### {snapshot.summary_title}")
    st.markdown("先看现在怎么配，再决定改哪里。")

    for row in snapshot.tag_rows:
        values = " / ".join(_format_items(row.items))
        st.markdown(f"**{row.name}**：{values}")

    if snapshot.field_rows:
        st.markdown(
            "**补充字段**："
            + " / ".join(field.name for field in snapshot.field_rows)
        )


def _render_tag_section():
    st.markdown("#### 标签区")
    st.markdown("标签用于给客户分类，方便销售选择，也方便后续筛选和统计。")


def _render_field_section(snapshot):
    st.markdown("#### 字段区")
    st.markdown("字段用于补充客户资料，比如采购周期、月需求量、下次回访时间。")
    st.markdown(
        "常见补充字段："
        + " / ".join(snapshot.field_helper_examples)
    )


def _format_items(items):
    formatted_items = []
    for item in items:
        label = item.label
        if not item.is_active:
            label = f"{label}（已停用）"
        formatted_items.append(label)
    return formatted_items
