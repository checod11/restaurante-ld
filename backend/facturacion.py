"""Caja local: venta POS académica y consumo de inventario en una transacción."""
from collections import defaultdict
from decimal import Decimal
import re
from backend.pedidos import ErrorPedido, bloquear_restaurante, entero_positivo, MAX_INT, MAX_SUBTOTAL, SQL_DETALLE
from backend.catalogo import decimal

METODOS = ('Efectivo', 'Tarjeta', 'Nequi')
SQL_PENDIENTES = '''SELECT p.num_pedido,p.num_mesa,p.id_mesero,p.fecha_hora_pedido,p.estado_pedido
FROM Pedido p WHERE p.NIT_restaurante=%s AND p.estado_pedido='Entregado'
AND NOT EXISTS (SELECT 1 FROM Factura f WHERE f.num_pedido=p.num_pedido AND f.NIT_restaurante=p.NIT_restaurante)'''


def dinero(valor):
    return format(valor, '.2f')


def validar_pago(datos):
    if (not isinstance(datos, dict) or not {'metodo_pago','monto_recibido'} <= set(datos)
            or set(datos)-{'metodo_pago','monto_recibido','nombre_cliente'}):
        raise ErrorPedido('Envia metodo_pago, monto_recibido y nombre_cliente opcional.')
    metodo = datos['metodo_pago']
    if metodo not in METODOS:
        raise ErrorPedido('Metodo de pago no valido.')
    valor = datos['monto_recibido']
    # Preferir cadenas decimales: sin notación exponencial ni redondeo implícito.
    if type(valor) not in (str,int,float) or not re.fullmatch(r'[0-9]{1,10}(?:\.[0-9]{1,2})?',str(valor)):
        raise ErrorPedido('Monto recibido no valido; usa hasta dos decimales.')
    monto = Decimal(str(valor))
    if monto > MAX_SUBTOTAL:
        raise ErrorPedido('Monto fuera del limite.')
    cliente = datos.get('nombre_cliente','Consumidor Final')
    if not isinstance(cliente,str) or len(cliente)>100 or not cliente.strip():
        raise ErrorPedido('Nombre de cliente no valido.')
    return metodo,monto,cliente.strip()


def detalle_y_total(cursor,nit,numero):
    cursor.execute(SQL_DETALLE,(nit,numero))
    filas=cursor.fetchall()
    if not filas:
        raise ErrorPedido('Pedido sin productos.',409)
    detalle=[]; subtotal=Decimal(0)
    for d in filas:
        if d['precio_unitario'] is None or not entero_positivo(d['cantidad']):
            raise ErrorPedido('Pedido sin precio historico o cantidad valida.',409)
        precio=decimal(d['precio_unitario'])
        if not precio.is_finite() or precio<0:
            raise ErrorPedido('Precio historico no valido.',409)
        importe=precio*d['cantidad']; subtotal+=importe
        detalle.append({**d,'precio_unitario':dinero(precio),'subtotal':dinero(importe)})
    if not 0<subtotal<=MAX_SUBTOTAL:
        raise ErrorPedido('Total fuera del limite de facturacion.',409)
    return detalle,subtotal


def consultar_pendientes(conexion,nit):
    with conexion.cursor() as c:
        c.execute(SQL_PENDIENTES+' ORDER BY p.fecha_hora_pedido,p.num_pedido',(nit,))
        filas=c.fetchall()
    return {'total':len(filas),'pedidos':[{**f,'fecha_hora_pedido':str(f['fecha_hora_pedido'])} for f in filas]}


def pedido_para_cobrar(c,nit,numero,bloquear=False):
    c.execute('SELECT num_pedido,num_mesa,id_mesero,estado_pedido FROM Pedido WHERE NIT_restaurante=%s AND num_pedido=%s'+(' FOR UPDATE' if bloquear else ''),(nit,numero))
    p=c.fetchone()
    if not p: raise ErrorPedido('Pedido no encontrado.',404)
    c.execute('SELECT id_factura FROM Factura WHERE NIT_restaurante=%s AND num_pedido=%s',(nit,numero))
    if c.fetchone(): raise ErrorPedido('Pedido ya facturado. Consulta el comprobante.',409)
    if p['estado_pedido']!='Entregado': raise ErrorPedido('Solo se facturan pedidos entregados.',409)
    return p


def precuenta(conexion,nit,numero):
    with conexion.cursor() as c:
        p=pedido_para_cobrar(c,nit,numero)
        items,total=detalle_y_total(c,nit,numero)
    return {**p,'productos':items,'subtotal':dinero(total),'impuesto_adicional':'0.00','total':dinero(total),'tipo_documento':'Factura POS','es_demo':True}


def consumo_receta(c,nit,items):
    """Agrega cantidades por insumo; no usa el precio ni la disponibilidad actuales."""
    consumo=defaultdict(lambda:Decimal(0))
    for item in items:
        c.execute('SELECT id_insumo,cantidad FROM Receta WHERE NIT_restaurante=%s AND num_serial_producto=%s ORDER BY id_insumo',(nit,item['num_serial']))
        receta=c.fetchall()
        if not receta: raise ErrorPedido('Producto sin receta registrada.',409)
        for r in receta:
            cantidad=decimal(r['cantidad'])
            if not cantidad.is_finite() or cantidad<=0:
                raise ErrorPedido('Receta no valida.',409)
            consumo[r['id_insumo']]+=cantidad*item['cantidad']
    for insumo, cantidad in sorted(consumo.items()):
        c.execute('SELECT cantidad_disponible FROM Insumo WHERE NIT_restaurante=%s AND id_insumo=%s FOR UPDATE',(nit,insumo))
        fila=c.fetchone()
        if not fila or cantidad>decimal(fila['cantidad_disponible']) or cantidad>Decimal('99999999.99'):
            raise ErrorPedido(f'Stock insuficiente del insumo {insumo}. No se registro el pago.',409)
    return consumo


