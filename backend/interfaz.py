"""Vistas HTML; la autenticación y los permisos siguen en backend.auth."""
from flask import Blueprint, g, make_response, redirect, render_template, url_for
from backend.auth import cargar_empleado_actual

bp = Blueprint('interfaz', __name__)
MODULOS = {
    'salon': {'titulo': 'Panel de salón', 'rol': 'Mesero', 'icono': '01', 'descripcion': 'Mesas, menú digital y pedidos', 'funciones': ['Seleccionar mesa', 'Consultar menú', 'Registrar pedidos y notas'], 'etapa': '3.2'},
    'cocina': {'titulo': 'Gestor de cocina y bar', 'rol': 'Cocinero', 'icono': '02', 'descripcion': 'Comandas y tiempos de preparación', 'funciones': ['Nuevas comandas', 'En preparación', 'Listas para entregar'], 'etapa': '3.3'},
    'caja': {'titulo': 'Panel de caja', 'rol': 'Cajero', 'icono': '03', 'descripcion': 'Precuentas, pagos y comprobantes', 'funciones': ['Consultar precuentas', 'Registrar pagos', 'Consultar comprobantes'], 'etapa': '3.4'},
    'administracion': {'titulo': 'Dashboard gerencial', 'rol': 'Administrador', 'icono': '04', 'descripcion': 'Inventario, alertas e indicadores', 'funciones': ['Inventario y movimientos', 'Alertas de stock', 'Reportes administrativos'], 'etapa': '3.5–3.7'},
}

@bp.after_request
def no_cache(response):
    response.headers['Cache-Control'] = 'no-store'
    return response


def autorizacion():
    error = cargar_empleado_actual()
    if error is None:
        return None
    status = make_response(error).status_code
    if status == 401:
        return redirect(url_for('interfaz.login'))
    return render_template('error_ui.html', estado=status), status


@bp.get('/login')
def login():
    return render_template('login.html')


@bp.get('/panel')
def panel():
    error = autorizacion()
    if error is not None:
        return error
    permitidos = [m for m in MODULOS if m in g.empleado['modulos']]
    if len(permitidos) == 1:
        return redirect(url_for('interfaz.modulo', nombre=permitidos[0]))
    if not permitidos:
        return render_template('error_ui.html', estado=403), 403
    return render_template('panel.html', empleado=g.empleado, modulos=MODULOS, actual=None)


@bp.get('/panel/<nombre>')
def modulo(nombre):
    error = autorizacion()
    if error is not None:
        return error
    if nombre not in MODULOS:
        return render_template('error_ui.html', estado=404), 404
    if nombre not in g.empleado['modulos']:
        return render_template('error_ui.html', estado=403), 403
    return render_template('panel.html', empleado=g.empleado, modulos=MODULOS, actual=nombre)
