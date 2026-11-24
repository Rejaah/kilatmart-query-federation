CREATE TABLE stock (
    sku           VARCHAR(32)  PRIMARY KEY,
    product_name  VARCHAR(100) NOT NULL,
    qty_on_hand   INT          NOT NULL,
    reorder_level INT          NOT NULL,
    warehouse     VARCHAR(50)  NOT NULL,
    updated_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO stock (sku, product_name, qty_on_hand, reorder_level, warehouse) VALUES
    ('SKU-001', 'Beras 5 kg',        50,  10, 'Gudang Jakarta'),
    ('SKU-002', 'Minyak Goreng 2 L',  3,  10, 'Gudang Jakarta'),
    ('SKU-003', 'Gula Pasir 1 kg',    8,  10, 'Gudang Surabaya'),
    ('SKU-004', 'Telur Ayam 1 kg',   10,  10, 'Gudang Surabaya'),
    ('SKU-005', 'Susu UHT 1 L',     100,  20, 'Gudang Jakarta'),
    ('SKU-006', 'Mie Instan Dus',    40,  15, 'Gudang Surabaya');
