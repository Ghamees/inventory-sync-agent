from agent.decision_engine import decide_action


def test_majority_consensus_adjusts_outlier():
    conflict = {
        "sku": "SKU-100",
        "warehouse_quantities": {
            "warehouse_a": 15,
            "warehouse_b": 15,
            "warehouse_c": 18,
        },
        "type": "quantity_mismatch",
    }

    decision = decide_action(conflict)

    assert decision["action"] == "adjust_stock"
    assert decision["target_quantity"] == 15
    assert decision["target_warehouses"] == ["warehouse_c"]


def test_no_consensus_triggers_recount():
    conflict = {
        "sku": "SKU-200",
        "warehouse_quantities": {
            "warehouse_a": 10,
            "warehouse_b": 12,
            "warehouse_c": 14,
        },
        "type": "quantity_mismatch",
    }

    decision = decide_action(conflict)

    assert decision["action"] == "trigger_recount"
    assert decision["target_quantity"] is None
    assert decision["target_warehouses"] == [
        "warehouse_a",
        "warehouse_b",
        "warehouse_c",
    ]
    