"""API de cocina y confirmación de entrega por el mesero."""
from flask import Blueprint, current_app, g, jsonify, request
from backend.db import get_connection
from backend.permisos import requiere_roles
from backend.pedidos import ErrorPedido
from backend.comandas import consultar_tablero, cambiar_estado

bp=Blueprint('comandas',__name__,url_prefix='/api')

@bp.get('/cocina/comandas')
@requiere_roles('Cocinero')
def tablero():
    conexion=None
    try:
        conexion=get_connection()
        return jsonify(consultar_tablero(conexion,g.empleado['NIT_restaurante'])),200
    except Exception:
        current_app.logger.exception('Error al consultar comandas')
        return jsonify(error='Servicio de cocina no disponible.'),503
    finally:
        if conexion is not None:
            conexion.close()


def ejecutar(numero,accion):
    if not request.is_json:
        return jsonify(error='Se requiere Content-Type application/json.'),415
    if request.content_length is not None and request.content_length>4096:
        return jsonify(error='Solicitud demasiado grande.'),413
    if request.get_json(silent=True)!={}:
        return jsonify(error='Envia un objeto JSON vacio; la identidad y fecha se obtienen del servidor.'),400
    conexion=None
    try:
        conexion=get_connection()
        pedido=cambiar_estado(conexion,g.empleado['NIT_restaurante'],g.empleado['id_empleado'],numero,accion)
        return jsonify(mensaje='Estado actualizado.',pedido=pedido),200
    except ErrorPedido as e:
        return jsonify(error=str(e)),e.estado
    except Exception:
        current_app.logger.exception('Error al cambiar estado de comanda')
        return jsonify(error='No se pudo confirmar el cambio. Consulta el estado antes de reintentar.'),503
    finally:
        if conexion is not None:
            conexion.close()

@bp.post('/cocina/comandas/<int:numero>/iniciar')
@requiere_roles('Cocinero')
def iniciar(numero):
    return ejecutar(numero,'iniciar')

@bp.post('/cocina/comandas/<int:numero>/lista')
@requiere_roles('Cocinero')
def lista(numero):
    return ejecutar(numero,'lista')

@bp.post('/salon/pedidos/<int:numero>/entregar')
@requiere_roles('Mesero')
def entregar(numero):
    return ejecutar(numero,'entregar')
