from warehouse_client import WAREHOUSES, fetch_inventory
from conflict_detector import detect_conflicts
from decision_engine import decide_action
from action_executor import execute_action
from action_ledger import (
    initialise_ledger,
    create_conflict_id,
    has_been_handled,
    record_action,
)


def main():
    initialise_ledger()

    print("Fetching inventory from all warehouses...\n")

    inventories = {}

    for warehouse_name in WAREHOUSES:
        inventory = fetch_inventory(warehouse_name)
        inventories[warehouse_name] = inventory

        print(f"{warehouse_name}:")
        print(inventory)
        print()

    conflicts = detect_conflicts(inventories)

    print("Conflict detection result:\n")

    if not conflicts:
        print("No conflicts detected.")
        return

    for conflict in conflicts:
        print(f"SKU: {conflict['sku']}")
        print(f"Type: {conflict['type']}")

        for warehouse_name, quantity in conflict["warehouse_quantities"].items():
            print(f"  {warehouse_name}: {quantity}")

        conflict_id = create_conflict_id(conflict)

        if has_been_handled(conflict_id):
            print("\nAlready handled. No duplicate action taken.\n")
            continue

        decision = decide_action(conflict)

        print("\nDecision:")
        print(f"  Action: {decision['action']}")
        print(f"  Reason: {decision['reason']}")
        print(f"  Target quantity: {decision['target_quantity']}")
        print(f"  Target warehouses: {decision['target_warehouses']}")

        results = execute_action(decision)

        record_action(
            conflict_id=conflict_id,
            sku=conflict["sku"],
            action=decision["action"],
            details={
                "decision": decision,
                "results": results,
            },
        )

        print("\nAction applied:")
        print(results)
        print()


if __name__ == "__main__":
    main()