"""Reportes de solo lectura, aislados por NIT y fechas inclusivas."""
import re
from datetime import date, timedelta, datetime
from decimal import Decimal, ROUND_HALF_UP
from backend.catalogo import decimal
from backend.inventario import consultar_inventario
from backend.pedidos import ErrorPedido


def periodo(desde=None, hasta=None):
    if desde is None and hasta is None:
        desde=hasta=date.today().isoformat()
    if not all(isinstance(v,str) and re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}',v) for v in (desde,hasta)):
        raise ErrorPedido('Envia desde y hasta con formato AAAA-MM-DD.')
    try:
        a,b=date.fromisoformat(desde),date.fromisoformat(hasta)
        fin=b+timedelta(days=1)
    except (ValueError,OverflowError):
        raise ErrorPedido('Fecha no valida.') from None
    if a.year<1000 or not 0<=(b-a).days<366:
        raise ErrorPedido('Rango no valido: maximo 366 dias, desde <= hasta.')
    return a.isoformat(),b.isoformat(),fin.isoformat()


def filas(conexion,sql,params):
    with conexion.cursor() as c:
        c.execute(sql,params)
        return c.fetchall()


def monto(v):
    return format(decimal(v).quantize(Decimal('0.01'),rounding=ROUND_HALF_UP),'f')


def limites(nit,p): return (nit,p[0],p[2])
def etiqueta(p): return {'desde':p[0],'hasta':p[1]}


def ventas(conexion,nit,p):
    registros=filas(conexion,'''SELECT DATE(fecha_emision) AS dia, COUNT(*) AS facturas,
       COALESCE(SUM(valor_total),0) AS total, COALESCE(SUM(subvalor_total),0) AS subtotal
       FROM v_resumen_facturacion_pedidos WHERE NIT_restaurante=%s
       AND fecha_emision >= %s AND fecha_emision < %s GROUP BY DATE(fecha_emision) ORDER BY dia''',limites(nit,p))
    mapa={str(r['dia']):r for r in registros}
    serie=[]; d=date.fromisoformat(p[0]); fin=date.fromisoformat(p[1]); total=Decimal(0); sub=Decimal(0); n=0
    while d<=fin:
        dia=d.isoformat(); r=mapa.get(dia,{}); t=decimal(r.get('total',0)); s=decimal(r.get('subtotal',0)); k=int(r.get('facturas',0))
        total+=t; sub+=s; n+=k
        serie.append({'fecha':dia,'facturas':k,'total':monto(t),'subtotal':monto(s)})
        d+=timedelta(days=1)
    return {'periodo':etiqueta(p),'resumen':{'facturas':n,'ventas_totales':monto(total),'subtotal':monto(sub),'ticket_promedio':monto(total/n if n else 0)},'serie_diaria':serie}


def productos(conexion,nit,p):
    registros=filas(conexion,'''SELECT dp.num_serial_producto AS num_serial, pr.nombre, pr.categoria_plato,
       SUM(dp.cantidad) AS unidades, SUM(dp.cantidad*dp.precio_unitario) AS importe_conocido,
       SUM(CASE WHEN dp.precio_unitario IS NULL THEN dp.cantidad ELSE 0 END) AS unidades_sin_precio
       FROM Factura f JOIN Detalle_Pedido dp ON dp.num_pedido=f.num_pedido AND dp.NIT_restaurante=f.NIT_restaurante
       JOIN Producto pr ON pr.num_serial=dp.num_serial_producto AND pr.NIT_restaurante=dp.NIT_restaurante
       WHERE f.NIT_restaurante=%s AND f.fecha_emision >= %s AND f.fecha_emision < %s
       GROUP BY dp.num_serial_producto,pr.nombre,pr.categoria_plato
       ORDER BY unidades DESC,dp.num_serial_producto''',limites(nit,p))
    for r in registros:
        r['unidades']=int(r['unidades']); r['unidades_sin_precio']=int(r['unidades_sin_precio'])
        r['importe_conocido']=None if r['importe_conocido'] is None else monto(r['importe_conocido'])
    return {'periodo':etiqueta(p),'total_unidades':sum(r['unidades'] for r in registros),'productos':registros,
            'nota':'Importe de lineas con precio historico; puede ser parcial y no equivale a ventas totales.'}


def consumo(conexion,nit,p):
    # Solo salidas ligadas a facturas; no reconstruir consumos antiguos con recetas actuales.
    registros=filas(conexion,'''SELECT i.id_insumo,i.nombre,i.unidad_medida,SUM(m.cantidad) AS cantidad_consumida,
       COUNT(*) AS movimientos FROM Movimiento_Inventario m JOIN Insumo i
       ON i.id_insumo=m.id_insumo AND i.NIT_restaurante=m.NIT_restaurante
       WHERE m.NIT_restaurante=%s AND m.fecha_hora >= %s AND m.fecha_hora < %s
       AND m.tipo='Salida' AND m.id_factura IS NOT NULL
       GROUP BY i.id_insumo,i.nombre,i.unidad_medida ORDER BY i.id_insumo''',limites(nit,p))
    for r in registros:r['cantidad_consumida']=monto(r['cantidad_consumida'])
    cobertura=filas(conexion,'''SELECT COUNT(*) AS facturas_sin_movimientos FROM Factura f WHERE f.NIT_restaurante=%s
       AND f.fecha_emision >= %s AND f.fecha_emision < %s AND NOT EXISTS
       (SELECT 1 FROM Movimiento_Inventario m WHERE m.NIT_restaurante=f.NIT_restaurante AND m.id_factura=f.id_factura AND m.tipo='Salida')''',limites(nit,p))[0]
    return {'periodo':etiqueta(p),'insumos':registros,**cobertura,'nota':'Consumo registrado por fecha de movimiento; no incluye ajustes ni reconstruye consumos historicos.'}


