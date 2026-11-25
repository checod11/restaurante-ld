-- L&D 3.8. Solo SELECT y variables de sesión. Ejecutar con cuenta autorizada en ambas BD.
USE restaurante_pro_max;
SET NAMES utf8mb4;
SET @nit = '900123456-1';
-- BLOQUE A: ejecutar antes de la venta y guardar resultados; repetir después.
SELECT NOW() AS fecha_servidor, COUNT(*) AS facturas,
       COALESCE(SUM(valor_total),0) AS ventas_totales
FROM Factura WHERE NIT_restaurante=@nit;
SELECT id_insumo,nombre,unidad_medida,cantidad_disponible,cantidad_minima
FROM Insumo WHERE NIT_restaurante=@nit ORDER BY id_insumo;
SELECT num_mesa,estado_mesa FROM v_estado_mesas
WHERE NIT_restaurante=@nit ORDER BY num_mesa;

-- BLOQUE B: después de la venta, reemplazar 0 por el número real.
SET @pedido = 0;
SET @factura = (SELECT id_factura FROM Factura WHERE NIT_restaurante=@nit AND num_pedido=@pedido);
SELECT @pedido AS pedido,@factura AS factura;
SELECT p.num_pedido,p.num_mesa,p.estado_pedido,p.id_mesero,p.id_cocinero,
       p.fecha_hora_pedido,p.fecha_inicio_preparacion,p.fecha_lista,p.fecha_entrega,
       v.estado_mesa
FROM Pedido p JOIN v_estado_mesas v ON p.num_mesa=v.num_mesa AND p.NIT_restaurante=v.NIT_restaurante
WHERE p.NIT_restaurante=@nit AND p.num_pedido=@pedido;
SELECT d.num_serial_producto,p.nombre,d.cantidad,d.precio_unitario,d.nota_especial,
       d.cantidad*d.precio_unitario AS importe
FROM Detalle_Pedido d JOIN Producto p ON d.num_serial_producto=p.num_serial AND d.NIT_restaurante=p.NIT_restaurante
WHERE d.NIT_restaurante=@nit AND d.num_pedido=@pedido;
SELECT id_factura,num_pedido,id_cajero,valor_total,subvalor_total,metodo_pago,monto_recibido,
       CASE WHEN metodo_pago='Efectivo' THEN monto_recibido-valor_total ELSE NULL END AS cambio,estado_validacion
FROM Factura WHERE NIT_restaurante=@nit AND num_pedido=@pedido;
SELECT COUNT(*) AS cantidad_facturas FROM Factura WHERE NIT_restaurante=@nit AND num_pedido=@pedido;
-- Comparación inmediata: no cambiar recetas entre el registro y esta consulta.
WITH esperado AS (
  SELECT r.id_insumo,SUM(r.cantidad*d.cantidad) AS consumo
  FROM Detalle_Pedido d JOIN Receta r ON d.num_serial_producto=r.num_serial_producto AND d.NIT_restaurante=r.NIT_restaurante
  WHERE d.NIT_restaurante=@nit AND d.num_pedido=@pedido GROUP BY r.id_insumo
), real AS (
  SELECT id_insumo,SUM(cantidad) AS consumo FROM Movimiento_Inventario
  WHERE NIT_restaurante=@nit AND id_factura=@factura AND tipo='Salida' GROUP BY id_insumo
), ids AS (SELECT id_insumo FROM esperado UNION SELECT id_insumo FROM real)
SELECT ids.id_insumo,i.nombre,i.unidad_medida,e.consumo AS esperado,r.consumo AS registrado,
       CASE WHEN e.consumo IS NOT NULL AND r.consumo=e.consumo THEN 'OK' ELSE 'REVISAR' END AS resultado
FROM ids JOIN Insumo i ON i.id_insumo=ids.id_insumo AND i.NIT_restaurante=@nit
LEFT JOIN esperado e ON e.id_insumo=ids.id_insumo LEFT JOIN real r ON r.id_insumo=ids.id_insumo;
SELECT id_movimiento,id_insumo,id_empleado,tipo,cantidad,fecha_hora
FROM Movimiento_Inventario WHERE NIT_restaurante=@nit AND id_factura=@factura;
-- Auditoría: usar collation común para comparación entre esquemas. No mostrar datos personales.
SELECT id_auditoria,operacion,fecha_hora,detalle_cambio FROM audit_pro.auditoria_Pedido
WHERE NIT_restaurante COLLATE utf8mb4_unicode_ci=@nit COLLATE utf8mb4_unicode_ci AND num_pedido=@pedido ORDER BY id_auditoria;
SELECT id_auditoria,operacion,fecha_hora FROM audit_pro.auditoria_Detalle_Pedido
WHERE NIT_restaurante COLLATE utf8mb4_unicode_ci=@nit COLLATE utf8mb4_unicode_ci AND num_pedido=@pedido ORDER BY id_auditoria;
SELECT id_auditoria,operacion,fecha_hora FROM audit_pro.auditoria_Factura
WHERE NIT_restaurante COLLATE utf8mb4_unicode_ci=@nit COLLATE utf8mb4_unicode_ci AND id_factura=@factura ORDER BY id_auditoria;
SELECT a.id_auditoria,a.id_movimiento,a.operacion,a.fecha_hora FROM audit_pro.auditoria_Movimiento_Inventario a
JOIN Movimiento_Inventario m ON a.id_movimiento=m.id_movimiento AND a.NIT_restaurante COLLATE utf8mb4_unicode_ci=m.NIT_restaurante COLLATE utf8mb4_unicode_ci
WHERE m.NIT_restaurante=@nit AND m.id_factura=@factura ORDER BY a.id_auditoria;
SELECT DISTINCT a.id_auditoria,a.id_insumo,a.operacion,a.fecha_hora,a.detalle_cambio FROM audit_pro.auditoria_Insumo a
JOIN Movimiento_Inventario m ON a.id_insumo=m.id_insumo AND a.NIT_restaurante COLLATE utf8mb4_unicode_ci=m.NIT_restaurante COLLATE utf8mb4_unicode_ci
WHERE m.NIT_restaurante=@nit AND m.id_factura=@factura AND a.operacion='UPD'
AND ABS(TIMESTAMPDIFF(SECOND,a.fecha_hora,m.fecha_hora))<=10 ORDER BY a.id_auditoria;
-- Las coincidencias temporales de Insumo son evidencia auxiliar, no vínculo único con factura.
