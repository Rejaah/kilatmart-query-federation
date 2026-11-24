import os
from typing import Literal

import psycopg
from fastapi import FastAPI, HTTPException
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

app = FastAPI(title="webshop-api")

def connect():
    return psycopg.connect(
        host=os.getenv("ORDERS_DB_HOST", "orders-db"),
        port=int(os.getenv("ORDERS_DB_PORT", "5432")),
        dbname=os.getenv("ORDERS_DB_NAME", "shop"),
        user=os.getenv("APP_DB_USER", "kilat"),
        password=os.getenv("APP_DB_PASSWORD", "kilat_pw"),
        row_factory=dict_row,
    )

class NewOrder(BaseModel):
    customer_name: str
    sku: str
    qty: int = Field(gt=0)
    total_amount: float = Field(ge=0)

class StatusUpdate(BaseModel):
    status: Literal["pending", "paid", "shipped", "cancelled"]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/orders")
def list_orders():
    with connect() as conn:
        return conn.execute("SELECT * FROM orders ORDER BY order_id").fetchall()

@app.post("/orders", status_code=201)
def create_order(body: NewOrder):
    with connect() as conn:
        return conn.execute(
            "INSERT INTO orders (customer_name, sku, qty, status, total_amount) "
            "VALUES (%s, %s, %s, 'pending', %s) RETURNING *",
            (body.customer_name, body.sku, body.qty, body.total_amount),
        ).fetchone()

@app.patch("/orders/{order_id}/status")
def update_status(order_id: int, body: StatusUpdate):
    with connect() as conn:
        row = conn.execute(
            "UPDATE orders SET status = %s WHERE order_id = %s RETURNING *",
            (body.status, order_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="order not found")
    return row