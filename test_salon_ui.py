"""Pruebas de integración de plantillas; no conectan a MariaDB."""
import unittest
from pathlib import Path
from unittest.mock import patch
from flask import Flask, g, jsonify
from backend.interfaz import bp

ROOT = Path(__file__).resolve().parent

class TestSalonUI(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__, template_folder=str(ROOT/'templates'), static_folder=str(ROOT/'static'))
        app.register_blueprint(bp)
        self.client = app.test_client()

    def identidad(self, modulo, rol):
        def cargar():
            g.empleado = {'nombre_empleado':'Mesero de prueba','roles':[rol],'modulos':[modulo]}
        return patch('backend.interfaz.cargar_empleado_actual', side_effect=cargar)

    def test_estructura_salon(self):
        with self.identidad('salon','Mesero'):
            r = self.client.get('/panel/salon')
            self.assertEqual(r.status_code,200)
            for id_ in ('salon-mesas','salon-categorias','salon-productos','salon-items','salon-enviar','salon-pedidos','salon-incertidumbre'):
                self.assertIn(('id="'+id_+'"').encode(),r.data)
            self.assertIn(b'/static/js/salon.js',r.data)
            self.assertIn(b'/static/css/salon.css',r.data)
            self.assertIn(b'cerrar-sesion',r.data)
            self.assertEqual(r.headers['Cache-Control'],'no-store')

    def test_sin_sesion(self):
        with patch('backend.interfaz.cargar_empleado_actual',side_effect=lambda:(jsonify(error='sin sesion'),401)):
            r=self.client.get('/panel/salon')
            self.assertEqual(r.status_code,302)
            self.assertTrue(r.location.endswith('/login'))

    def test_cocinero_no_autorizado(self):
        with self.identidad('cocina','Cocinero'):
            self.assertEqual(self.client.get('/panel/salon').status_code,403)

    def test_otros_paneles_conservados(self):
        for modulo,rol in [('cocina','Cocinero'),('caja','Cajero'),('administracion','Administrador')]:
            with self.subTest(modulo=modulo), self.identidad(modulo,rol):
                r=self.client.get('/panel/'+modulo)
                self.assertEqual(r.status_code,200)
                self.assertNotIn(b'id="salon-app"',r.data)
                self.assertIn(b'cerrar-sesion',r.data)

    def test_estaticos(self):
        for ruta in ('/static/css/salon.css','/static/js/salon.js'):
            with self.subTest(ruta=ruta):
                r=self.client.get(ruta)
                try:self.assertEqual(r.status_code,200)
                finally:r.close()

if __name__=='__main__': unittest.main()
