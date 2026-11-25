"""Inventario administrativo. Comparte el bloqueo de pedidos y facturacion."""
import re
from decimal import Decimal
from backend.catalogo import decimal
from backend.pedidos import ErrorPedido, bloquear_restaurante, entero_positivo

MAX_STOCK = Decimal('99999999.99')
TIPOS_MANUALES = {'Entrada', 'AjusteEntrada', 'AjusteSalida'}
SQL_STOCK = '''SELECT i.id_insumo,i.nombre,i.unidad_medida,i.cantidad_disponible,i.cantidad_minima,
       COALESCE(r.comprometido,0) AS comprometido
FROM Insumo i LEFT JOIN (
    SELECT rec.NIT_restaurante,rec.id_insumo,SUM(dp.cantidad*rec.cantidad) AS comprometido
    FROM Pedido p JOIN Detalle_Pedido dp ON dp.num_pedido=p.num_pedido AND dp.NIT_restaurante=p.NIT_restaurante
    JOIN Receta rec ON rec.num_serial_producto=dp.num_serial_producto AND rec.NIT_restaurante=dp.NIT_restaurante
    WHERE p.NIT_restaurante=%s AND p.estado_pedido NOT IN ('Cancelado','Cerrado')
    AND NOT EXISTS (SELECT 1 FROM Factura f WHERE f.num_pedido=p.num_pedido AND f.NIT_restaurante=p.NIT_restaurante)
    GROUP BY rec.NIT_restaurante,rec.id_insumo
) r ON r.id_insumo=i.id_insumo AND r.NIT_restaurante=i.NIT_restaurante
WHERE i.NIT_restaurante=%s'''


def fmt(x):
    return format(decimal(x),'.2f')


def serializar(f):
    fisico=decimal(f['cantidad_disponible']); minimo=decimal(f['cantidad_minima'])
    reserva=max(Decimal(0),decimal(f['comprometido']))
    util=max(Decimal(0),fisico-reserva)
    estado='Agotado' if util==0 else ('Bajo' if util<=minimo else 'Normal')
    return {**{k:f[k] for k in ('id_insumo','nombre','unidad_medida')},
            'cantidad_disponible':fmt(fisico),'cantidad_minima':fmt(minimo),
            'comprometido':fmt(reserva),'utilizable':fmt(util),'estado_stock':estado,
            'reserva_insuficiente':fisico<reserva}


def leer_stock(c,nit,insumo=None):
    sql=SQL_STOCK; params=(nit,nit)
    if insumo is not None:
        sql+=' AND i.id_insumo=%s'; params+=(insumo,)
    c.execute(sql+' ORDER BY i.id_insumo',params)
    return c.fetchall()


def consultar_inventario(conexion,nit,solo_alertas=False):
    with conexion.cursor() as c:
        items=[serializar(f) for f in leer_stock(c,nit)]
    resumen={s:sum(i['estado_stock']==s for i in items) for s in ('Normal','Bajo','Agotado')}
    if solo_alertas:
        items=[i for i in items if i['estado_stock']!='Normal']
    return {'total':len(items),'resumen':resumen,'insumos':items}


def validar_movimiento(datos):
    if not isinstance(datos,dict) or set(datos)!={'id_insumo','tipo','cantidad','motivo'}:
        raise ErrorPedido('Envia id_insumo, tipo, cantidad y motivo.')
    insumo,tipo,cantidad,motivo=(datos[k] for k in ('id_insumo','tipo','cantidad','motivo'))
    if not entero_positivo(insumo): raise ErrorPedido('Identificador de insumo no valido.')
    if not isinstance(tipo,str) or tipo not in TIPOS_MANUALES:
        raise ErrorPedido('Tipo manual no valido. Usa Entrada, AjusteEntrada o AjusteSalida.')
    # Aceptar enteros y cadenas decimales; evitar conversiones binarias de JSON float.
    if type(cantidad) not in (int,str) or not re.fullmatch(r'[0-9]{1,8}(?:\.[0-9]{1,2})?',str(cantidad)):
        raise ErrorPedido('Cantidad positiva con maximo 8 enteros y 2 decimales; usa texto decimal.')
    cantidad=Decimal(str(cantidad))
    if not 0<cantidad<=MAX_STOCK: raise ErrorPedido('Cantidad fuera del rango permitido.')
    if not isinstance(motivo,str) or not 1<=len(motivo.strip())<=150:
        raise ErrorPedido('El motivo es obligatorio (1 a 150 caracteres).')
    return insumo,tipo,cantidad,motivo.strip()


