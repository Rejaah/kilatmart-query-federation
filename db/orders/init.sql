CREATE TABLE orders (
    order_id      SERIAL PRIMARY KEY,
    customer_name TEXT          NOT NULL,
    sku           TEXT          NOT NULL,
    qty           INTEGER       NOT NULL,
    status        TEXT          NOT NULL CHECK (status IN ('pending', 'paid', 'shipped', 'cancelled')),
    total_amount  NUMERIC(12,2) NOT NULL,
    created_at    TIMESTAMP     NOT NULL DEFAULT now()
);

INSERT INTO orders (customer_name, sku, qty, status, total_amount) VALUES
    ('Andi Pratama',    'SKU-002', 2, 'paid',      120000),
    ('Budi Santoso',    'SKU-001', 1, 'paid',       85000),
    ('Citra Lestari',   'SKU-003', 3, 'paid',      210000),
    ('Dewi Anggraini',  'SKU-004', 1, 'paid',       95000),
    ('Eko Wijaya',      'SKU-005', 5, 'paid',      450000),
    ('Fajar Nugroho',   'SKU-002', 1, 'pending',    60000),
    ('Gita Permata',    'SKU-003', 2, 'pending',   140000),
    ('Hendra Kusuma',   'SKU-004', 2, 'cancelled', 190000),
    ('Indah Sari',      'SKU-006', 1, 'shipped',    70000),
    ('Joko Susilo',     'SKU-002', 4, 'paid',      240000),
    ('Kiki Amelia',     'SKU-001', 2, 'pending',   170000),
    ('Lina Marlina',    'SKU-006', 3, 'paid',      225000);
