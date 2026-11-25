"""Rutas de caja protegidas por el rol Cajero."""
from flask import Blueprint,current_app,g,jsonify,request
from backend.db import get_connection
from backend.permisos import requiere_roles
from backend.pedidos import ErrorPedido
from backend.facturacion import consultar_pendientes,precuenta,facturar,comprobante

bp=Blueprint('caja',__name__,url_prefix='/api/caja')


def ejecutar(fn,*args,codigo=200,clave=None):
    conexion=None
    try:
        conexion=get_connection()
        resultado=fn(conexion,g.empleado['NIT_restaurante'],*args)
        return jsonify({clave:resultado} if clave else resultado),codigo
    except ErrorPedido as e:
        return jsonify(error=str(e)),e.estado
    except Exception:
        current_app.logger.exception('Error en caja')
        return jsonify(error='Operacion no confirmada. Consulta el comprobante antes de reintentar.'),503
    finally:
        if conexion is not None: conexion.close()


@bp.get('/pendientes')
@requiere_roles('Cajero')
def pendientes():
    return ejecutar(consultar_pendientes)


@bp.get('/pedidos/<int:numero>/precuenta')
@requiere_roles('Cajero')
def consultar_precuenta(numero):
    return ejecutar(precuenta,numero)


@bp.post('/pedidos/<int:numero>/pagar')
@requiere_roles('Cajero')
def pagar(numero):
    if not request.is_json: return jsonify(error='Se requiere application/json.'),415
    if request.content_length is not None and request.content_length>4096: return jsonify(error='Solicitud demasiado grande.'),413
    return ejecutar(facturar,g.empleado['id_empleado'],numero,request.get_json(silent=True),codigo=201,clave='factura')


@bp.get('/pedidos/<int:numero>/comprobante')
@requiere_roles('Cajero')
def consultar_comprobante(numero):
    return ejecutar(comprobante,numero,clave='factura')
