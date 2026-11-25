"""Prueba local de solo lectura; ejecutar desde la raíz del proyecto."""
import sys
from contextlib import closing

import pymysql
from backend.db import get_connection

NIT = "900123456-1"
TABLAS = {
    "Restaurante", "Proveedor", "Empleado", "Producto", "Insumo", "Mesero",
    "Cocinero", "Cajero", "Administrador", "Pedido", "Factura", "Orden_Compra",
    "Receta", "Detalle_Pedido", "Detalle_Orden_Compra", "Mesa", "Movimiento_Inventario",
}
VISTAS = ("v_resumen_facturacion_pedidos", "v_ficha_recetas_insumos", "v_estado_mesas")


def main():
    try:
        with closing(get_connection()) as conn, conn.cursor() as cur:
            cur.execute("SELECT VERSION() AS version, DATABASE() AS bd, CURRENT_USER() AS cuenta")
            info = cur.fetchone()
            print(f"[OK] Conexión: {info['bd']} | Cuenta: {info['cuenta']}")
            print(f"Servidor: {info['version']}")
            cur.execute("""SELECT TABLE_NAME AS nombre FROM information_schema.TABLES
                           WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE'""")
            presentes = {r["nombre"].lower() for r in cur.fetchall()}
            faltantes = sorted(t for t in TABLAS if t.lower() not in presentes)
            if faltantes:
                raise ValueError("Tablas faltantes: " + ", ".join(faltantes))
            print("[OK] Las 17 tablas de la versión ampliada están presentes.")
            cur.execute("SELECT nombre_restaurante FROM Restaurante WHERE NIT = %s", (NIT,))
            restaurante = cur.fetchone()
            if not restaurante:
                raise ValueError("No existe el restaurante de prueba; revisa el DML.")
            print("[OK] " + restaurante["nombre_restaurante"])
            # Identificadores fijos definidos en el código; valores externos parametrizados.
            for tabla in ("Empleado", "Mesero", "Cocinero", "Cajero", "Administrador", "Producto", "Insumo", "Pedido", "Factura"):
                cur.execute(f"SELECT COUNT(*) AS total FROM `{tabla}` WHERE NIT_restaurante = %s", (NIT,))
                total = cur.fetchone()["total"]
                if total == 0:
                    raise ValueError(f"{tabla} no tiene datos para el restaurante de prueba.")
                print(f"  {tabla}: {total}")
            for vista in VISTAS:
                cur.execute(f"SELECT COUNT(*) AS total FROM `{vista}` WHERE NIT_restaurante = %s", (NIT,))
                print(f"[OK] Vista {vista}: {cur.fetchone()['total']} filas")
            for tabla, columnas in {
                "Empleado": "activo",
                "Pedido": "id_cocinero, fecha_inicio_preparacion, fecha_lista, fecha_entrega",
                "Detalle_Pedido": "nota_especial, precio_unitario",
                "Factura": "documento_cliente, correo_cliente, cufe, estado_validacion, referencia_proveedor, monto_recibido",
                "Mesa": "activa",
                "Movimiento_Inventario": "id_movimiento, tipo, cantidad, id_factura",
            }.items():
                cur.execute(f"SELECT {columnas} FROM `{tabla}` LIMIT 0")
            print("[OK] Columnas nuevas disponibles.")
            cur.execute("SELECT estado_mesa, COUNT(*) AS total FROM v_estado_mesas WHERE NIT_restaurante=%s GROUP BY estado_mesa", (NIT,))
            for fila in cur.fetchall():
                print(f"  Mesas {fila['estado_mesa']}: {fila['total']}")
            conn.rollback()
        print("[OK] Prueba de conexión y lectura finalizada. No se modificaron datos.")
        return 0
    except (pymysql.MySQLError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
