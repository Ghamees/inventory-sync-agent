from collections import defaultdict


def detect_conflicts(inventories: dict) -> list[dict]:
    sku_states = defaultdict(dict)

    for warehouse_name, inventory in inventories.items():
        for sku, quantity in inventory.items():
            sku_states[sku][warehouse_name] = quantity

    conflicts = []

    for sku, warehouse_quantities in sku_states.items():
        quantities = list(warehouse_quantities.values())

        if len(set(quantities)) > 1:
            conflicts.append(
                {
                    "sku": sku,
                    "warehouse_quantities": warehouse_quantities,
                    "type": "quantity_mismatch",
                }
            )

    return conflicts