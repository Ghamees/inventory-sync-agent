from collections import Counter


def decide_action(conflict: dict) -> dict:
    sku = conflict["sku"]

    if conflict["type"] == "missing_sku":
        return {
            "sku": sku,
            "action": "manual_review",
            "target_quantity": None,
            "target_warehouses": conflict["missing_warehouses"],
            "reason": "SKU is missing from one or more warehouse systems",
        }

    warehouse_quantities = conflict["warehouse_quantities"]

    quantities = list(warehouse_quantities.values())
    counts = Counter(quantities)

    most_common_quantity, frequency = counts.most_common(1)[0]

    if frequency >= 2:
        outliers = [
            warehouse_name
            for warehouse_name, quantity in warehouse_quantities.items()
            if quantity != most_common_quantity
        ]

        return {
            "sku": sku,
            "action": "adjust_stock",
            "target_quantity": most_common_quantity,
            "target_warehouses": outliers,
            "reason": "Majority warehouse consensus",
        }

    return {
        "sku": sku,
        "action": "trigger_recount",
        "target_quantity": None,
        "target_warehouses": list(warehouse_quantities.keys()),
        "reason": "No warehouse quantity consensus",
    }