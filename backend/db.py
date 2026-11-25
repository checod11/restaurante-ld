"""Conexión reutilizable; todavía no contiene rutas HTTP."""
import os
from pathlib import Path

import pymysql
from dotenv import load_dotenv
from pymysql.cursors import DictCursor

ROOT = Path(__file__).resolve().parents[1]


def get_connection():
    """Abre una conexión nueva. Quien la usa debe cerrarla."""
    load_dotenv(ROOT / ".env")
    password = os.getenv("DB_PASSWORD", "")
    if not password or password == "CAMBIAR_CLAVE_APP":
        raise ValueError("Configura DB_PASSWORD en el archivo .env.")
    try:
        port = int(os.getenv("DB_PORT", "3306"))
        if not 1 <= port <= 65535:
            raise ValueError
    except ValueError:
        raise ValueError("DB_PORT debe ser un puerto entre 1 y 65535.") from None
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=port,
        user=os.getenv("DB_USER", "app_mirador"),
        password=password,
        database=os.getenv("DB_NAME", "restaurante_pro_max"),
        charset="utf8mb4",
        cursorclass=DictCursor,
        connect_timeout=5,
        read_timeout=10,
        write_timeout=10,
        autocommit=False,
    )