def facturar(conexion,nit,cajero,numero,datos):
    metodo,monto,cliente=validar_pago(datos)
    try:
        conexion.begin()
        with conexion.cursor() as c:
            bloquear_restaurante(c,nit)
            c.execute('''SELECT e.id_empleado FROM Empleado e JOIN Cajero ca ON ca.id_empleado=e.id_empleado AND ca.NIT_restaurante=e.NIT_restaurante
                         WHERE e.NIT_restaurante=%s AND e.id_empleado=%s AND e.activo=1''',(nit,cajero))
            if not c.fetchone(): raise ErrorPedido('Cajero no habilitado.',403)
            p=pedido_para_cobrar(c,nit,numero,True)
            items,total=detalle_y_total(c,nit,numero)
            if monto<total or (metodo!='Efectivo' and monto!=total):
                raise ErrorPedido('Monto insuficiente o diferente del total para pago no efectivo.',409)
            consumo=consumo_receta(c,nit,items)
            c.execute('SELECT COALESCE(MAX(id_factura),0) AS ultimo FROM Factura WHERE NIT_restaurante=%s',(nit,))
            id_factura=max(0,c.fetchone()['ultimo'])+1
            if id_factura>MAX_INT: raise ErrorPedido('Numeracion de facturas agotada.',409)
            c.execute('''INSERT INTO Factura (id_factura,NIT_restaurante,num_pedido,id_cajero,nombre_cliente,valor_total,subvalor_total,fecha_emision,metodo_pago,tipo_documento,estado_validacion,monto_recibido)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,NOW(),%s,'Factura POS','Demo',%s)''',
                      (id_factura,nit,numero,cajero,cliente,dinero(total),dinero(total),metodo,dinero(monto)))
            for insumo,cantidad in sorted(consumo.items()):
                c.execute('UPDATE Insumo SET cantidad_disponible=cantidad_disponible-%s WHERE NIT_restaurante=%s AND id_insumo=%s',(dinero(cantidad),nit,insumo))
                c.execute('''INSERT INTO Movimiento_Inventario (NIT_restaurante,id_insumo,id_empleado,id_factura,tipo,cantidad,fecha_hora,motivo)
                             VALUES (%s,%s,%s,%s,'Salida',%s,NOW(),'Consumo por facturacion POS demo')''',(nit,insumo,cajero,id_factura,dinero(cantidad)))
            c.execute("UPDATE Pedido SET estado_pedido='Cerrado' WHERE NIT_restaurante=%s AND num_pedido=%s",(nit,numero))
            c.execute('SELECT fecha_emision FROM Factura WHERE NIT_restaurante=%s AND id_factura=%s',(nit,id_factura))
            fecha=str(c.fetchone()['fecha_emision'])
            c.execute('SELECT estado_mesa FROM v_estado_mesas WHERE NIT_restaurante=%s AND num_mesa=%s',(nit,p['num_mesa']))
            mesa=c.fetchone()
            respuesta={'id_factura':id_factura,'num_pedido':numero,'num_mesa':p['num_mesa'],'estado_mesa':mesa['estado_mesa'] if mesa else None,
                       'id_cajero':cajero,'nombre_cliente':cliente,'fecha_emision':fecha,'metodo_pago':metodo,'tipo_documento':'Factura POS','estado_validacion':'Demo',
                       'subtotal':dinero(total),'impuesto_adicional':'0.00','total':dinero(total),'monto_recibido':dinero(monto),'cambio':dinero(monto-total),
                       'estado_pedido':'Cerrado','es_demo':True,'productos':items,'movimientos':[{'id_insumo':k,'cantidad':dinero(v)} for k,v in sorted(consumo.items())]}
        conexion.commit()
        return respuesta
    except Exception:
        conexion.rollback()
        raise


def comprobante(conexion,nit,numero):
    """Solo comprobantes creados por esta demo, no reinterpreta facturas históricas."""
    with conexion.cursor() as c:
        c.execute('''SELECT f.id_factura,f.num_pedido,f.id_cajero,f.nombre_cliente,f.valor_total,f.subvalor_total,f.fecha_emision,f.metodo_pago,f.tipo_documento,f.estado_validacion,f.monto_recibido,p.num_mesa
            FROM Factura f JOIN Pedido p ON p.num_pedido=f.num_pedido AND p.NIT_restaurante=f.NIT_restaurante
            WHERE f.NIT_restaurante=%s AND f.num_pedido=%s AND f.estado_validacion='Demo' ''',(nit,numero))
        f=c.fetchone()
        if not f: raise ErrorPedido('Comprobante de demostracion no encontrado.',404)
        items,_=detalle_y_total(c,nit,numero)
    total=decimal(f['valor_total']); recibido=decimal(f['monto_recibido']); subtotal=decimal(f['subvalor_total'])
    return {**{k:v for k,v in f.items() if k not in ('valor_total','subvalor_total','monto_recibido','fecha_emision')},
            'fecha_emision':str(f['fecha_emision']),'subtotal':dinero(subtotal),'total':dinero(total),'impuesto_adicional':dinero(total-subtotal),
            'monto_recibido':dinero(recibido),'cambio':dinero(recibido-total),'productos':items,'es_demo':True}