def cierre_caja(conexion,nit,p):
    registros=filas(conexion,'''SELECT f.id_cajero,e.nombre_empleado AS cajero,f.metodo_pago,COUNT(*) AS facturas,
       SUM(f.valor_total) AS total,
       SUM(CASE WHEN f.metodo_pago='Efectivo' AND f.monto_recibido IS NOT NULL THEN f.monto_recibido ELSE NULL END) AS efectivo_recibido,
       SUM(CASE WHEN f.metodo_pago='Efectivo' AND f.monto_recibido IS NOT NULL THEN f.monto_recibido-f.valor_total ELSE NULL END) AS cambio,
       SUM(CASE WHEN f.metodo_pago='Efectivo' AND f.monto_recibido IS NULL THEN 1 ELSE 0 END) AS efectivo_sin_dato
       FROM Factura f JOIN Empleado e ON e.id_empleado=f.id_cajero AND e.NIT_restaurante=f.NIT_restaurante
       WHERE f.NIT_restaurante=%s AND f.fecha_emision >= %s AND f.fecha_emision < %s
       GROUP BY f.id_cajero,e.nombre_empleado,f.metodo_pago ORDER BY f.id_cajero,f.metodo_pago''',limites(nit,p))
    metodos={}; total=Decimal(0); n=0
    for r in registros:
        t=decimal(r['total']); total+=t; n+=r['facturas']; k=r['metodo_pago']; metodos[k]=metodos.get(k,Decimal(0))+t
        for campo in ('total','efectivo_recibido','cambio'):
            r[campo]=None if r[campo] is None else monto(r[campo])
        r['efectivo_sin_dato']=int(r['efectivo_sin_dato'])
    return {'periodo':etiqueta(p),'total':monto(total),'facturas':n,'por_metodo':[{'metodo_pago':k,'total':monto(v)} for k,v in sorted(metodos.items())],
            'por_cajero_metodo':registros,'nota':'Resumen de ventas registradas; no equivale a arqueo fisico, saldo inicial ni conciliacion bancaria.'}


def dashboard(conexion,nit,p):
    venta=ventas(conexion,nit,p); caja=cierre_caja(conexion,nit,p); platos=productos(conexion,nit,p)
    mesas={'Libre':0,'Ocupada':0,'Inactiva':0}
    for r in filas(conexion,'''SELECT estado_mesa,COUNT(*) AS total FROM v_estado_mesas WHERE NIT_restaurante=%s GROUP BY estado_mesa''',(nit,)):
        mesas[r['estado_mesa']]=r['total']
    pedidos={s:0 for s in ('Tomado','Preparacion','Lista','Entregado')}
    for r in filas(conexion,'''SELECT p.estado_pedido,COUNT(*) AS total FROM Pedido p WHERE p.NIT_restaurante=%s
       AND p.estado_pedido IN ('Tomado','Preparacion','Lista','Entregado') AND NOT EXISTS
       (SELECT 1 FROM Factura f WHERE f.NIT_restaurante=p.NIT_restaurante AND f.num_pedido=p.num_pedido) GROUP BY p.estado_pedido''',(nit,)):
        pedidos[r['estado_pedido']]=r['total']
    tiempos=filas(conexion,'''SELECT fecha_inicio_preparacion,fecha_lista FROM Pedido WHERE NIT_restaurante=%s
       AND fecha_lista >= %s AND fecha_lista < %s AND fecha_inicio_preparacion IS NOT NULL
       AND fecha_lista >= fecha_inicio_preparacion AND estado_pedido <> 'Cancelado' ''',limites(nit,p))
    segundos=sum((datetime.fromisoformat(str(r['fecha_lista']))-datetime.fromisoformat(str(r['fecha_inicio_preparacion']))).total_seconds() for r in tiempos)
    alertas=consultar_inventario(conexion,nit,True)
    return {'periodo':etiqueta(p),'ventas':venta['resumen'],'serie_diaria':venta['serie_diaria'],'pagos':caja['por_metodo'],
            'productos_mas_vendidos':platos['productos'][:10], 'preparacion':{'muestra':len(tiempos),'promedio_segundos':round(segundos/len(tiempos),2) if tiempos else None},
            'estado_actual':{'mesas':mesas,'pedidos_pendientes':pedidos,'inventario':alertas['resumen'],'alertas':alertas['insumos']}}
