"""Comandas derivadas de Pedido. No altera stock ni factura."""
from datetime import datetime
from backend.pedidos import ErrorPedido, bloquear_restaurante, entero_positivo

ESTADOS = ('Tomado', 'Preparacion', 'Lista')
SQL_CABECERA = '''SELECT p.num_pedido,p.num_mesa,p.id_mesero,m.nombre_empleado AS mesero,
 p.id_cocinero,c.nombre_empleado AS cocinero,p.estado_pedido,p.fecha_hora_pedido,
 p.fecha_inicio_preparacion,p.fecha_lista,p.fecha_entrega
 FROM Pedido p JOIN Empleado m ON m.id_empleado=p.id_mesero AND m.NIT_restaurante=p.NIT_restaurante
 LEFT JOIN Empleado c ON c.id_empleado=p.id_cocinero AND c.NIT_restaurante=p.NIT_restaurante'''
SQL_TABLERO = '''SELECT p.num_pedido,p.num_mesa,p.id_mesero,m.nombre_empleado AS mesero,
 p.id_cocinero,c.nombre_empleado AS cocinero,p.estado_pedido,p.fecha_hora_pedido,
 p.fecha_inicio_preparacion,p.fecha_lista,p.fecha_entrega,
 d.num_serial_producto AS num_serial,pr.nombre,d.cantidad,d.nota_especial
 FROM Pedido p JOIN Empleado m ON m.id_empleado=p.id_mesero AND m.NIT_restaurante=p.NIT_restaurante
 LEFT JOIN Empleado c ON c.id_empleado=p.id_cocinero AND c.NIT_restaurante=p.NIT_restaurante
 LEFT JOIN Detalle_Pedido d ON d.num_pedido=p.num_pedido AND d.NIT_restaurante=p.NIT_restaurante
 LEFT JOIN Producto pr ON pr.num_serial=d.num_serial_producto AND pr.NIT_restaurante=d.NIT_restaurante
 WHERE p.NIT_restaurante=%s AND p.estado_pedido IN ('Tomado','Preparacion','Lista')
 AND NOT EXISTS (SELECT 1 FROM Factura f WHERE f.num_pedido=p.num_pedido AND f.NIT_restaurante=p.NIT_restaurante)
 ORDER BY p.fecha_hora_pedido,p.num_pedido,d.num_serial_producto'''
FECHAS = ('fecha_hora_pedido','fecha_inicio_preparacion','fecha_lista','fecha_entrega')
CAMPOS = ('num_pedido','num_mesa','id_mesero','mesero','id_cocinero','cocinero','estado_pedido',*FECHAS)


def serializar(fila):
    dato = {k: fila[k] for k in CAMPOS}
    for k in FECHAS:
        dato[k] = str(dato[k]) if dato[k] is not None else None
    inicio, fin = dato['fecha_inicio_preparacion'], dato['fecha_lista']
    dato['duracion_preparacion_segundos'] = None
    if inicio and fin:
        diferencia = (datetime.fromisoformat(fin)-datetime.fromisoformat(inicio)).total_seconds()
        if diferencia >= 0:
            dato['duracion_preparacion_segundos'] = int(diferencia)
    return dato


def consultar_tablero(conexion,nit):
    """Una sola consulta: encabezados y detalles de comandas sin facturar."""
    with conexion.cursor() as cursor:
        cursor.execute(SQL_TABLERO,(nit,))
        filas=cursor.fetchall()
    agrupados={}
    for fila in filas:
        numero=fila['num_pedido']
        if numero not in agrupados:
            agrupados[numero]={**serializar(fila),'productos':[]}
        if fila['num_serial'] is not None:
            agrupados[numero]['productos'].append({k:fila[k] for k in ('num_serial','nombre','cantidad','nota_especial')})
    columnas={s:[] for s in ESTADOS}
    for pedido in agrupados.values():
        columnas[pedido['estado_pedido']].append(pedido)
    return {'total':len(agrupados),'resumen':{s:len(v) for s,v in columnas.items()},'comandas':columnas}


