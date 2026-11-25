"""Registro atómico de pedidos. El stock físico se descuenta al facturar."""
from collections import defaultdict
from decimal import Decimal

from backend.catalogo import consulta_productos, preparar_productos, decimal

MAX_INT = 2147483647
MAX_SUBTOTAL = Decimal('9999999999.99')  # DECIMAL(12,2) de Factura


class ErrorPedido(Exception):
    def __init__(self, mensaje, estado=400):
        super().__init__(mensaje)
        self.estado = estado


def entero_positivo(valor, maximo=MAX_INT):
    return type(valor) is int and 1 <= valor <= maximo


def validar_pedido(datos):
    if not isinstance(datos, dict) or set(datos) != {'num_mesa', 'productos'}:
        raise ErrorPedido('Envia num_mesa y productos; no envies precios ni datos de empleado.')
    mesa = datos['num_mesa']
    items = datos['productos']
    if not entero_positivo(mesa):
        raise ErrorPedido('Numero de mesa no valido.')
    if not isinstance(items, list) or not 1 <= len(items) <= 100:
        raise ErrorPedido('El pedido debe tener entre 1 y 100 productos distintos.')
    vistos = set()
    resultado = []
    for item in items:
        if (not isinstance(item, dict) or not {'num_serial', 'cantidad'} <= set(item)
                or set(item) - {'num_serial', 'cantidad', 'nota_especial'}):
            raise ErrorPedido('Cada producto requiere num_serial, cantidad y nota_especial opcional.')
        serial, cantidad = item['num_serial'], item['cantidad']
        if not entero_positivo(serial) or not entero_positivo(cantidad, 1000):
            raise ErrorPedido('Producto o cantidad no valida (1 a 1000 unidades).')
        if serial in vistos:
            raise ErrorPedido('Producto repetido: agrupa su cantidad y usa una sola nota por producto.')
        vistos.add(serial)
        nota = item.get('nota_especial')
        if nota is not None and (not isinstance(nota, str) or len(nota) > 255):
            raise ErrorPedido('La nota especial debe tener maximo 255 caracteres.')
        resultado.append({'num_serial': serial, 'cantidad': cantidad,
                          'nota_especial': (nota.strip() or None) if nota else None})
    return mesa, resultado


def preparar_carrito(filas, items):
    """Valida consumo agregado por ingrediente, incluyendo reservas previas."""
    productos = {p['num_serial']: p for p in preparar_productos(filas)}
    recetas = defaultdict(list)
    for fila in filas:
        recetas[fila['num_serial']].append(fila)
    consumo = defaultdict(lambda: Decimal(0))
    utilizable = {}
    detalle = []
    subtotal = Decimal(0)
    for item in items:
        serial, cantidad = item['num_serial'], item['cantidad']
        p = productos.get(serial)
        if p is None:
            raise ErrorPedido(f'Producto {serial} no encontrado en este restaurante.', 404)
        if not p['disponible'] or cantidad > p['max_unidades']:
            raise ErrorPedido(f'Producto {serial}: no disponible en la cantidad solicitada.', 409)
        precio = decimal(p['precio'])
        if precio < 0:
            raise ErrorPedido(f'Precio invalido del producto {serial}.', 409)
        for r in recetas[serial]:
            insumo = r['id_insumo']
            consumo[insumo] += decimal(r['cantidad_receta']) * cantidad
            utilizable[insumo] = max(Decimal(0), decimal(r['cantidad_disponible'])
                                     - max(Decimal(0), decimal(r['comprometido'])))
        importe = precio * cantidad
        subtotal += importe
        detalle.append({**item, 'nombre': p['nombre'], 'precio_unitario': format(precio, '.2f'),
                        'subtotal': format(importe, '.2f')})
    for insumo, requerido in consumo.items():
        if requerido > utilizable[insumo]:
            raise ErrorPedido(f'Stock insuficiente del insumo {insumo} para el carrito completo.', 409)
    if subtotal > MAX_SUBTOTAL:
        raise ErrorPedido('Subtotal superior al limite de facturacion.', 409)
    return detalle, format(subtotal, '.2f')


def bloquear_restaurante(cursor, nit):
    """Mutex transaccional por restaurante; reutilizar en futuras escrituras."""
    cursor.execute('SELECT NIT, estado_suscripcion_software FROM Restaurante WHERE NIT = %s FOR UPDATE', (nit,))
    fila = cursor.fetchone()
    if not fila or fila['estado_suscripcion_software'] != 'Activo':
        raise ErrorPedido('Restaurante no habilitado.', 403)


