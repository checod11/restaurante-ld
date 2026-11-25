"""Pruebas automatizadas sin BD real. Ejecutar: python -m unittest -v test_permisos"""
import os
import unittest
from unittest.mock import patch

# Solo para el proceso de pruebas, no modifica el archivo .env.
os.environ['SECRET_KEY'] = 'clave-ficticia-exclusiva-de-pruebas-' * 2
from app import app
from werkzeug.security import generate_password_hash

NIT = '900123456-1'
CLAVE = 'clave-ficticia-test-123'
HASH = generate_password_hash(CLAVE, method='scrypt')
ROLES = ('Mesero', 'Cocinero', 'Cajero', 'Administrador')
RUTAS = ('salon', 'cocina', 'caja', 'administracion')


class PermisosTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.empleado = {
            'id_empleado': 1, 'NIT_restaurante': NIT,
            'nombre_empleado': 'Empleado de prueba', 'usuario_software': 'prueba',
            'clave_hash': HASH, 'activo': 1, 'estado_suscripcion_software': 'Activo',
            **{f'es_{rol.lower()}': 0 for rol in ROLES},
        }
        parche = patch('backend.auth.buscar_empleado', side_effect=self.buscar)
        parche.start()
        self.addCleanup(parche.stop)

    def buscar(self, usuario=None, id_empleado=None, nit=None):
        if nit != NIT or (usuario is not None and usuario != 'prueba') or (id_empleado is not None and id_empleado != 1):
            return None
        return self.empleado.copy()

    def login(self, clave=CLAVE):
        return self.client.post('/api/auth/login', json={'usuario': 'prueba', 'contrasena': clave})

    def acceso(self, modulo):
        return self.client.get(f'/api/{modulo}/acceso')

    def test_matriz_cuatro_roles(self):
        for rol in ROLES:
            with self.subTest(rol=rol):
                self.client = app.test_client()
                for otro in ROLES:
                    self.empleado[f'es_{otro.lower()}'] = int(otro == rol)
                respuesta = self.login()
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(respuesta.json['empleado']['roles'], [rol])
                self.assertNotIn('clave_hash', respuesta.json['empleado'])
                for otro, modulo in zip(ROLES, RUTAS):
                    self.assertEqual(self.acceso(modulo).status_code, 200 if otro == rol else 403)

    def test_sin_sesion(self):
        for modulo in RUTAS:
            self.assertEqual(self.acceso(modulo).status_code, 401)

    def test_roles_multiples(self):
        self.empleado.update(es_mesero=1, es_cajero=1)
        self.assertEqual(self.login().json['empleado']['roles'], ['Mesero', 'Cajero'])
        self.assertEqual(self.acceso('salon').status_code, 200)
        self.assertEqual(self.acceso('caja').status_code, 200)
        self.assertEqual(self.acceso('cocina').status_code, 403)

    def test_sin_roles(self):
        self.assertEqual(self.login().status_code, 403)
        self.assertEqual(self.acceso('salon').status_code, 401)

    def test_revocacion_rol(self):
        self.empleado.update(es_mesero=1, es_cajero=1)
        self.assertEqual(self.login().status_code, 200)
        self.empleado['es_mesero'] = 0
        self.assertEqual(self.acceso('salon').status_code, 403)
        self.assertEqual(self.acceso('caja').status_code, 200)
        self.empleado['es_cajero'] = 0
        self.assertEqual(self.acceso('caja').status_code, 403)
        self.assertEqual(self.client.get('/api/auth/me').status_code, 401)

    def test_empleado_desactivado(self):
        self.empleado['es_mesero'] = 1
        self.assertEqual(self.login().status_code, 200)
        self.empleado['activo'] = 0
        self.assertEqual(self.acceso('salon').status_code, 401)

    def test_suscripcion_suspendida(self):
        self.empleado['es_mesero'] = 1
        self.assertEqual(self.login().status_code, 200)
        self.empleado['estado_suscripcion_software'] = 'Suspendido'
        self.assertEqual(self.acceso('salon').status_code, 401)

    def test_clave_incorrecta(self):
        self.empleado['es_mesero'] = 1
        self.assertEqual(self.login('incorrecta').status_code, 401)

    def test_logout(self):
        self.empleado['es_mesero'] = 1
        self.assertEqual(self.login().status_code, 200)
        self.assertEqual(self.client.post('/api/auth/logout', json={}).status_code, 200)
        self.assertEqual(self.acceso('salon').status_code, 401)

    def test_falla_bd(self):
        self.empleado['es_mesero'] = 1
        self.assertEqual(self.login().status_code, 200)
        with patch('backend.auth.buscar_empleado', side_effect=RuntimeError('Fallo simulado')):
            self.assertEqual(self.acceso('salon').status_code, 503)


if __name__ == '__main__':
    unittest.main()
