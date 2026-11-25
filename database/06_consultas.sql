SET NAMES utf8mb4;
USE restaurante_pro_max;
-- Consulta 1: Ranking de productos facturados

SELECT p.NIT_restaurante, p.num_serial AS id_producto, p.nombre AS producto,
       SUM(dp.cantidad) AS unidades_facturadas,
       SUM(dp.cantidad * p.precio) AS valor_a_precio_actual
FROM `Detalle_Pedido` AS dp
INNER JOIN `Producto` AS p ON p.num_serial = dp.num_serial_producto
    AND p.NIT_restaurante = dp.NIT_restaurante
INNER JOIN `Factura` AS f ON f.num_pedido = dp.num_pedido
    AND f.NIT_restaurante = dp.NIT_restaurante
WHERE p.NIT_restaurante = '900123456-1'
GROUP BY p.NIT_restaurante, p.num_serial, p.nombre
HAVING SUM(dp.cantidad) >= 3
ORDER BY valor_a_precio_actual DESC, p.num_serial;

-- Consulta 2: Ingresos totales y ticket promedio por método de pago

SELECT 
    r.nombre_restaurante,
    f.metodo_pago,
    COUNT(f.id_factura) AS total_facturas,
    SUM(f.valor_total) AS ingresos_totales,
    ROUND(AVG(f.valor_total), 2) AS promedio_por_factura
FROM Factura f
INNER JOIN Restaurante r 
    ON f.NIT_restaurante = r.NIT
GROUP BY r.nombre_restaurante, f.metodo_pago
ORDER BY ingresos_totales DESC;

-- Consulta 3: Cajeros con recaudo superior o igual al promedio de facturación

SELECT 
    r.nombre_restaurante,
    f.id_cajero,
    COUNT(f.id_factura) AS facturas_emitidas,
    SUM(f.subvalor_total) AS total_subtotal,
    SUM(f.valor_total) AS total_recaudado
FROM Factura f
INNER JOIN Restaurante r 
    ON f.NIT_restaurante = r.NIT
GROUP BY r.nombre_restaurante, f.id_cajero
HAVING SUM(f.valor_total) >= (
    SELECT AVG(valor_total) 
    FROM Factura
)
ORDER BY total_recaudado DESC;

-- Consulta 4: Alerta de inventario crítico y platos afectados en el menú

SELECT 
    ins.id_insumo,
    ins.nombre AS nombre_insumo,
    ins.unidad_medida,
    ins.cantidad_disponible,
    ins.cantidad_minima,
    prod.nombre AS plato_afectado,
    rec.cantidad AS cantidad_requerida_receta
FROM Insumo ins
INNER JOIN Receta rec 
    ON ins.id_insumo = rec.id_insumo 
    AND ins.NIT_restaurante = rec.NIT_restaurante
INNER JOIN Producto prod 
    ON rec.num_serial_producto = prod.num_serial 
    AND rec.NIT_restaurante = prod.NIT_restaurante
WHERE ins.cantidad_disponible <= ins.cantidad_minima
ORDER BY ins.cantidad_disponible ASC;

-- Consulta 5: Platos con precio superior al promedio y cantidad de ingredientes

SELECT 
    prod.num_serial,
    prod.nombre AS nombre_producto,
    prod.categoria_plato,
    prod.precio,
    COUNT(rec.id_insumo) AS total_ingredientes
FROM Producto prod
LEFT JOIN Receta rec 
    ON prod.num_serial = rec.num_serial_producto 
    AND prod.NIT_restaurante = rec.NIT_restaurante
WHERE prod.precio > (
    SELECT AVG(precio) 
    FROM Producto
)
GROUP BY prod.num_serial, prod.nombre, prod.categoria_plato, prod.precio
ORDER BY prod.precio DESC;

-- Consulta 6: Control de pedidos registrados pendientes de facturación

SELECT 
    p.num_pedido,
    r.nombre_restaurante,
    p.num_mesa,
    p.id_mesero,
    p.fecha_hora_pedido,
    p.estado_pedido
FROM Pedido p
INNER JOIN Restaurante r 
    ON p.NIT_restaurante = r.NIT
LEFT JOIN Factura f 
    ON p.num_pedido = f.num_pedido 
    AND p.NIT_restaurante = f.NIT_restaurante
WHERE f.id_factura IS NULL
ORDER BY p.fecha_hora_pedido ASC;

-- Consulta 7: Consumo teórico de insumos según pedidos facturados

SELECT 
    ins.NIT_restaurante,
    ins.id_insumo,
    ins.nombre AS nombre_insumo,
    ins.unidad_medida,
    SUM(dp.cantidad * rec.cantidad) AS consumo_teorico_facturado,
    ins.cantidad_disponible AS stock_actual_bodega
FROM Factura f
INNER JOIN Detalle_Pedido dp 
    ON f.num_pedido = dp.num_pedido 
    AND f.NIT_restaurante = dp.NIT_restaurante
INNER JOIN Receta rec 
    ON dp.num_serial_producto = rec.num_serial_producto 
    AND dp.NIT_restaurante = rec.NIT_restaurante
INNER JOIN Insumo ins 
    ON rec.id_insumo = ins.id_insumo 
    AND rec.NIT_restaurante = ins.NIT_restaurante
GROUP BY ins.NIT_restaurante, ins.id_insumo, ins.nombre, ins.unidad_medida, ins.cantidad_disponible
ORDER BY consumo_teorico_facturado DESC;

-- Consulta 8: Desempeño de atención por mesero y ventas facturadas

SELECT 
    r.nombre_restaurante,
    p.id_mesero,
    COUNT(DISTINCT p.num_pedido) AS pedidos_facturados,
    COUNT(DISTINCT p.num_mesa) AS mesas_atendidas,
    SUM(f.valor_total) AS ventas_generadas,
    ROUND(AVG(f.valor_total), 2) AS promedio_venta_pedido
FROM Pedido p
INNER JOIN Restaurante r 
  ON p.NIT_restaurante = r.NIT
INNER JOIN Factura f 
    ON p.num_pedido = f.num_pedido 
    AND p.NIT_restaurante = f.NIT_restaurante
GROUP BY r.nombre_restaurante, p.id_mesero
HAVING COUNT(DISTINCT p.num_pedido) >= 2
ORDER BY ventas_generadas DESC;
