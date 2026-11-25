"""Autenticación local del MVP. Identificación de roles por subtipos y sesión local."""
from flask import Blueprint, current_app, g, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from backend.db import get_connection

bp = Blueprint("auth", __name__, url_prefix="/api/auth")
# El valor ficticio evita omitir el cálculo del hash para usuarios inexistentes.
DUMMY_HASH = generate_password_hash("valor-interno-no-utilizable", method="scrypt")


def buscar_empleado(usuario=None, id_empleado=None, nit=None):
    sql = """
        SELECT e.id_empleado, e.NIT_restaurante, e.nombre_empleado,
               e.usuario_software, e.`contraseña_software` AS clave_hash,
               e.activo, r.estado_suscripcion_software,
               EXISTS (SELECT 1 FROM Mesero m
                       WHERE m.id_empleado = e.id_empleado
                         AND m.NIT_restaurante = e.NIT_restaurante) AS es_mesero,
               EXISTS (SELECT 1 FROM Cocinero c
                       WHERE c.id_empleado = e.id_empleado
                         AND c.NIT_restaurante = e.NIT_restaurante) AS es_cocinero,
               EXISTS (SELECT 1 FROM Cajero ca
                       WHERE ca.id_empleado = e.id_empleado
                         AND ca.NIT_restaurante = e.NIT_restaurante) AS es_cajero,
               EXISTS (SELECT 1 FROM Administrador a
                       WHERE a.id_empleado = e.id_empleado
                         AND a.NIT_restaurante = e.NIT_restaurante) AS es_administrador
        FROM Empleado e
        JOIN Restaurante r ON r.NIT = e.NIT_restaurante
        WHERE e.NIT_restaurante = %s
    """
    if usuario is not None:
        sql += " AND e.usuario_software = %s LIMIT 2"
        params = (nit, usuario)
    else:
        sql += " AND e.id_empleado = %s LIMIT 2"
        params = (nit, id_empleado)
    conexion = get_connection()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(sql, params)
            filas = cursor.fetchall()
        # No autenticar un usuario ambiguo si existen duplicados.
        return filas[0] if len(filas) == 1 else None
    finally:
        conexion.close()


def habilitado(empleado):
    return bool(empleado and empleado["activo"] == 1 and
                empleado["estado_suscripcion_software"] == "Activo")


# La herencia es parcial y superpuesta: cero, uno o varios roles.
ROLES_MODULOS = (
    ("es_mesero", "Mesero", "salon"),
    ("es_cocinero", "Cocinero", "cocina"),
    ("es_cajero", "Cajero", "caja"),
    ("es_administrador", "Administrador", "administracion"),
)


def roles_de(empleado):
    return [rol for campo, rol, _ in ROLES_MODULOS if empleado.get(campo) == 1]


def datos_publicos(empleado):
    datos = {k: empleado[k] for k in (
        "id_empleado", "NIT_restaurante", "nombre_empleado", "usuario_software"
    )}
    roles = roles_de(empleado)
    datos["roles"] = roles
    datos["modulos"] = [modulo for _, rol, modulo in ROLES_MODULOS if rol in roles]
    return datos


def cargar_empleado_actual():
    """Revalida la sesión en la BD en cada petición protegida.

    Devuelve None si está autorizada la sesión, o una respuesta HTTP de error.
    La identidad pública queda en g.empleado, limitada a esta petición.
    """
    if "id_empleado" not in session or session.get("nit") != current_app.config["DEMO_NIT"]:
        session.clear()
        return jsonify(error="No has iniciado sesion."), 401
    try:
        empleado = buscar_empleado(id_empleado=session["id_empleado"], nit=session["nit"])
    except Exception:
        current_app.logger.exception("Error al consultar sesion")
        return jsonify(error="Servicio de autenticacion no disponible."), 503
    if not habilitado(empleado):
        session.clear()
        return jsonify(error="Sesion no habilitada."), 401
    if not roles_de(empleado):
        session.clear()
        return jsonify(error="Empleado sin roles asignados."), 403
    g.empleado = datos_publicos(empleado)
    return None


@bp.post("/login")
def login():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return jsonify(error="Envia un objeto JSON."), 400
    usuario = datos.get("usuario")
    clave = datos.get("contrasena")
    if (not isinstance(usuario, str) or not isinstance(clave, str)
            or not usuario.strip() or len(usuario) > 50
            or not clave or len(clave) > 256):
        return jsonify(error="Usuario o contrasena no validos."), 400
    nit = current_app.config["DEMO_NIT"]
    try:
        empleado = buscar_empleado(usuario=usuario.strip(), nit=nit)
        almacenada = empleado.get("clave_hash") if empleado else None
        es_hash = isinstance(almacenada, str) and almacenada.startswith("scrypt:")
        try:
            coincide = check_password_hash(almacenada if es_hash else DUMMY_HASH, clave)
        except (ValueError, TypeError):
            coincide = False
        if not (es_hash and coincide and habilitado(empleado)):
            return jsonify(error="Credenciales invalidas o acceso no habilitado."), 401
    except Exception:
        current_app.logger.exception("Error al consultar autenticacion")
        return jsonify(error="Servicio de autenticacion no disponible."), 503
    if not roles_de(empleado):
        session.clear()
        return jsonify(error="Empleado sin roles asignados."), 403
    session.clear()
    session.permanent = True
    session["id_empleado"] = empleado["id_empleado"]
    session["nit"] = empleado["NIT_restaurante"]
    return jsonify(mensaje="Inicio de sesion exitoso", empleado=datos_publicos(empleado)), 200


@bp.get("/me")
def me():
    error = cargar_empleado_actual()
    if error is not None:
        return error
    return jsonify(empleado=g.empleado), 200


@bp.post("/logout")
def logout():
    if not isinstance(request.get_json(silent=True), dict):
        return jsonify(error="Envia un objeto JSON."), 400
    session.clear()
    return jsonify(mensaje="Sesion cerrada"), 200
