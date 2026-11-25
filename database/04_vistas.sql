SET NAMES utf8mb4;
USE restaurante_pro_max;
-- Vista 1: v_resumen_facturacion_pedidos

CREATE OR REPLACE VIEW v_resumen_facturacion_pedidos AS
SELECT
    f.id_factura,
    f.NIT_restaurante,
    r.nombre_restaurante,
    f.num_pedido,
    p.num_mesa,
    f.id_cajero,
    f.nombre_cliente,
    f.subvalor_total,
    f.valor_total,
    f.metodo_pago,
    f.tipo_documento,
    f.fecha_emision
FROM Factura f
INNER JOIN Restaurante r
    ON f.NIT_restaurante = r.NIT
INNER JOIN Pedido p
    ON f.num_pedido = p.num_pedido
   AND f.NIT_restaurante = p.NIT_restaurante;

SELECT * FROM v_resumen_facturacion_pedidos;

-- Vista 2: v_ficha_recetas_insumos
CREATE OR REPLACE VIEW v_ficha_recetas_insumos AS
SELECT
    rec.num_serial_producto,
    rec.id_insumo,
    rec.NIT_restaurante,
    prod.nombre AS nombre_producto,
    prod.categoria_plato,
    prod.precio,
    ins.nombre AS nombre_insumo,
    ins.unidad_medida,
    rec.cantidad AS cantidad_requerida,
    ins.cantidad_disponible
FROM Receta rec
INNER JOIN Producto prod
    ON rec.num_serial_producto = prod.num_serial
   AND rec.NIT_restaurante = prod.NIT_restaurante
INNER JOIN Insumo ins
    ON rec.id_insumo = ins.id_insumo
   AND rec.NIT_restaurante = ins.NIT_restaurante;

SELECT * FROM v_ficha_recetas_insumos;

-- Verificación general de vistas creadas

SHOW FULL TABLES WHERE Table_type = 'VIEW';
