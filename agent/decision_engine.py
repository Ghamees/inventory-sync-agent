from collections import Counter


def decide_action(conflict: dict) -> dict:
    sku = conflict["sku"]
    warehouse_quantities = conflict["warehouse_quantities"]

    quantities = list(warehouse_quantities.values())
    counts = Counter(quantities)

    most_common_quantity, frequency = counts.most_common(1)[0]

    # If at least two warehouses agree, treat that as the consensus.
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

    # No majority means the conflict is ambiguous.
    return {
        "sku": sku,
        "action": "trigger_recount",
        "target_quantity": None,
        "target_warehouses": list(warehouse_quantities.keys()),
        "reason": "No warehouse quantity consensus",
    }