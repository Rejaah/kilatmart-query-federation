FROM python:3.12-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "import duckdb; duckdb.sql('INSTALL postgres'); duckdb.sql('INSTALL mysql')"
COPY app ./app
COPY queries ./queries
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]