def registrar_pedido(conexion, nit, id_mesero, mesa, items):
    """Adquiere bloqueo ANTES de leer reservas y generar el ID compuesto."""
    try:
        conexion.begin()
        with conexion.cursor() as cursor:
            bloquear_restaurante(cursor, nit)
            # Revalidar al empleado dentro de la transacción.
            cursor.execute('''SELECT e.id_empleado FROM Empleado e JOIN Mesero m
                ON m.id_empleado=e.id_empleado AND m.NIT_restaurante=e.NIT_restaurante
                WHERE e.NIT_restaurante=%s AND e.id_empleado=%s AND e.activo=1''', (nit, id_mesero))
            if not cursor.fetchone():
                raise ErrorPedido('Mesero no habilitado.', 403)
            cursor.execute('SELECT activa FROM Mesa WHERE NIT_restaurante=%s AND num_mesa=%s FOR UPDATE', (nit, mesa))
            fila = cursor.fetchone()
            if not fila:
                raise ErrorPedido('Mesa no encontrada.', 404)
            if not fila['activa']:
                raise ErrorPedido('Mesa inactiva.', 409)
            sql, params = consulta_productos(nit)
            cursor.execute(sql, params)
            detalle, subtotal = preparar_carrito(cursor.fetchall(), items)
            # IDs originales no son AUTO_INCREMENT; el bloqueo evita colisiones
            # entre escritores que respeten este protocolo por restaurante.
            cursor.execute('SELECT COALESCE(MAX(num_pedido),0) AS ultimo FROM Pedido WHERE NIT_restaurante=%s', (nit,))
            numero = max(0, cursor.fetchone()['ultimo']) + 1
            if numero > MAX_INT:
                raise ErrorPedido('Numeracion de pedidos agotada.', 409)
            cursor.execute('''INSERT INTO Pedido
                (num_pedido,NIT_restaurante,id_mesero,num_mesa,fecha_hora_pedido,estado_pedido)
                VALUES (%s,%s,%s,%s,NOW(),'Tomado')''', (numero,nit,id_mesero,mesa))
            cursor.executemany('''INSERT INTO Detalle_Pedido
                (num_pedido,num_serial_producto,NIT_restaurante,cantidad,nota_especial,precio_unitario)
                VALUES (%s,%s,%s,%s,%s,%s)''', [
                    (numero,d['num_serial'],nit,d['cantidad'],d['nota_especial'],d['precio_unitario'])
                    for d in detalle])
            cursor.execute('SELECT fecha_hora_pedido FROM Pedido WHERE NIT_restaurante=%s AND num_pedido=%s', (nit,numero))
            fecha = cursor.fetchone()['fecha_hora_pedido']
            respuesta = {'num_pedido': numero, 'num_mesa': mesa, 'id_mesero': id_mesero,
                         'estado_pedido': 'Tomado', 'fecha_hora_pedido': str(fecha),
                         'productos': detalle, 'subtotal': subtotal}
        conexion.commit()
        return respuesta
    except Exception:
        conexion.rollback()
        raise


SQL_PEDIDOS = '''SELECT p.num_pedido,p.num_mesa,p.id_mesero,p.fecha_hora_pedido,p.estado_pedido,
       EXISTS(SELECT 1 FROM Factura f WHERE f.num_pedido=p.num_pedido
              AND f.NIT_restaurante=p.NIT_restaurante) AS facturado
FROM Pedido p WHERE p.NIT_restaurante=%s AND p.id_mesero=%s'''

SQL_DETALLE = '''SELECT d.num_serial_producto AS num_serial,p.nombre,d.cantidad,d.nota_especial,d.precio_unitario
FROM Detalle_Pedido d JOIN Producto p ON p.num_serial=d.num_serial_producto
 AND p.NIT_restaurante=d.NIT_restaurante
WHERE d.NIT_restaurante=%s AND d.num_pedido=%s ORDER BY d.num_serial_producto'''


def serializar_pedido(fila):
    return {**fila, 'fecha_hora_pedido': str(fila['fecha_hora_pedido']), 'facturado': bool(fila['facturado'])}


def consultar_detalle(conexion,nit,mesero,numero):
    with conexion.cursor() as cursor:
        cursor.execute(SQL_PEDIDOS+' AND p.num_pedido=%s', (nit,mesero,numero))
        fila=cursor.fetchone()
        if not fila:
            raise ErrorPedido('Pedido no encontrado.',404)
        cursor.execute(SQL_DETALLE,(nit,numero))
        productos=[]
        subtotal=Decimal(0)
        completo=True
        for d in cursor.fetchall():
            precio=d['precio_unitario']
            importe=None if precio is None else decimal(precio)*d['cantidad']
            if importe is None:
                completo=False
            else:
                subtotal+=importe
            productos.append({**d,'precio_unitario':None if precio is None else format(decimal(precio),'.2f'),
                              'subtotal':None if importe is None else format(importe,'.2f')})
        return {**serializar_pedido(fila),'productos':productos,
                'subtotal':format(subtotal,'.2f') if completo and productos else None}
