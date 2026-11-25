-- L&D | Etapa 2.10 | SOLO LECTURA. Ejecutar con usuario autorizado para audit_pro.
-- Cambiar 0 por el número del pedido nuevo que reportó prueba_integracion.py.
USE restaurante_pro_max;
SET NAMES utf8mb4;
SET @pedido = 0;
SET @nit = '900123456-1';
-- Comparaciones explícitas para evitar ERROR 1267 entre las dos bases.
SET @factura = (SELECT id_factura FROM Factura WHERE num_pedido=@pedido
  AND NIT_restaurante COLLATE utf8mb4_unicode_ci = @nit COLLATE utf8mb4_unicode_ci);

SELECT @pedido AS pedido, @factura AS factura;
SELECT num_pedido,num_mesa,id_mesero,id_cocinero,estado_pedido,
       fecha_hora_pedido,fecha_inicio_preparacion,fecha_lista,fecha_entrega
FROM Pedido WHERE num_pedido=@pedido AND NIT_restaurante COLLATE utf8mb4_unicode_ci=@nit COLLATE utf8mb4_unicode_ci;
SELECT num_serial_producto,cantidad,precio_unitario,nota_especial
FROM Detalle_Pedido WHERE num_pedido=@pedido AND NIT_restaurante COLLATE utf8mb4_unicode_ci=@nit COLLATE utf8mb4_unicode_ci;
SELECT id_factura,id_cajero,valor_total,subvalor_total,metodo_pago,monto_recibido,estado_validacion
FROM Factura WHERE num_pedido=@pedido AND NIT_restaurante COLLATE utf8mb4_unicode_ci=@nit COLLATE utf8mb4_unicode_ci;
SELECT id_movimiento,id_insumo,id_empleado,tipo,cantidad,fecha_hora
FROM Movimiento_Inventario WHERE id_factura=@factura AND NIT_restaurante COLLATE utf8mb4_unicode_ci=@nit COLLATE utf8mb4_unicode_ci;

-- Resultado esperado para el pedido nuevo: 1 INS y 4 UPD (inicio, lista, entrega, cierre).
SELECT * FROM audit_pro.auditoria_Pedido WHERE num_pedido=@pedido
AND NIT_restaurante COLLATE utf8mb4_unicode_ci=@nit COLLATE utf8mb4_unicode_ci ORDER BY id_auditoria;
-- 1 INS del detalle (la prueba crea una sola línea).
SELECT * FROM audit_pro.auditoria_Detalle_Pedido WHERE num_pedido=@pedido
AND NIT_restaurante COLLATE utf8mb4_unicode_ci=@nit COLLATE utf8mb4_unicode_ci ORDER BY id_auditoria;
-- 1 INS de factura.
SELECT * FROM audit_pro.auditoria_Factura WHERE id_factura=@factura
AND NIT_restaurante COLLATE utf8mb4_unicode_ci=@nit COLLATE utf8mb4_unicode_ci ORDER BY id_auditoria;
-- 1 INS por ingrediente; JOIN con collation común.
SELECT a.* FROM audit_pro.auditoria_Movimiento_Inventario a
JOIN Movimiento_Inventario m ON a.id_movimiento=m.id_movimiento
AND a.NIT_restaurante COLLATE utf8mb4_unicode_ci=m.NIT_restaurante COLLATE utf8mb4_unicode_ci
WHERE m.id_factura=@factura AND m.NIT_restaurante COLLATE utf8mb4_unicode_ci=@nit COLLATE utf8mb4_unicode_ci
ORDER BY a.id_auditoria;
-- Actualizaciones candidatas de insumos en el instante de la venta.
-- La auditoría de Insumo no guarda id_factura: corroborar cantidades y fecha manualmente.
SELECT a.* FROM audit_pro.auditoria_Insumo a
JOIN Movimiento_Inventario m ON a.id_insumo=m.id_insumo
AND a.NIT_restaurante COLLATE utf8mb4_unicode_ci=m.NIT_restaurante COLLATE utf8mb4_unicode_ci
WHERE m.id_factura=@factura AND m.NIT_restaurante COLLATE utf8mb4_unicode_ci=@nit COLLATE utf8mb4_unicode_ci
AND a.operacion='UPD' AND ABS(TIMESTAMPDIFF(SECOND,a.fecha_hora,m.fecha_hora))<=10
ORDER BY a.id_auditoria;
