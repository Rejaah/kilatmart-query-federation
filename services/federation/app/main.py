import logging
import sys

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.federation import QueryFailed, QueryTimeout, SourceUnavailable, run_report

logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                    format="%(levelname)s %(name)s %(message)s")
log = logging.getLogger("federation")

app = FastAPI(title="federation")


@app.exception_handler(SourceUnavailable)
async def on_source_unavailable(request: Request, exc: SourceUnavailable):
    log.error("path=%s error=source_unavailable source=%s", request.url.path, exc.source)
    return JSONResponse(status_code=503, content={
        "error": "source_unavailable", "source": exc.source, "detail": exc.detail})


@app.exception_handler(QueryTimeout)
async def on_query_timeout(request: Request, exc: QueryTimeout):
    log.error("path=%s error=source_timeout source=%s timeout_s=%s",
              request.url.path, exc.source, exc.timeout_s)
    return JSONResponse(status_code=504, content={
        "error": "source_timeout", "timeout_s": exc.timeout_s, "source": exc.source})


@app.exception_handler(QueryFailed)
async def on_query_failed(request: Request, exc: QueryFailed):
    log.error("path=%s error=query_failed detail=%s", request.url.path, exc)
    return JSONResponse(status_code=500, content={"error": "query_failed", "detail": str(exc)})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/reports/low-stock-paid-orders")
def low_stock_paid_orders():
    result = run_report("low_stock_paid_orders")
    log.info("report=low_stock rows=%d elapsed_ms=%d",
             result["row_count"], result["elapsed_ms"])
    return result
