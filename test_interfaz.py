"""Pruebas de navegación HTML sin escrituras en MariaDB."""
import unittest
from pathlib import Path
from unittest.mock import patch
from flask import Flask, g, jsonify
from backend.interfaz import bp

ROOT = Path(__file__).resolve().parent

class TestInterfaz(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__, template_folder=str(ROOT/'templates'), static_folder=str(ROOT/'static'))
        self.app.register_blueprint(bp)
        self.client = self.app.test_client()

    def identidad(self, modulos, roles):
        def cargar():
            g.empleado = {'nombre_empleado':'Empleado de prueba','roles':roles,'modulos':modulos}
        return patch('backend.interfaz.cargar_empleado_actual', side_effect=cargar)

    def test_login_publico(self):
        r = self.client.get('/login')
        self.assertEqual(r.status_code,200)
        self.assertIn(b'login-form',r.data)
        self.assertEqual(r.headers['Cache-Control'],'no-store')

    def test_sin_sesion(self):
        with patch('backend.interfaz.cargar_empleado_actual',side_effect=lambda:(jsonify(error='sin sesion'),401)):
            r = self.client.get('/panel/salon')
            self.assertEqual(r.status_code,302)
            self.assertTrue(r.location.endswith('/login'))

    def test_roles(self):
        for modulo, rol in [('salon','Mesero'),('cocina','Cocinero'),('caja','Cajero'),('administracion','Administrador')]:
            with self.subTest(modulo=modulo), self.identidad([modulo],[rol]):
                self.assertTrue(self.client.get('/panel').location.endswith('/panel/'+modulo))
                self.assertEqual(self.client.get('/panel/'+modulo).status_code,200)
                for otro in {'salon','cocina','caja','administracion'}-{modulo}:
                    self.assertEqual(self.client.get('/panel/'+otro).status_code,403)

    def test_varios_roles(self):
        with self.identidad(['salon','caja'],['Mesero','Cajero']):
            r=self.client.get('/panel')
            self.assertEqual(r.status_code,200)
            self.assertIn(b'/panel/salon',r.data)
            self.assertIn(b'/panel/caja',r.data)
            self.assertNotIn(b'/panel/cocina',r.data)

    def test_servicio_no_disponible(self):
        with patch('backend.interfaz.cargar_empleado_actual',side_effect=lambda:(jsonify(error='bd'),503)):
            self.assertEqual(self.client.get('/panel').status_code,503)

    def test_modulo_desconocido(self):
        with self.identidad(['salon'],['Mesero']):
            self.assertEqual(self.client.get('/panel/otro').status_code,404)

if __name__=='__main__': unittest.main()
