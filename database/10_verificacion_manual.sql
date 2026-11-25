-- Ejecutar como administrador. Solo consultas.
USE restaurante_pro_max;
SELECT TABLE_SCHEMA,TABLE_TYPE,COUNT(*) AS cantidad FROM information_schema.TABLES
WHERE TABLE_SCHEMA IN ('restaurante_pro_max','audit_pro') GROUP BY TABLE_SCHEMA,TABLE_TYPE;
SELECT COUNT(*) AS disparadores FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA='restaurante_pro_max';
SELECT * FROM v_estado_mesas WHERE NIT_restaurante='900123456-1' ORDER BY num_mesa;
SELECT p.num_pedido,p.num_mesa,p.estado_pedido,d.nota_especial,d.precio_unitario
FROM Pedido p JOIN Detalle_Pedido d ON p.num_pedido=d.num_pedido AND p.NIT_restaurante=d.NIT_restaurante
LEFT JOIN Factura f ON f.num_pedido=p.num_pedido AND f.NIT_restaurante=p.NIT_restaurante
WHERE p.NIT_restaurante='900123456-1' AND f.id_factura IS NULL ORDER BY p.num_pedido;
SELECT COUNT(*) AS movimientos FROM Movimiento_Inventario;
SELECT COUNT(*) AS mesas_auditadas FROM audit_pro.auditoria_Mesa;
SELECT COUNT(*) AS movimientos_auditados FROM audit_pro.auditoria_Movimiento_Inventario;

SELECT TABLE_NAME,CONSTRAINT_NAME,REFERENCED_TABLE_NAME FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA='restaurante_pro_max' AND CONSTRAINT_NAME IN ('fk_pedido_mesa','fk_pedido_cocinero','fk_mov_insumo','fk_mov_empleado','fk_mov_factura') AND REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY TABLE_NAME,CONSTRAINT_NAME,ORDINAL_POSITION;
