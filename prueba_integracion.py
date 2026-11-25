"""Prueba E2E local: crea UNA venta académica, nunca reintenta escrituras."""
import getpass
import json
import secrets
import sys
from datetime import datetime
from decimal import Decimal
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import (Request, build_opener, HTTPCookieProcessor,
                            ProxyHandler, HTTPRedirectHandler)
from urllib.parse import urlencode

BASE = 'http://127.0.0.1:5000'
NIT = '900123456-1'
D = Decimal


class Fallo(Exception):
    pass


def verificar(condicion, mensaje):
    if not condicion:
        raise Fallo(mensaje)


class SinRedireccion(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Cliente:
    def __init__(self):
        self.opener = build_opener(ProxyHandler({}), SinRedireccion(), HTTPCookieProcessor(CookieJar()))

    def pedir(self, ruta, datos=None, esperado=200):
        verificar(ruta.startswith('/api/') and not ruta.startswith('//'), 'Ruta no permitida.')
        cuerpo = None if datos is None else json.dumps(datos).encode('utf-8')
        req = Request(BASE + ruta, data=cuerpo, headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        try:
            with self.opener.open(req, timeout=20) as resp:
                codigo, raw = resp.status, resp.read()
        except HTTPError as e:
            codigo, raw = e.code, e.read()
            e.close()
        try:
            resultado = json.loads(raw)
        except (ValueError, UnicodeError):
            raise Fallo(f'{ruta}: respuesta no JSON (HTTP {codigo}).') from None
        verificar(codigo == esperado, f'{ruta}: HTTP {codigo}; esperado {esperado}. Revisa la terminal Flask.')
        verificar(isinstance(resultado, dict), f'{ruta}: respuesta inesperada.')
        return resultado


def sql(consulta, parametros=()):
    # Se usa la conexión existente únicamente para SELECT, no para escrituras.
    from backend.db import get_connection
    c = get_connection()
    try:
        with c.cursor() as cursor:
            cursor.execute(consulta, parametros)
            return cursor.fetchall()
    finally:
        c.close()


def mapa_stock(respuesta):
    return {x['id_insumo']: tuple(D(x[k]) for k in ('cantidad_disponible', 'comprometido', 'utilizable')) for x in respuesta['insumos']}


def monto_producto(respuesta, serial):
    return next((int(x['unidades']) for x in respuesta['productos'] if x['num_serial'] == serial), 0)


def consumo_insumo(respuesta, insumo):
    return next((D(x['cantidad_consumida']) for x in respuesta['insumos'] if x['id_insumo'] == insumo), D(0))


def comprobar_stock(antes, despues, receta, fase):
    verificar(antes.keys() == despues.keys(), 'Cambió el conjunto de insumos.')
    for insumo, (fis, res, util) in antes.items():
        consumo = receta.get(insumo, D(0))
        esperado = (fis, res + consumo, max(D(0), fis-res-consumo)) if fase == 'reserva' else (fis-consumo, res, max(D(0), fis-consumo-res))
        verificar(despues[insumo] == esperado, f'Stock inesperado del insumo {insumo} en fase {fase}.')


def ejecutar(log):
    anon = Cliente()
    verificar(anon.pedir('/api/estado')['base_datos'] == 'restaurante_pro_max', 'La API no apunta a la BD académica esperada.')
    datos_bd = sql('SELECT DATABASE() AS bd, DATE(NOW()) AS fecha')[0]
    verificar(datos_bd['bd'] == 'restaurante_pro_max', 'La conexión local no apunta a la BD académica.')
    fecha = str(datos_bd['fecha'])
    q = '?' + urlencode({'desde': fecha, 'hasta': fecha})
    log('Conexión API y MariaDB: correcta; fecha de prueba ' + fecha)
    perfiles = [('cperez','Mesero','salon'),('pchef','Cocinero','cocina'),('ccaja','Cajero','caja'),('rjefe','Administrador','administracion')]
    clientes = {}
    identidades = {}
    for usuario, rol, modulo in perfiles:
        cliente = Cliente()
        clave = getpass.getpass(f'Contraseña de {usuario}: ')
        try:
            empleado = cliente.pedir('/api/auth/login', {'usuario': usuario, 'contrasena': clave})['empleado']
        finally:
            del clave
        verificar(empleado['usuario_software'] == usuario and empleado['NIT_restaurante'] == NIT and rol in empleado['roles'], f'Identidad/rol incorrecto de {usuario}.')
        verificar(cliente.pedir('/api/auth/me')['empleado'] == empleado, f'Sesión inválida de {usuario}.')
        clientes[rol] = cliente
        identidades[rol] = empleado
        for _, otro, ruta in perfiles:
            cliente.pedir(f'/api/{ruta}/acceso', esperado=200 if otro in empleado['roles'] else 403)
        log(f'Autenticación y matriz de permisos: {usuario}, {rol}, correcta.')
    for _, _, modulo in perfiles:
        anon.pedir(f'/api/{modulo}/acceso', esperado=401)
    anon.pedir('/api/auth/login', {'usuario':'usuario_e2e_inexistente', 'contrasena':'clave_de_prueba_invalida'}, esperado=401)
    log('Acceso anónimo y credenciales inválidas: rechazados.')
    salon, cocina, caja, admin = (clientes[r] for r in ('Mesero','Cocinero','Cajero','Administrador'))
    salon.pedir('/api/salon/categorias')
    mesas = salon.pedir('/api/salon/mesas')['mesas']
    libres = [m['num_mesa'] for m in mesas if m['activa'] and m['estado_mesa']=='Libre']
    verificar(bool(libres), 'No hay mesas libres. No se escribió ningún pedido.')
    mesa = 6 if 6 in libres else libres[0]
    disponibles = [p for p in salon.pedir('/api/salon/productos')['productos'] if p['disponible'] and p['max_unidades']>=1 and D(p['precio'])>0]
    verificar(bool(disponibles), 'No hay productos disponibles con precio positivo.')
    p = next((p for p in disponibles if p['num_serial']==105), disponibles[0])
    serial, total = p['num_serial'], D(p['precio'])
    receta = {x['id_insumo']: D(x['cantidad']) for x in sql('SELECT id_insumo,cantidad FROM Receta WHERE NIT_restaurante=%s AND num_serial_producto=%s',(NIT,serial))}
    verificar(bool(receta) and all(v>0 for v in receta.values()), 'Receta no válida.')
    stock0 = mapa_stock(admin.pedir('/api/administracion/inventario'))
    ventas0 = admin.pedir('/api/administracion/reportes/ventas'+q)['resumen']
    prod0 = admin.pedir('/api/administracion/reportes/productos'+q)
    cons0 = admin.pedir('/api/administracion/reportes/consumo'+q)
    cierre0 = admin.pedir('/api/administracion/reportes/cierre-caja'+q)
    admin.pedir('/api/administracion/inventario/alertas')
    admin.pedir('/api/administracion/dashboard'+q)
    # La marca permite localizar un pedido aunque se pierda la respuesta HTTP.
    marca = 'DEMO E2E ' + secrets.token_hex(6)
    log(f'Plan de prueba: mesa {mesa}, producto {serial} ({p["nombre"]}), 1 unidad, total {total:.2f} COP, marca {marca}.')
    print('Se registrará una venta académica permanente y se consumirá una unidad de producto. No se procesa dinero real.')
    verificar(input('Escribe SI para continuar con la escritura: ').strip()=='SI', 'Cancelado antes de escribir.')
    # Ninguna otra sesión debe modificar datos durante la prueba.
    salon.pedir('/api/salon/pedidos', {'num_mesa':mesa,'productos':[]}, esperado=400)
    log('Pedido vacío: rechazado.')
    pedido = salon.pedir('/api/salon/pedidos', {'num_mesa':mesa,'productos':[{'num_serial':serial,'cantidad':1,'nota_especial':marca}]}, esperado=201)['pedido']
    n = pedido['num_pedido']
    log(f'Pedido registrado: {n}. NO repetir automáticamente si hay un fallo posterior.')
    verificar(pedido['estado_pedido']=='Tomado' and pedido['num_mesa']==mesa and D(pedido['subtotal'])==total, 'Pedido no coincide con la solicitud.')
    detalle = salon.pedir(f'/api/salon/pedidos/{n}')['pedido']
    verificar(len(detalle['productos'])==1 and detalle['productos'][0]['nota_especial']==marca and detalle['productos'][0]['cantidad']==1 and detalle['productos'][0]['num_serial']==serial and D(detalle['subtotal'])==total, 'Detalle de pedido no coincide.')
    verificar(any(m['num_mesa']==mesa and m['estado_mesa']=='Ocupada' for m in salon.pedir('/api/salon/mesas')['mesas']), 'Mesa no ocupada.')
    comprobar_stock(stock0,mapa_stock(admin.pedir('/api/administracion/inventario')),receta,'reserva')
    log('Detalle, subtotal, mesa ocupada y reserva sin descuento físico: correctos.')
    tablero = cocina.pedir('/api/cocina/comandas')['comandas']
    verificar(any(x['num_pedido']==n and any(d['nota_especial']==marca for d in x['productos']) for x in tablero['Tomado']), 'Comanda o nota no visible en cocina.')
    cocina.pedir(f'/api/cocina/comandas/{n}/lista', {}, esperado=409)
    caja.pedir(f'/api/caja/pedidos/{n}/precuenta', esperado=409)
    salon.pedir(f'/api/cocina/comandas/{n}/iniciar', {}, esperado=403)
    log('Salto de estado, cobro anticipado y modificación sin rol: rechazados.')
    inicio = cocina.pedir(f'/api/cocina/comandas/{n}/iniciar', {})['pedido']
    verificar(inicio['estado_pedido']=='Preparacion' and inicio['id_cocinero']==identidades['Cocinero']['id_empleado'] and inicio['fecha_inicio_preparacion'], 'Inicio de cocina incorrecto.')
    lista = cocina.pedir(f'/api/cocina/comandas/{n}/lista', {})['pedido']
    verificar(lista['estado_pedido']=='Lista' and lista['fecha_lista'] and lista['duracion_preparacion_segundos'] is not None and lista['duracion_preparacion_segundos']>=0, 'Finalización de cocina incorrecta.')
    verificar(salon.pedir(f'/api/salon/pedidos/{n}')['pedido']['estado_pedido']=='Lista', 'Salón no ve el cambio de estado.')
    entrega = salon.pedir(f'/api/salon/pedidos/{n}/entregar', {})['pedido']
    verificar(entrega['estado_pedido']=='Entregado' and entrega['fecha_entrega'], 'Entrega incorrecta.')
    verificar(any(x['num_pedido']==n for x in caja.pedir('/api/caja/pendientes')['pedidos']), 'Pedido no disponible en caja.')
    log('Cocina, fechas, sincronización con salón y entrega: correctas.')
    pre = caja.pedir(f'/api/caja/pedidos/{n}/precuenta')
    verificar(D(pre['total'])==total, 'Precuenta incorrecta.')
    caja.pedir(f'/api/caja/pedidos/{n}/pagar', {'metodo_pago':'Efectivo','monto_recibido':'0.00'}, esperado=409)
    verificar(not sql('SELECT id_factura FROM Factura WHERE NIT_restaurante=%s AND num_pedido=%s',(NIT,n)), 'Pago insuficiente generó factura.')
    comprobar_stock(stock0,mapa_stock(admin.pedir('/api/administracion/inventario')),receta,'reserva')
    log('Precuenta correcta; pago insuficiente rechazado sin factura ni consumo.')
    pago = {'metodo_pago':'Efectivo','monto_recibido':format(total+D(1000),'.2f'),'nombre_cliente':'Consumidor Final'}
    f = caja.pedir(f'/api/caja/pedidos/{n}/pagar',pago,esperado=201)['factura']
    fid = f['id_factura']
    log(f'Factura registrada: {fid}, pedido {n}.')
    verificar(f['estado_pedido']=='Cerrado' and f['estado_mesa']=='Libre' and f['es_demo'] and D(f['total'])==total and D(f['cambio'])==1000, 'Resultado de pago incorrecto.')
    comp = caja.pedir(f'/api/caja/pedidos/{n}/comprobante')['factura']
    verificar(comp['id_factura']==fid and D(comp['total'])==total and comp['es_demo'], 'Comprobante incorrecto.')
    verificar(salon.pedir(f'/api/salon/pedidos/{n}')['pedido']['estado_pedido']=='Cerrado', 'Salón no ve el cierre.')
    verificar(any(m['num_mesa']==mesa and m['estado_mesa']=='Libre' for m in salon.pedir('/api/salon/mesas')['mesas']), 'Mesa no liberada.')
    stock1 = mapa_stock(admin.pedir('/api/administracion/inventario'))
    comprobar_stock(stock0,stock1,receta,'factura')
    log('Pago, cambio, comprobante, cierre y consumo físico: correctos.')
    caja.pedir(f'/api/caja/pedidos/{n}/pagar',pago,esperado=409)
    verificar(mapa_stock(admin.pedir('/api/administracion/inventario'))==stock1, 'Doble pago cambió el inventario.')
    facturas = sql('SELECT id_factura,valor_total FROM Factura WHERE NIT_restaurante=%s AND num_pedido=%s',(NIT,n))
    verificar(len(facturas)==1 and facturas[0]['id_factura']==fid and D(facturas[0]['valor_total'])==total, 'Factura no única o importe incorrecto en MariaDB.')
    movimientos = sql('SELECT id_movimiento,id_insumo,tipo,cantidad,id_empleado FROM Movimiento_Inventario WHERE NIT_restaurante=%s AND id_factura=%s',(NIT,fid))
    verificar(len(movimientos)==len(receta) and {x['id_insumo']:D(x['cantidad']) for x in movimientos}==receta and all(x['tipo']=='Salida' and x['id_empleado']==identidades['Cajero']['id_empleado'] for x in movimientos), 'Movimientos de factura incorrectos.')
    log('Doble pago rechazado; factura única y movimientos exactos en MariaDB: ' + ', '.join(str(m['id_movimiento']) for m in movimientos))
    verificar(str(f['fecha_emision'])[:10]==fecha and str(sql('SELECT DATE(NOW()) AS fecha')[0]['fecha'])==fecha, 'Cambió el día durante la prueba; verifica los reportes manualmente, no repitas el pago.')
    ventas = admin.pedir('/api/administracion/reportes/ventas'+q)['resumen']
    verificar(ventas['facturas']==ventas0['facturas']+1 and D(ventas['ventas_totales'])==D(ventas0['ventas_totales'])+total, 'Incremento de ventas incorrecto.')
    prod = admin.pedir('/api/administracion/reportes/productos'+q)
    verificar(monto_producto(prod,serial)==monto_producto(prod0,serial)+1, 'Ranking de productos incorrecto.')
    cons = admin.pedir('/api/administracion/reportes/consumo'+q)
    for k,v in receta.items():
        verificar(consumo_insumo(cons,k)==consumo_insumo(cons0,k)+v, f'Reporte de consumo incorrecto: {k}.')
    cierre = admin.pedir('/api/administracion/reportes/cierre-caja'+q)
    verificar(cierre['facturas']==cierre0['facturas']+1 and D(cierre['total'])==D(cierre0['total'])+total, 'Cierre de caja incorrecto.')
    dash = admin.pedir('/api/administracion/dashboard'+q)
    verificar(dash['ventas']==ventas, 'Dashboard no coincide con ventas.')
    log('Ventas, ranking, consumo, cierre de caja y dashboard: correctos.')
    for rol, cliente in clientes.items():
        cliente.pedir('/api/auth/logout', {})
        cliente.pedir('/api/auth/me', esperado=401)
    log('Cierre de las cuatro sesiones: correcto.')
    log(f'RESULTADO API/BD: APROBADO. Pedido {n}; factura {fid}; mesa {mesa}; fecha {fecha}. Auditoría administrativa pendiente de verificar con SQL.')


def main():
    carpeta = Path(__file__).resolve().parent / 'evidencias'
    carpeta.mkdir(exist_ok=True)
    ruta = carpeta / ('integracion_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '.txt')
    with ruta.open('x',encoding='utf-8') as archivo:
        def log(m):
            print(m, flush=True)
            archivo.write(m+'\n'); archivo.flush()
        log('L&D | Etapa 2.10 | Prueba de integración local')
        log('Solo en BD académica respaldada, sin otros usuarios realizando operaciones.')
        try:
            ejecutar(log)
        except (Exception, KeyboardInterrupt) as e:
            log('RESULTADO: NO APROBADO / interrumpido.')
            # No guardar credenciales ni detalles internos de conexión.
            log(str(e) if isinstance(e,Fallo) else f'Tipo de error: {type(e).__name__}. Consulta terminal Flask/configuración.')
            log('No reejecutar automáticamente. Si hubo escrituras, localizar el pedido por la marca y revisar factura/stock antes de continuar.')
            print('Evidencia:',ruta)
            return 1
    print('Evidencia:',ruta)
    return 0


if __name__=='__main__':
    sys.exit(main())
