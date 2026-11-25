"""Consultas y cálculo de disponibilidad. No realizan escrituras."""
from decimal import Decimal

SQL_MESAS = """
SELECT num_mesa, activa, estado_mesa
FROM v_estado_mesas
WHERE NIT_restaurante = %s
ORDER BY num_mesa
"""

SQL_CATEGORIAS = """
SELECT DISTINCT categoria_plato
FROM Producto
WHERE NIT_restaurante = %s
  AND categoria_plato IS NOT NULL AND TRIM(categoria_plato) <> ''
ORDER BY categoria_plato
"""

# El agregado cuenta insumos comprometidos por todos los productos de pedidos
# abiertos. Se excluyen cancelados, cerrados y pedidos con factura existente.
SQL_PRODUCTOS = """
SELECT p.num_serial, p.nombre, p.precio, p.disponibilidad, p.categoria_plato,
       r.id_insumo AS ingrediente_receta, r.cantidad AS cantidad_receta,
       i.id_insumo, i.cantidad_disponible,
       COALESCE(res.comprometido, 0) AS comprometido
FROM Producto p
LEFT JOIN Receta r ON r.num_serial_producto = p.num_serial
    AND r.NIT_restaurante = p.NIT_restaurante
LEFT JOIN Insumo i ON i.id_insumo = r.id_insumo
    AND i.NIT_restaurante = r.NIT_restaurante
LEFT JOIN (
    SELECT rec.NIT_restaurante, rec.id_insumo,
           SUM(dp.cantidad * rec.cantidad) AS comprometido
    FROM Pedido pe
    JOIN Detalle_Pedido dp ON dp.num_pedido = pe.num_pedido
        AND dp.NIT_restaurante = pe.NIT_restaurante
    JOIN Receta rec ON rec.num_serial_producto = dp.num_serial_producto
        AND rec.NIT_restaurante = dp.NIT_restaurante
    WHERE pe.NIT_restaurante = %s
      AND pe.estado_pedido NOT IN ('Cancelado', 'Cerrado')
      AND NOT EXISTS (
          SELECT 1 FROM Factura f WHERE f.num_pedido = pe.num_pedido
            AND f.NIT_restaurante = pe.NIT_restaurante
      )
    GROUP BY rec.NIT_restaurante, rec.id_insumo
) res ON res.id_insumo = i.id_insumo
    AND res.NIT_restaurante = i.NIT_restaurante
WHERE p.NIT_restaurante = %s
"""


def consulta_productos(nit, categoria=None):
    sql = SQL_PRODUCTOS
    params = (nit, nit)
    if categoria is not None:
        sql += " AND p.categoria_plato = %s"
        params += (categoria,)
    return sql + " ORDER BY p.nombre, p.num_serial, r.id_insumo", params


def decimal(valor):
    # MariaDB/PyMySQL devuelve Decimal. str permite además probar con SQLite.
    return Decimal(str(valor))


def preparar_productos(filas):
    """Agrupa ingredientes y devuelve únicamente datos públicos del menú."""
    grupos = {}
    for fila in filas:
        grupos.setdefault(fila['num_serial'], []).append(fila)
    salida = []
    for grupo in grupos.values():
        p = grupo[0]
        motivo = None
        limite = 0
        if str(p['disponibilidad']).strip().casefold() != 'disponible':
            motivo = 'ProductoDeshabilitado'
        elif p['ingrediente_receta'] is None:
            motivo = 'SinReceta'
        else:
            capacidades = []
            for fila in grupo:
                if (fila['id_insumo'] is None or fila['cantidad_receta'] is None
                        or fila['cantidad_disponible'] is None
                        or decimal(fila['cantidad_receta']) <= 0):
                    motivo = 'RecetaInvalida'
                    break
                utilizable = max(Decimal(0), decimal(fila['cantidad_disponible'])
                                 - max(Decimal(0), decimal(fila['comprometido'])))
                capacidades.append(int(utilizable // decimal(fila['cantidad_receta'])))
            if motivo is None:
                limite = min(capacidades)
                if limite == 0:
                    motivo = 'StockInsuficiente'
        salida.append({
            'num_serial': p['num_serial'], 'nombre': p['nombre'],
            'precio': format(decimal(p['precio']), '.2f'),
            'categoria_plato': p['categoria_plato'],
            'disponibilidad': p['disponibilidad'],
            'disponible': motivo is None,
            'max_unidades': limite,
            'motivo_no_disponible': motivo,
        })
    return salida
