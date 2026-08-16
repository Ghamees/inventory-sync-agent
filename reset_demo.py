from pathlib import Path

from agent.action_ledger import DB_PATH


def reset_demo():
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Deleted ledger: {DB_PATH}")
    else:
        print("No ledger database found.")

    print()
    print("Demo reset complete.")
    print("Important: restart Warehouse C before the demo so its in-memory")
    print("inventory returns to SKU-100 = 18 and SKU-300 remains missing.")


if __name__ == "__main__":
    reset_demo()