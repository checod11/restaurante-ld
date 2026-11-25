"""Pruebas de rutas y plantillas: no modifican MariaDB."""
import unittest
from pathlib import Path
from unittest.mock import patch
from flask import Flask, g, jsonify
from backend.interfaz import bp

ROOT = Path(__file__).resolve().parent

class TestCocinaUI(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__, template_folder=str(ROOT/'templates'), static_folder=str(ROOT/'static'))
        app.register_blueprint(bp)
        self.client = app.test_client()

    def identidad(self, modulo, rol):
        def cargar():
            g.empleado = {'id_empleado':6,'nombre_empleado':'Cocinero de prueba','roles':[rol],'modulos':[modulo]}
        return patch('backend.interfaz.cargar_empleado_actual', side_effect=cargar)

    def test_estructura_cocina(self):
        with self.identidad('cocina','Cocinero'):
            r=self.client.get('/panel/cocina')
            self.assertEqual(r.status_code,200)
            for id_ in ('cocina-app','cocina-Tomado','cocina-Preparacion','cocina-Lista','cocina-actualizar','cocina-error'):
                self.assertIn(('id="'+id_+'"').encode(),r.data)
            self.assertIn(b'data-empleado="6"',r.data)
            self.assertIn(b'cerrar-sesion',r.data)
            self.assertEqual(r.headers['Cache-Control'],'no-store')

    def test_sin_sesion(self):
        with patch('backend.interfaz.cargar_empleado_actual',side_effect=lambda:(jsonify(error='sin sesion'),401)):
            r=self.client.get('/panel/cocina')
            self.assertEqual(r.status_code,302)
            self.assertTrue(r.location.endswith('/login'))

    def test_roles_no_autorizados(self):
        for modulo,rol in [('salon','Mesero'),('caja','Cajero'),('administracion','Administrador')]:
            with self.subTest(rol=rol), self.identidad(modulo,rol):
                self.assertEqual(self.client.get('/panel/cocina').status_code,403)

    def test_paneles_conservados(self):
        for modulo,rol in [('salon','Mesero'),('caja','Cajero'),('administracion','Administrador')]:
            with self.subTest(rol=rol), self.identidad(modulo,rol):
                r=self.client.get('/panel/'+modulo)
                self.assertEqual(r.status_code,200)
                self.assertNotIn(b'id="cocina-app"',r.data)
                if modulo=='salon': self.assertIn(b'id="salon-app"',r.data)

    def test_estaticos(self):
        for ruta in ('/static/css/cocina.css','/static/js/cocina.js'):
            with self.subTest(ruta=ruta):
                r=self.client.get(ruta)
                try: self.assertEqual(r.status_code,200)
                finally: r.close()

if __name__=='__main__': unittest.main()