def cambiar_estado(conexion,nit,empleado,numero,accion):
    """Mismo bloqueo por restaurante que registro de pedidos (etapa 2.5)."""
    if not entero_positivo(numero) or accion not in ('iniciar','lista','entregar'):
        raise ErrorPedido('Accion o numero de pedido no valido.')
    rol='Mesero' if accion=='entregar' else 'Cocinero'
    try:
        conexion.begin()
        with conexion.cursor() as cursor:
            bloquear_restaurante(cursor,nit)
            # Identificador SQL proviene exclusivamente de constantes, no del cliente.
            cursor.execute(f'''SELECT e.id_empleado FROM Empleado e JOIN {rol} r
              ON r.id_empleado=e.id_empleado AND r.NIT_restaurante=e.NIT_restaurante
              WHERE e.NIT_restaurante=%s AND e.id_empleado=%s AND e.activo=1 FOR UPDATE''',(nit,empleado))
            if not cursor.fetchone():
                raise ErrorPedido('Empleado no habilitado para esta accion.',403)
            cursor.execute('''SELECT num_pedido,id_mesero,id_cocinero,estado_pedido,
              fecha_inicio_preparacion,fecha_lista FROM Pedido
              WHERE NIT_restaurante=%s AND num_pedido=%s FOR UPDATE''',(nit,numero))
            pedido=cursor.fetchone()
            if not pedido or (accion=='entregar' and pedido['id_mesero']!=empleado):
                raise ErrorPedido('Pedido no encontrado.',404)
            cursor.execute('SELECT num_pedido FROM Factura WHERE NIT_restaurante=%s AND num_pedido=%s FOR UPDATE',(nit,numero))
            if cursor.fetchone():
                raise ErrorPedido('El pedido ya esta facturado.',409)
            esperado={'iniciar':'Tomado','lista':'Preparacion','entregar':'Lista'}[accion]
            if pedido['estado_pedido']!=esperado:
                raise ErrorPedido(f'La accion requiere estado {esperado}.',409)
            if accion=='iniciar':
                if pedido['id_cocinero'] is not None or pedido['fecha_inicio_preparacion'] is not None:
                    raise ErrorPedido('La comanda ya tiene datos de preparacion.',409)
                cursor.execute('SELECT num_pedido FROM Detalle_Pedido WHERE NIT_restaurante=%s AND num_pedido=%s LIMIT 1',(nit,numero))
                if not cursor.fetchone():
                    raise ErrorPedido('La comanda no tiene productos.',409)
                cursor.execute('''UPDATE Pedido SET estado_pedido='Preparacion',id_cocinero=%s,
                  fecha_inicio_preparacion=NOW() WHERE NIT_restaurante=%s AND num_pedido=%s''',(empleado,nit,numero))
            elif accion=='lista':
                if pedido['id_cocinero']!=empleado:
                    raise ErrorPedido('Solo el cocinero asignado puede finalizar la comanda.',403)
                if pedido['fecha_inicio_preparacion'] is None:
                    raise ErrorPedido('No existe hora de inicio de preparacion.',409)
                cursor.execute('''UPDATE Pedido SET estado_pedido='Lista',fecha_lista=NOW()
                  WHERE NIT_restaurante=%s AND num_pedido=%s''',(nit,numero))
            else:
                if pedido['fecha_lista'] is None:
                    raise ErrorPedido('No existe hora de finalizacion.',409)
                cursor.execute('''UPDATE Pedido SET estado_pedido='Entregado',fecha_entrega=NOW()
                  WHERE NIT_restaurante=%s AND num_pedido=%s''',(nit,numero))
            cursor.execute(SQL_CABECERA+' WHERE p.NIT_restaurante=%s AND p.num_pedido=%s',(nit,numero))
            resultado=serializar(cursor.fetchone())
        conexion.commit()
        return resultado
    except Exception:
        conexion.rollback()
        raise
