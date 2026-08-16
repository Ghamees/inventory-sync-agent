from warehouse_client import update_stock


def execute_action(decision: dict) -> list[dict]:
    results = []

    if decision["action"] == "adjust_stock":
        for warehouse_name in decision["target_warehouses"]:
            result = update_stock(
                warehouse_name=warehouse_name,
                sku=decision["sku"],
                quantity=decision["target_quantity"],
            )

            results.append(
                {
                    "warehouse": warehouse_name,
                    "result": result,
                }
            )

    elif decision["action"] == "trigger_recount":
        results.append(
            {
                "warehouse": decision["target_warehouses"],
                "result": "Recount requested",
            }
        )

    return results