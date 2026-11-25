"""API del módulo de salón, protegida por RBAC."""
from flask import Blueprint, current_app, g, jsonify, request

from backend.db import get_connection
from backend.permisos import requiere_roles
from backend.catalogo import (SQL_MESAS, SQL_CATEGORIAS,
                              consulta_productos, preparar_productos)

from backend.pedidos import (ErrorPedido, validar_pedido, registrar_pedido,
                             SQL_PEDIDOS, serializar_pedido, consultar_detalle)

bp = Blueprint('salon', __name__, url_prefix='/api/salon')


def consultar(sql, parametros):
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(sql, parametros)
            return cursor.fetchall()
    finally:
        conexion.close()


def error_bd():
    current_app.logger.exception('Error al consultar datos de salon')
    return jsonify(error='Servicio de salon no disponible.'), 503


@bp.get('/mesas')
@requiere_roles('Mesero')
def mesas():
    try:
        filas = consultar(SQL_MESAS, (g.empleado['NIT_restaurante'],))
        datos = [dict(num_mesa=f['num_mesa'], activa=bool(f['activa']),
                      estado_mesa=f['estado_mesa']) for f in filas]
        resumen = {'libres': 0, 'ocupadas': 0, 'inactivas': 0}
        claves = {'Libre': 'libres', 'Ocupada': 'ocupadas', 'Inactiva': 'inactivas'}
        for dato in datos:
            resumen[claves[dato['estado_mesa']]] += 1
        return jsonify(total=len(datos), resumen=resumen, mesas=datos), 200
    except Exception:
        return error_bd()


@bp.get('/categorias')
@requiere_roles('Mesero')
def categorias():
    try:
        filas = consultar(SQL_CATEGORIAS, (g.empleado['NIT_restaurante'],))
        datos = [f['categoria_plato'] for f in filas]
        return jsonify(total=len(datos), categorias=datos), 200
    except Exception:
        return error_bd()


@bp.get('/productos')
@requiere_roles('Mesero')
def productos():
    categoria = request.args.get('categoria')
    if categoria is not None:
        categoria = categoria.strip()
        if not categoria or len(categoria) > 50:
            return jsonify(error='Categoria no valida.'), 400
    try:
        sql, params = consulta_productos(g.empleado['NIT_restaurante'], categoria)
        datos = preparar_productos(consultar(sql, params))
        return jsonify(total=len(datos), productos=datos), 200
    except Exception:
        return error_bd()


# Etapa 2.5: pedidos del mesero autenticado.
@bp.post('/pedidos')
@requiere_roles('Mesero')
def crear_pedido():
    conexion = None
    try:
        if not request.is_json:
            return jsonify(error='Se requiere Content-Type application/json.'), 415
        if request.content_length is not None and request.content_length > 262144:
            return jsonify(error='Solicitud demasiado grande.'), 413
        mesa, items = validar_pedido(request.get_json(silent=True))
        conexion = get_connection()
        pedido = registrar_pedido(conexion, g.empleado['NIT_restaurante'],
                                 g.empleado['id_empleado'], mesa, items)
        return jsonify(mensaje='Pedido registrado.', pedido=pedido), 201
    except ErrorPedido as e:
        return jsonify(error=str(e)), e.estado
    except Exception:
        current_app.logger.exception('Error al registrar pedido')
        return jsonify(error='No se pudo confirmar el registro. Consulta tus pedidos antes de reintentar.'), 503
    finally:
        if conexion is not None:
            conexion.close()


@bp.get('/pedidos')
@requiere_roles('Mesero')
def listar_pedidos():
    try:
        filas = consultar(SQL_PEDIDOS+' ORDER BY p.num_pedido DESC LIMIT 100',
                          (g.empleado['NIT_restaurante'],g.empleado['id_empleado']))
        datos = [serializar_pedido(f) for f in filas]
        return jsonify(total=len(datos), pedidos=datos), 200
    except Exception:
        return error_bd()


@bp.get('/pedidos/<int:numero>')
@requiere_roles('Mesero')
def detalle_pedido(numero):
    conexion = None
    try:
        conexion = get_connection()
        pedido = consultar_detalle(conexion, g.empleado['NIT_restaurante'],
                                  g.empleado['id_empleado'], numero)
        return jsonify(pedido=pedido), 200
    except ErrorPedido as e:
        return jsonify(error=str(e)), e.estado
    except Exception:
        return error_bd()
    finally:
        if conexion is not None:
            conexion.close()
