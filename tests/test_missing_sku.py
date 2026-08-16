from agent.conflict_detector import detect_conflicts
from agent.decision_engine import decide_action


def test_missing_sku_triggers_manual_review():
    inventories = {
        "warehouse_a": {
            "SKU-100": 15,
            "SKU-300": 20,
        },
        "warehouse_b": {
            "SKU-100": 15,
            "SKU-300": 20,
        },
        "warehouse_c": {
            "SKU-100": 15,
        },
    }

    conflicts = detect_conflicts(inventories)

    missing_sku_conflicts = [
        conflict
        for conflict in conflicts
        if conflict["type"] == "missing_sku"
    ]

    assert len(missing_sku_conflicts) == 1

    conflict = missing_sku_conflicts[0]

    assert conflict["sku"] == "SKU-300"
    assert conflict["missing_warehouses"] == ["warehouse_c"]

    decision = decide_action(conflict)

    assert decision["action"] == "manual_review"
    assert decision["target_warehouses"] == ["warehouse_c"]