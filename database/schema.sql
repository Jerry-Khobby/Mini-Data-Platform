----creating databases
CREATE DATABASE metabase;


-- Core tables

CREATE TABLE IF NOT EXISTS sales (
    order_id      TEXT PRIMARY KEY,
    product       TEXT,
    category      TEXT,
    sale_amount   NUMERIC(12, 2),
    sale_date     TIMESTAMP,
    region        TEXT,
    processed_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id            SERIAL PRIMARY KEY,
    dag_id        TEXT        NOT NULL,
    run_id        TEXT        NOT NULL,
    status        TEXT        NOT NULL,
    rows_loaded   INT         DEFAULT 0,
    started_at    TIMESTAMP   DEFAULT NOW(),
    finished_at   TIMESTAMP
);

-- Useful indexes

CREATE INDEX IF NOT EXISTS idx_sales_date     ON sales(sale_date);
CREATE INDEX IF NOT EXISTS idx_sales_category ON sales(category);
CREATE INDEX IF NOT EXISTS idx_sales_region   ON sales(region);