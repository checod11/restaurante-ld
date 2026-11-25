import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify

from backend.auth import bp as auth_bp
from backend.permisos import bp as permisos_bp
from backend.salon import bp as salon_bp
from backend.cocina import bp as cocina_bp
from backend.caja import bp as caja_bp
from backend.administracion import bp as administracion_bp
from backend.db import get_connection
from backend.interfaz import bp as interfaz_bp

load_dotenv(Path(__file__).resolve().parent / ".env")
clave_secreta = os.getenv("SECRET_KEY", "")
if len(clave_secreta) < 32:
    raise RuntimeError("Configura SECRET_KEY en .env con una clave aleatoria de al menos 32 caracteres.")

app = Flask(__name__)
app.config.update(
    SECRET_KEY=clave_secreta,
    DEMO_NIT="900123456-1",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Strict",
    SESSION_COOKIE_SECURE=False,  # Solo para HTTP local; usar True con HTTPS.
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    SESSION_REFRESH_EACH_REQUEST=False,
)
app.register_blueprint(auth_bp)
app.register_blueprint(permisos_bp)
app.register_blueprint(salon_bp)
app.register_blueprint(cocina_bp)
app.register_blueprint(caja_bp)
app.register_blueprint(administracion_bp)
app.register_blueprint(interfaz_bp)


@app.route("/")
def inicio():
    return jsonify({
        "proyecto": "Software Administrador de Restaurantes L&D",
        "restaurante": "Mirador Bumangués",
        "version": "1.0.0",
        "estado": "Servidor activo",
        "mensaje": "Bienvenido al sistema"
    })


@app.route("/api/estado")
def estado():
    conexion = None
    try:
        conexion = get_connection()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT DATABASE() AS base_datos")
            resultado = cursor.fetchone()
        return jsonify(servidor="Activo", conexion="Exitosa",
                       base_datos=resultado["base_datos"]), 200
    except Exception:
        app.logger.exception("Error de conexion con MariaDB")
        return jsonify(servidor="Activo", conexion="Fallida",
                       mensaje="Error de conexion con la base de datos"), 503
    finally:
        if conexion is not None:
            conexion.close()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
