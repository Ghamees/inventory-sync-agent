import httpx


WAREHOUSES = {
    "warehouse_a": "http://127.0.0.1:8001",
    "warehouse_b": "http://127.0.0.1:8002",
    "warehouse_c": "http://127.0.0.1:8003",
}


def fetch_inventory(warehouse_name: str) -> dict:
    base_url = WAREHOUSES[warehouse_name]

    response = httpx.get(
        f"{base_url}/inventory",
        timeout=5.0,
    )

    response.raise_for_status()

    return response.json()


def update_stock(
    warehouse_name: str,
    sku: str,
    quantity: int,
) -> dict:
    base_url = WAREHOUSES[warehouse_name]

    response = httpx.patch(
        f"{base_url}/inventory/{sku}",
        json={"quantity": quantity},
        timeout=5.0,
    )

    response.raise_for_status()

    return response.json()