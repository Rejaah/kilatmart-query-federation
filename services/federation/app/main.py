import logging
import sys

from fastapi import FastAPI

from app.federation import run_report

logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                    format="%(levelname)s %(name)s %(message)s")
log = logging.getLogger("federation")

app = FastAPI(title="federation")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/reports/low-stock-paid-orders")
def low_stock_paid_orders():
    result = run_report("low_stock_paid_orders")
    log.info("report=low_stock rows=%d elapsed_ms=%d",
             result["row_count"], result["elapsed_ms"])
    return result