def registrar_movimiento(conexion,nit,empleado,datos):
    insumo,tipo,cantidad,motivo=validar_movimiento(datos)
    try:
        conexion.begin()
        with conexion.cursor() as c:
            bloquear_restaurante(c,nit)
            c.execute('''SELECT e.id_empleado FROM Empleado e JOIN Administrador a
                ON a.id_empleado=e.id_empleado AND a.NIT_restaurante=e.NIT_restaurante
                WHERE e.NIT_restaurante=%s AND e.id_empleado=%s AND e.activo=1 FOR UPDATE''',(nit,empleado))
            if not c.fetchone(): raise ErrorPedido('Administrador no habilitado.',403)
            c.execute('SELECT cantidad_disponible FROM Insumo WHERE NIT_restaurante=%s AND id_insumo=%s FOR UPDATE',(nit,insumo))
            fila=c.fetchone()
            if not fila: raise ErrorPedido('Insumo no encontrado.',404)
            antes=decimal(fila['cantidad_disponible'])
            filas=leer_stock(c,nit,insumo)
            reserva=max(Decimal(0),decimal(filas[0]['comprometido']))
            despues=antes-cantidad if tipo=='AjusteSalida' else antes+cantidad
            if despues<0 or despues>MAX_STOCK:
                raise ErrorPedido('El movimiento deja el stock fuera del rango permitido.',409)
            if tipo=='AjusteSalida' and despues<reserva:
                raise ErrorPedido('El ajuste afecta existencias comprometidas en pedidos abiertos.',409)
            c.execute('UPDATE Insumo SET cantidad_disponible=%s WHERE NIT_restaurante=%s AND id_insumo=%s',(fmt(despues),nit,insumo))
            c.execute('''INSERT INTO Movimiento_Inventario
              (NIT_restaurante,id_insumo,id_empleado,id_factura,tipo,cantidad,fecha_hora,motivo)
              VALUES (%s,%s,%s,NULL,%s,%s,NOW(),%s)''',(nit,insumo,empleado,tipo,fmt(cantidad),motivo))
            # LAST_INSERT_ID es especifico de esta conexion, no depende de otros restaurantes.
            c.execute('SELECT LAST_INSERT_ID() AS id_movimiento')
            identificador=c.fetchone()['id_movimiento']
            actual=serializar(leer_stock(c,nit,insumo)[0])
            respuesta={'id_movimiento':identificador,'id_insumo':insumo,'id_empleado':empleado,
                'tipo':tipo,'cantidad':fmt(cantidad),'motivo':motivo,'id_factura':None,
                'stock_anterior':fmt(antes),'stock_nuevo':fmt(despues),'insumo':actual}
        conexion.commit()
        return respuesta
    except Exception:
        conexion.rollback()
        raise


def consultar_movimientos(conexion,nit,insumo=None,antes_de=None):
    sql='''SELECT m.id_movimiento,m.id_insumo,i.nombre AS insumo,i.unidad_medida,
        m.id_empleado,e.nombre_empleado,m.id_factura,m.tipo,m.cantidad,m.fecha_hora,m.motivo
        FROM Movimiento_Inventario m JOIN Insumo i ON i.id_insumo=m.id_insumo AND i.NIT_restaurante=m.NIT_restaurante
        JOIN Empleado e ON e.id_empleado=m.id_empleado AND e.NIT_restaurante=m.NIT_restaurante
        WHERE m.NIT_restaurante=%s'''; params=(nit,)
    if insumo is not None: sql+=' AND m.id_insumo=%s'; params+=(insumo,)
    if antes_de is not None: sql+=' AND m.id_movimiento<%s'; params+=(antes_de,)
    with conexion.cursor() as c:
        c.execute(sql+' ORDER BY m.id_movimiento DESC LIMIT 101',params)
        filas=c.fetchall()
    mas=len(filas)>100; filas=filas[:100]
    for f in filas:
        f['cantidad']=fmt(f['cantidad']); f['fecha_hora']=str(f['fecha_hora'])
    return {'total':len(filas),'movimientos':filas,'siguiente_antes_de':filas[-1]['id_movimiento'] if mas else None}
