-- Ejecutar como root/administrador. No modifica datos persistentes.
SET NAMES utf8mb4;
SELECT VERSION() AS version_servidor;
SELECT TABLE_SCHEMA, TABLE_TYPE, COUNT(*) AS cantidad
FROM information_schema.TABLES
WHERE TABLE_SCHEMA IN ('restaurante_pro_max','audit_pro')
GROUP BY TABLE_SCHEMA, TABLE_TYPE;
SELECT COUNT(*) AS disparadores FROM information_schema.TRIGGERS
WHERE TRIGGER_SCHEMA = 'restaurante_pro_max';
USE restaurante_pro_max;
SELECT 'Restaurante' AS tabla, COUNT(*) AS filas FROM `Restaurante`
UNION ALL
SELECT 'Proveedor' AS tabla, COUNT(*) AS filas FROM `Proveedor`
UNION ALL
SELECT 'Empleado' AS tabla, COUNT(*) AS filas FROM `Empleado`
UNION ALL
SELECT 'Producto' AS tabla, COUNT(*) AS filas FROM `Producto`
UNION ALL
SELECT 'Insumo' AS tabla, COUNT(*) AS filas FROM `Insumo`
UNION ALL
SELECT 'Mesero' AS tabla, COUNT(*) AS filas FROM `Mesero`
UNION ALL
SELECT 'Cocinero' AS tabla, COUNT(*) AS filas FROM `Cocinero`
UNION ALL
SELECT 'Cajero' AS tabla, COUNT(*) AS filas FROM `Cajero`
UNION ALL
SELECT 'Administrador' AS tabla, COUNT(*) AS filas FROM `Administrador`
UNION ALL
SELECT 'Pedido' AS tabla, COUNT(*) AS filas FROM `Pedido`
UNION ALL
SELECT 'Factura' AS tabla, COUNT(*) AS filas FROM `Factura`
UNION ALL
SELECT 'Orden_Compra' AS tabla, COUNT(*) AS filas FROM `Orden_Compra`
UNION ALL
SELECT 'Receta' AS tabla, COUNT(*) AS filas FROM `Receta`
UNION ALL
SELECT 'Detalle_Pedido' AS tabla, COUNT(*) AS filas FROM `Detalle_Pedido`
UNION ALL
SELECT 'Detalle_Orden_Compra' AS tabla, COUNT(*) AS filas FROM `Detalle_Orden_Compra`;
SELECT 'Restaurante' AS tabla_auditoria, COUNT(*) AS filas FROM audit_pro.`auditoria_Restaurante`
UNION ALL
SELECT 'Proveedor' AS tabla_auditoria, COUNT(*) AS filas FROM audit_pro.`auditoria_Proveedor`
UNION ALL
SELECT 'Empleado' AS tabla_auditoria, COUNT(*) AS filas FROM audit_pro.`auditoria_Empleado`
UNION ALL
SELECT 'Producto' AS tabla_auditoria, COUNT(*) AS filas FROM audit_pro.`auditoria_Producto`
UNION ALL
SELECT 'Insumo' AS tabla_auditoria, COUNT(*) AS filas FROM audit_pro.`auditoria_Insumo`
UNION ALL
SELECT 'Mesero' AS tabla_auditoria, COUNT(*) AS filas FROM audit_pro.`auditoria_Mesero`
UNION ALL
SELECT 'Cocinero' AS tabla_auditoria, COUNT(*) AS filas FROM audit_pro.`auditoria_Cocinero`
UNION ALL
SELECT 'Cajero' AS tabla_auditoria, COUNT(*) AS filas FROM audit_pro.`auditoria_Cajero`
UNION ALL
SELECT 'Administrador' AS tabla_auditoria, COUNT(*) AS filas FROM audit_pro.`auditoria_Administrador`
UNION ALL
SELECT 'Pedido' AS tabla_auditoria, COUNT(*) AS filas FROM audit_pro.`auditoria_Pedido`
UNION ALL
SELECT 'Factura' AS tabla_auditoria, COUNT(*) AS filas FROM audit_pro.`auditoria_Factura`
UNION ALL
SELECT 'Orden_Compra' AS tabla_auditoria, COUNT(*) AS filas FROM audit_pro.`auditoria_Orden_Compra`
UNION ALL
SELECT 'Receta' AS tabla_auditoria, COUNT(*) AS filas FROM audit_pro.`auditoria_Receta`
UNION ALL
SELECT 'Detalle_Pedido' AS tabla_auditoria, COUNT(*) AS filas FROM audit_pro.`auditoria_Detalle_Pedido`
UNION ALL
SELECT 'Detalle_Orden_Compra' AS tabla_auditoria, COUNT(*) AS filas FROM audit_pro.`auditoria_Detalle_Orden_Compra`;
-- Verificar registro UPD dentro de una transacción y revertirlo.
START TRANSACTION;
UPDATE Producto SET precio = precio + 1
WHERE num_serial = 101 AND NIT_restaurante = '900123456-1';
SELECT id_auditoria, num_serial, operacion, detalle_cambio
FROM audit_pro.auditoria_Producto
WHERE num_serial = 101 AND NIT_restaurante = '900123456-1'
ORDER BY id_auditoria DESC LIMIT 1;
ROLLBACK;
SELECT num_serial, precio FROM Producto
WHERE num_serial = 101 AND NIT_restaurante = '900123456-1';
