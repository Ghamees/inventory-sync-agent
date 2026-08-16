from collections import defaultdict


def detect_conflicts(inventories: dict) -> list[dict]:
    sku_states = defaultdict(dict)
    warehouse_names = list(inventories.keys())

    for warehouse_name, inventory in inventories.items():
        for sku, quantity in inventory.items():
            sku_states[sku][warehouse_name] = quantity

    conflicts = []

    for sku, warehouse_quantities in sku_states.items():

        # Detect if the SKU is missing from one or more warehouses.
        missing_warehouses = [
            warehouse_name
            for warehouse_name in warehouse_names
            if warehouse_name not in warehouse_quantities
        ]

        if missing_warehouses:
            conflicts.append(
                {
                    "sku": sku,
                    "warehouse_quantities": warehouse_quantities,
                    "missing_warehouses": missing_warehouses,
                    "type": "missing_sku",
                }
            )
            continue

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