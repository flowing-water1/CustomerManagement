from customer_management.services.dashboard import build_dashboard_snapshot


def test_build_dashboard_snapshot_returns_totals_rankings_and_distributions(
    db_session, dashboard_seed_data
):
    snapshot = build_dashboard_snapshot(db_session)

    assert snapshot.total_records == 3
    assert snapshot.sales_rankings[0].count >= snapshot.sales_rankings[-1].count
    assert any(item.group_code == "customer_type" for item in snapshot.tag_distributions)
    assert {item.label: item.count for item in snapshot.customer_level_distribution} == {
        "一般": 2,
        "重要": 1,
    }
    assert {item.label: item.count for item in snapshot.customer_type_distribution} == {
        "已成交": 2,
        "未成交": 1,
    }
    assert not hasattr(snapshot, "cross_statistics")
