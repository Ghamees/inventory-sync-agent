from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Warehouse C API")


class StockUpdate(BaseModel):
    quantity: int


inventory = {
    "SKU-100": 18,
    "SKU-200": 8,
}


@app.get("/inventory")
def get_inventory():
    return inventory


@app.get("/inventory/{sku}")
def get_stock(sku: str):
    if sku not in inventory:
        raise HTTPException(status_code=404, detail="SKU not found")

    return {
        "sku": sku,
        "quantity": inventory[sku],
    }


@app.patch("/inventory/{sku}")
def update_stock(sku: str, update: StockUpdate):
    if sku not in inventory:
        raise HTTPException(status_code=404, detail="SKU not found")

    inventory[sku] = update.quantity

    return {
        "message": "Stock updated",
        "sku": sku,
        "quantity": inventory[sku],
    }