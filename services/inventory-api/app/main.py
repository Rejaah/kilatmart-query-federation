import os
from contextlib import closing

import pymysql
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pymysql.cursors import DictCursor

app = FastAPI(title="inventory-api")

def connect():
    return pymysql.connect(
        host=os.getenv("STOCK_DB_HOST", "stock-db"),
        port=int(os.getenv("STOCK_DB_PORT", "3306")),
        database=os.getenv("STOCK_DB_NAME", "inventory"),
        user=os.getenv("APP_DB_USER", "kilat"),
        password=os.getenv("APP_DB_PASSWORD", "kilat_pw"),
        cursorclass=DictCursor,
        autocommit=True,
    )

class StockUpdate(BaseModel):
    qty_on_hand: int = Field(ge=0)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/stock")
def list_stock():
    with closing(connect()) as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM stock ORDER BY sku")
        return cur.fetchall()

@app.put("/stock/{sku}")
def update_stock(sku: str, body: StockUpdate):
    with closing(connect()) as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE stock SET qty_on_hand = %s WHERE sku = %s",
            (body.qty_on_hand, sku),
        )
        cur.execute("SELECT * FROM stock WHERE sku = %s", (sku,))
        row = cur.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="sku not found")
    return row