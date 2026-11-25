import os
import threading
import time
from pathlib import Path

import duckdb

QUERIES_DIR = Path(__file__).resolve().parent.parent / "queries"
TIMEOUT_S = float(os.getenv("QUERY_TIMEOUT_S", "5"))

FED_USER = os.getenv("FED_DB_USER", "fed_ro")
FED_PASSWORD = os.getenv("FED_DB_PASSWORD", "fed_ro_pw")

# (nama sumber, alias di SQL, tipe extension, connection string)
SOURCES = [
    (
        "orders-db", "shop", "postgres",
        f"host={os.getenv('ORDERS_DB_HOST', 'orders-db')} "
        f"port={os.getenv('ORDERS_DB_PORT', '5432')} "
        f"dbname={os.getenv('ORDERS_DB_NAME', 'shop')} "
        f"user={FED_USER} password={FED_PASSWORD}",
    ),
    (
        "stock-db", "inv", "mysql",
        f"host={os.getenv('STOCK_DB_HOST', 'stock-db')} "
        f"port={os.getenv('STOCK_DB_PORT', '3306')} "
        f"database={os.getenv('STOCK_DB_NAME', 'inventory')} "
        f"user={FED_USER} password={FED_PASSWORD}",
    ),
]


def _attach(con, source, alias, kind, dsn):
    con.execute(f"ATTACH '{dsn}' AS {alias} (TYPE {kind}, READ_ONLY)")


def _work(sql, state):
    con = duckdb.connect()
    state["con"] = con
    try:
        con.execute("LOAD postgres")
        con.execute("LOAD mysql")
        for source, alias, kind, dsn in SOURCES:
            state["stage"] = source
            _attach(con, source, alias, kind, dsn)
        state["stage"] = None
        cur = con.execute(sql)
        cols = [c[0] for c in cur.description]
        state["result"] = [dict(zip(cols, row)) for row in cur.fetchall()]
    except duckdb.Error as exc:
        state["error"] = exc
    finally:
        con.close()


def _execute(sql):
    """Jalankan sql di thread sendiri dan tunggu paling lama TIMEOUT_S detik."""
    state = {"con": None, "stage": None, "result": None, "error": None}

    worker = threading.Thread(target=_work, args=(sql, state), daemon=True)
    worker.start()
    worker.join(TIMEOUT_S)

    if worker.is_alive():
        if state["con"] is not None:
            state["con"].interrupt()
        raise TimeoutError(f"timeout after {TIMEOUT_S}s")
    if state["error"] is not None:
        raise state["error"]
    return state["result"]


def _read_sql(name):
    return (QUERIES_DIR / f"{name}.sql").read_text(encoding="utf-8")


def run_report(name):
    started = time.perf_counter()
    rows = _execute(_read_sql(name))
    return {
        "query": name,
        "sources": [s[0] for s in SOURCES],
        "row_count": len(rows),
        "elapsed_ms": round((time.perf_counter() - started) * 1000),
        "rows": rows,
    }
