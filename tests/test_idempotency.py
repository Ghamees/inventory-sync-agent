from agent.action_ledger import (
    create_conflict_id,
    has_been_handled,
    initialise_ledger,
    record_action,
)


def test_same_conflict_is_not_handled_twice(tmp_path, monkeypatch):
    from agent import action_ledger

    test_db = tmp_path / "test_agent.db"
    monkeypatch.setattr(action_ledger, "DB_PATH", test_db)

    initialise_ledger()

    conflict = {
        "sku": "SKU-100",
        "warehouse_quantities": {
            "warehouse_a": 15,
            "warehouse_b": 15,
            "warehouse_c": 18,
        },
        "type": "quantity_mismatch",
    }

    conflict_id = create_conflict_id(conflict)

    assert has_been_handled(conflict_id) is False

    record_action(
        conflict_id=conflict_id,
        sku="SKU-100",
        action="adjust_stock",
        details={"target_quantity": 15},
    )

    assert has_been_handled(conflict_id) is True