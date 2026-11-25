"""Reglas reutilizables de autorización y rutas de prueba del MVP."""
from functools import wraps

from flask import Blueprint, g, jsonify

from backend.auth import cargar_empleado_actual, ROLES_MODULOS

bp = Blueprint("permisos", __name__, url_prefix="/api")
ROLES_VALIDOS = frozenset(rol for _, rol, _ in ROLES_MODULOS)


def requiere_roles(*roles_permitidos):
    """Permite acceder si el empleado tiene al menos uno de los roles indicados."""
    if not roles_permitidos or not set(roles_permitidos) <= ROLES_VALIDOS:
        raise ValueError("Configura uno o varios roles validos.")
    permitidos = frozenset(roles_permitidos)

    def decorar(funcion):
        @wraps(funcion)
        def verificar(*args, **kwargs):
            error = cargar_empleado_actual()
            if error is not None:
                return error
            if not permitidos.intersection(g.empleado["roles"]):
                return jsonify(error="No tienes permisos para este modulo."), 403
            return funcion(*args, **kwargs)
        return verificar
    return decorar


def respuesta_modulo(modulo):
    return jsonify(mensaje="Acceso autorizado", modulo=modulo,
                   empleado=g.empleado, tipo="prueba_de_permisos"), 200


@bp.get("/salon/acceso")
@requiere_roles("Mesero")
def salon():
    return respuesta_modulo("salon")


@bp.get("/cocina/acceso")
@requiere_roles("Cocinero")
def cocina():
    return respuesta_modulo("cocina")


@bp.get("/caja/acceso")
@requiere_roles("Cajero")
def caja():
    return respuesta_modulo("caja")


@bp.get("/administracion/acceso")
@requiere_roles("Administrador")
def administracion():
    return respuesta_modulo("administracion")
