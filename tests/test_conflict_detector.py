from agent.conflict_detector import detect_conflicts


def test_matching_inventory_has_no_conflicts():
    inventories = {
        "warehouse_a": {
            "SKU-100": 15,
            "SKU-200": 8,
        },
        "warehouse_b": {
            "SKU-100": 15,
            "SKU-200": 8,
        },
        "warehouse_c": {
            "SKU-100": 15,
            "SKU-200": 8,
        },
    }

    conflicts = detect_conflicts(inventories)

    assert conflicts == []


def test_quantity_mismatch_is_detected():
    inventories = {
        "warehouse_a": {"SKU-100": 15},
        "warehouse_b": {"SKU-100": 15},
        "warehouse_c": {"SKU-100": 18},
    }

    conflicts = detect_conflicts(inventories)

    assert len(conflicts) == 1
    assert conflicts[0]["sku"] == "SKU-100"
    assert conflicts[0]["type"] == "quantity_mismatch"
    assert conflicts[0]["warehouse_quantities"] == {
        "warehouse_a": 15,
        "warehouse_b": 15,
        "warehouse_c": 18,
    }
    