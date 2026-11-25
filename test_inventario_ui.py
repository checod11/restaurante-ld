"""Pruebas de plantillas y acceso, sin escrituras en MariaDB."""
import unittest
from pathlib import Path
from unittest.mock import patch
from flask import Flask, g, jsonify
from backend.interfaz import bp
ROOT=Path(__file__).resolve().parent
class TestInventarioUI(unittest.TestCase):
    def setUp(self):
        app=Flask(__name__,template_folder=str(ROOT/'templates'),static_folder=str(ROOT/'static'))
        app.register_blueprint(bp)
        self.client=app.test_client()
    def identidad(self, modulo, rol):
        def cargar():
            g.empleado={'id_empleado':16,'nombre_empleado':'Empleado de prueba','roles':[rol],'modulos':[modulo]}
        return patch('backend.interfaz.cargar_empleado_actual',side_effect=cargar)
    def test_estructura_inventario(self):
        with self.identidad('administracion','Administrador'):
            r=self.client.get('/panel/administracion')
            self.assertEqual(r.status_code,200)
            for id_ in ('inv-app','inv-alertas','inv-insumos','inv-form','inv-registrar','inv-movimientos','inv-incertidumbre'):
                self.assertIn(('id="'+id_+'"').encode(),r.data)
            self.assertEqual(r.headers['Cache-Control'],'no-store')
    def test_sin_sesion(self):
        with patch('backend.interfaz.cargar_empleado_actual',side_effect=lambda:(jsonify(error='sin sesion'),401)):
            r=self.client.get('/panel/administracion')
            self.assertEqual(r.status_code,302)
            self.assertTrue(r.location.endswith('/login'))
    def test_roles_no_autorizados(self):
        for modulo,rol in [('salon','Mesero'),('cocina','Cocinero'),('caja','Cajero')]:
            with self.subTest(rol=rol),self.identidad(modulo,rol):
                self.assertEqual(self.client.get('/panel/administracion').status_code,403)
    def test_paneles_conservados(self):
        for modulo,rol in [('salon','Mesero'),('cocina','Cocinero'),('caja','Cajero')]:
            with self.subTest(rol=rol),self.identidad(modulo,rol):
                r=self.client.get('/panel/'+modulo)
                self.assertEqual(r.status_code,200)
                self.assertIn(('id="'+modulo+'-app"').encode(),r.data)
                self.assertNotIn(b'id="inv-app"',r.data)
    def test_estaticos(self):
        for path in ('/static/css/inventario.css','/static/js/inventario.js'):
            r=self.client.get(path)
            try:self.assertEqual(r.status_code,200)
            finally:r.close()
if __name__=='__main__':unittest.main()
