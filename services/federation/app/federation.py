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


class SourceUnavailable(Exception):
    def __init__(self, source, detail):
        super().__init__(detail)
        self.source = source
        self.detail = detail


class QueryTimeout(Exception):
    def __init__(self, timeout_s, source):
        super().__init__(f"timeout after {timeout_s}s")
        self.timeout_s = timeout_s
        self.source = source


class QueryFailed(Exception):
    pass


def _attach(con, source, alias, kind, dsn):
    try:
        con.execute(f"ATTACH '{dsn}' AS {alias} (TYPE {kind}, READ_ONLY)")
    except duckdb.Error as exc:
        # pesan DuckDB memuat connection string, jadi password disamarkan
        raise SourceUnavailable(source, str(exc).replace(FED_PASSWORD, "***")) from exc


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
    except SourceUnavailable as exc:
        state["error"] = exc
    except duckdb.Error as exc:
        state["error"] = QueryFailed(str(exc))
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
        raise QueryTimeout(TIMEOUT_S, state["stage"])
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


def explain_report(name):
    rows = _execute("EXPLAIN " + _read_sql(name))
    return "\n".join(row["explain_value"] for row in rows)


def _check_one(source, alias, kind, dsn, out):
    started = time.perf_counter()
    con = duckdb.connect()
    out["con"] = con
    try:
        con.execute(f"LOAD {kind}")
        _attach(con, source, alias, kind, dsn)
        out["status"], out["detail"] = "up", None
    except SourceUnavailable as exc:
        out["status"], out["detail"] = "down", exc.detail
    except duckdb.Error as exc:
        out["status"], out["detail"] = "down", str(exc)
    finally:
        out["elapsed_ms"] = round((time.perf_counter() - started) * 1000)
        con.close()


def check_sources():
    """Coba ATTACH tiap sumber secara paralel. Status: up, down, atau timeout."""
    jobs = []
    for source, alias, kind, dsn in SOURCES:
        out = {
            "source": source, "status": "timeout", "con": None,
            "detail": f"tidak menjawab dalam {TIMEOUT_S:g} detik",
            "elapsed_ms": round(TIMEOUT_S * 1000),
        }
        worker = threading.Thread(target=_check_one, args=(source, alias, kind, dsn, out), daemon=True)
        worker.start()
        jobs.append((worker, out))

    deadline = time.perf_counter() + TIMEOUT_S
    sources = []
    for worker, out in jobs:
        worker.join(max(0.0, deadline - time.perf_counter()))
        if worker.is_alive() and out["con"] is not None:
            out["con"].interrupt()
        sources.append({k: out[k] for k in ("source", "status", "detail", "elapsed_ms")})

    all_up = all(s["status"] == "up" for s in sources)
    return {"status": "ok" if all_up else "degraded", "sources": sources}
