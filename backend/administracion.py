"""Rutas administrativas de inventario y reportes."""
from flask import Blueprint,current_app,g,jsonify,request
from backend.db import get_connection
from backend.permisos import requiere_roles
from backend.pedidos import ErrorPedido, MAX_INT
from backend.inventario import consultar_inventario,consultar_movimientos,registrar_movimiento

from backend.reportes import periodo, ventas, productos, consumo, cierre_caja, dashboard

bp=Blueprint('administracion',__name__,url_prefix='/api/administracion')


def ejecutar(fn,*args,codigo=200,clave=None):
    conexion=None
    try:
        conexion=get_connection()
        resultado=fn(conexion,g.empleado['NIT_restaurante'],*args)
        return jsonify({clave:resultado} if clave else resultado),codigo
    except ErrorPedido as e:
        return jsonify(error=str(e)),e.estado
    except Exception:
        current_app.logger.exception('Error del modulo administrativo')
        return jsonify(error=('No fue posible consultar la informacion.' if request.method=='GET' else 'Operacion no confirmada. Consulta el historial antes de reintentar.')),503
    finally:
        if conexion is not None: conexion.close()


@bp.get('/inventario')
@requiere_roles('Administrador')
def inventario():
    return ejecutar(consultar_inventario)


@bp.get('/inventario/alertas')
@requiere_roles('Administrador')
def alertas():
    return ejecutar(consultar_inventario,True)


def parametro_entero(nombre,maximo):
    v=request.args.get(nombre)
    if v is None: return None
    if not v.isascii() or not v.isdecimal() or len(v)>19 or not 1<=int(v)<=maximo:
        raise ErrorPedido(f'Parametro {nombre} no valido.')
    return int(v)


@bp.get('/inventario/movimientos')
@requiere_roles('Administrador')
def movimientos():
    try:
        insumo=parametro_entero('id_insumo',MAX_INT)
        antes=parametro_entero('antes_de',9223372036854775807)
    except ErrorPedido as e: return jsonify(error=str(e)),e.estado
    return ejecutar(consultar_movimientos,insumo,antes)


@bp.post('/inventario/movimientos')
@requiere_roles('Administrador')
def registrar():
    if not request.is_json: return jsonify(error='Se requiere application/json.'),415
    if request.content_length is not None and request.content_length>4096:
        return jsonify(error='Solicitud demasiado grande.'),413
    return ejecutar(registrar_movimiento,g.empleado['id_empleado'],request.get_json(silent=True),codigo=201,clave='movimiento')


# Etapa 2.9: reportes de solo lectura, conservando las rutas de inventario.


def reporte(fn):
    try:
        if set(request.args)-{'desde','hasta'} or any(len(request.args.getlist(k))!=1 for k in request.args):
            raise ErrorPedido('Solo se permiten desde y hasta, una vez cada uno.')
        rango=periodo(request.args.get('desde'),request.args.get('hasta'))
    except ErrorPedido as e:
        return jsonify(error=str(e)),e.estado
    return ejecutar(fn,rango)


@bp.get('/dashboard')
@requiere_roles('Administrador')
def dashboard_api():
    return reporte(dashboard)


@bp.get('/reportes/ventas')
@requiere_roles('Administrador')
def ventas_api():
    return reporte(ventas)


@bp.get('/reportes/productos')
@requiere_roles('Administrador')
def productos_api():
    return reporte(productos)


@bp.get('/reportes/consumo')
@requiere_roles('Administrador')
def consumo_api():
    return reporte(consumo)


@bp.get('/reportes/cierre-caja')
@requiere_roles('Administrador')
def cierre_caja_api():
    return reporte(cierre_caja)

# Etapa 3.7: catálogo, usuarios y exportaciones.
from flask import send_file
from backend.gestion import catalogos, guardar
from backend.exportaciones import TIPOS, pdf, xlsx

@bp.get('/gestion')
@requiere_roles('Administrador')
def gestion_api():
    return ejecutar(catalogos)

@bp.post('/gestion/<accion>')
@requiere_roles('Administrador')
def guardar_api(accion):
    if not request.is_json:return jsonify(error='Se requiere application/json.'),415
    if request.content_length is not None and request.content_length>32768:return jsonify(error='Solicitud demasiado grande.'),413
    return ejecutar(guardar,g.empleado['id_empleado'],accion,request.get_json(silent=True))

@bp.get('/reportes/<tipo>/exportar/<formato>')
@requiere_roles('Administrador')
def exportar_api(tipo,formato):
    if tipo not in TIPOS or formato not in ('pdf','xlsx'):return jsonify(error='Formato o informe no válido.'),404
    con=None
    try:
        if set(request.args)-{'desde','hasta'} or any(len(request.args.getlist(k))!=1 for k in request.args):raise ErrorPedido('Solo se permiten desde y hasta.')
        p=periodo(request.args.get('desde'),request.args.get('hasta'))
        con=get_connection(); j=TIPOS[tipo][1](con,g.empleado['NIT_restaurante'],p)
        archivo=(pdf if formato=='pdf' else xlsx)(tipo,j)
        r=send_file(archivo,as_attachment=True,download_name=f'{tipo}_{p[0]}_{p[1]}.{formato}',mimetype='application/pdf' if formato=='pdf' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        r.headers['Cache-Control']='no-store'; return r
    except ErrorPedido as e:return jsonify(error=str(e)),e.estado
    except Exception:
        current_app.logger.exception('Error de exportación')
        return jsonify(error='No fue posible generar el archivo.'),503
    finally:
        if con is not None:con.close()
