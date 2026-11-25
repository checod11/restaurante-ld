"""Sustituye solo las credenciales de ejemplo de cuatro empleados del DML."""
from getpass import getpass

from werkzeug.security import generate_password_hash
from backend.db import get_connection

NIT = "900123456-1"
CUENTAS = [(1, "cperez"), (6, "pchef"), (11, "ccaja"), (16, "rjefe")]


def main():
    conexion = get_connection()
    try:
        pendientes = []
        with conexion.cursor() as cursor:
            for id_empleado, usuario in CUENTAS:
                cursor.execute("""
                    SELECT usuario_software, `contraseña_software` AS clave_hash
                    FROM Empleado WHERE id_empleado=%s AND NIT_restaurante=%s
                """, (id_empleado, NIT))
                fila = cursor.fetchone()
                if not fila or fila["usuario_software"] != usuario:
                    raise RuntimeError(f"No coincide el registro esperado: {usuario}.")
                if fila["clave_hash"] == "hash123":
                    pendientes.append((id_empleado, usuario))
                else:
                    print(f"[OMITIDO] {usuario}: credencial distinta del valor inicial.")
        conexion.rollback()  # Cerrar la lectura antes de pedir datos por teclado.
        cambios = []
        for id_empleado, usuario in pendientes:
            while True:
                clave = getpass(f"Nueva clave para {usuario} (12 a 256 caracteres): ")
                confirmacion = getpass("Confirmar clave: ")
                if 12 <= len(clave) <= 256 and clave == confirmacion:
                    break
                print("Las claves no coinciden o no cumplen la longitud.")
            cambios.append((generate_password_hash(clave, method="scrypt"), id_empleado, NIT, usuario, "hash123"))
            del clave, confirmacion
        with conexion.cursor() as cursor:
            for cambio in cambios:
                cursor.execute("""
                    UPDATE Empleado SET `contraseña_software`=%s
                    WHERE id_empleado=%s AND NIT_restaurante=%s
                      AND usuario_software=%s AND BINARY `contraseña_software`=%s
                """, cambio)
                if cursor.rowcount != 1:
                    raise RuntimeError("La credencial cambio durante la configuracion; no se guardaran cambios.")
        conexion.commit()
        print(f"[OK] {len(cambios)} credenciales actualizadas.")
    except BaseException:
        conexion.rollback()
        raise
    finally:
        conexion.close()


if __name__ == "__main__":
    main()
