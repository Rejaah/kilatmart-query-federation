SELECT o.order_id, o.customer_name, o.sku,
       o.qty AS qty_ordered, s.qty_on_hand, s.reorder_level
FROM shop.orders AS o
JOIN inv.stock   AS s ON s.sku = o.sku
WHERE o.status = 'paid'
  AND s.qty_on_hand <= s.reorder_level
ORDER BY o.order_id;
