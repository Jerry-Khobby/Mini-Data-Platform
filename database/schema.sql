
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



-- Total revenue by region
CREATE OR REPLACE VIEW vw_revenue_by_region AS
SELECT region, ROUND(SUM(sale_amount)::numeric, 2) AS total_revenue, COUNT(*) AS total_orders
FROM sales GROUP BY region ORDER BY total_revenue DESC;

-- Revenue by product
CREATE OR REPLACE VIEW vw_revenue_by_product AS
SELECT product, ROUND(SUM(sale_amount)::numeric, 2) AS total_revenue, COUNT(*) AS units_sold
FROM sales GROUP BY product ORDER BY total_revenue DESC;

-- Revenue by category
CREATE OR REPLACE VIEW vw_revenue_by_category AS
SELECT category, ROUND(SUM(sale_amount)::numeric, 2) AS total_revenue, COUNT(*) AS total_orders
FROM sales GROUP BY category ORDER BY total_revenue DESC;

-- Monthly sales trend
CREATE OR REPLACE VIEW vw_monthly_sales_trend AS
SELECT DATE_TRUNC('month', sale_date) AS month, ROUND(SUM(sale_amount)::numeric, 2) AS total_revenue, COUNT(*) AS total_orders
FROM sales GROUP BY month ORDER BY month;

-- Average order value by region
CREATE OR REPLACE VIEW vw_avg_order_value AS
SELECT region, ROUND(AVG(sale_amount)::numeric, 2) AS avg_order_value
FROM sales GROUP BY region ORDER BY avg_order_value DESC;

-- Daily sales (for time series charts)
CREATE OR REPLACE VIEW vw_daily_sales AS
SELECT sale_date::date AS day, ROUND(SUM(sale_amount)::numeric, 2) AS total_revenue, COUNT(*) AS orders
FROM sales GROUP BY day ORDER BY day;



CREATE TABLE etl_monitoring (
    run_id SERIAL PRIMARY KEY,
    run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_rows INT,
    valid_rows INT,
    invalid_rows INT,
    invalid_ratio FLOAT,
    load_duration_seconds FLOAT,
    status VARCHAR(20)
);