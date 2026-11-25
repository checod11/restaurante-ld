"""Pruebas de Flask con sesiones y consultas simuladas; sin modificar MariaDB."""
import os,unittest
from unittest.mock import patch
from backend.exportaciones import TIPOS
from backend.gestion import clave
from werkzeug.security import check_password_hash
from test_pedidos import NIT

class GestionUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('SECRET_KEY','clave-exclusiva-de-pruebas-automatizadas-123456')
        from app import app
        cls.app=app
    def setUp(self):
        self.client=self.app.test_client();self.empleado=dict(id_empleado=16,NIT_restaurante=NIT,nombre_empleado='Roberto',usuario_software='rjefe',activo=1,estado_suscripcion_software='Activo',es_mesero=0,es_cocinero=0,es_cajero=0,es_administrador=1)
        p=patch('backend.auth.buscar_empleado',return_value=self.empleado);p.start();self.addCleanup(p.stop)
    def sesion(self):
        with self.client.session_transaction() as s:s['id_empleado']=16;s['nit']=NIT
    def test_sin_sesion(self):
        self.assertEqual(self.client.get('/api/administracion/gestion').status_code,401)
        self.assertEqual(self.client.get('/api/administracion/reportes/ventas/exportar/pdf').status_code,401)
    def test_otro_rol(self):
        self.sesion();self.empleado.update(es_administrador=0,es_mesero=1)
        self.assertEqual(self.client.get('/api/administracion/gestion').status_code,403)
        self.assertEqual(self.client.post('/api/administracion/gestion/minimo',json={}).status_code,403)
        self.assertEqual(self.client.get('/api/administracion/reportes/ventas/exportar/xlsx').status_code,403)
    def test_plantilla(self):
        self.sesion();r=self.client.get('/panel/administracion');self.assertEqual(r.status_code,200)
        for i in ('ge-app','dg-pdf','dg-xlsx','inv-app','dg-reportes'):self.assertIn(f'id="{i}"'.encode(),r.data)
    def test_catalogo_y_guardar(self):
        self.sesion()
        with patch('backend.administracion.get_connection') as c,patch('backend.administracion.catalogos',return_value={'productos':[]}) as f:
            self.assertEqual(self.client.get('/api/administracion/gestion').status_code,200);f.assert_called_once_with(c.return_value,NIT)
        with patch('backend.administracion.get_connection') as c,patch('backend.administracion.guardar',return_value={'id':201}) as f:
            d={'id_insumo':201,'cantidad_minima':'5'};self.assertEqual(self.client.post('/api/administracion/gestion/minimo',json=d).status_code,200);f.assert_called_once_with(c.return_value,NIT,16,'minimo',d)
    def test_exportacion(self):
        self.sesion();j={'periodo':{'desde':'2026-11-25','hasta':'2026-11-25'},'resumen':{'ventas_totales':'0','facturas':0,'ticket_promedio':'0','subtotal':'0'},'serie_diaria':[]}
        from unittest.mock import Mock
        f=Mock(return_value=j)
        with patch('backend.administracion.get_connection') as c,patch.dict(TIPOS,{'ventas':('Ventas por período',f)}):
            for ext,magic in [('pdf',b'%PDF-'),('xlsx',b'PK')]:
                r=self.client.get('/api/administracion/reportes/ventas/exportar/'+ext+'?desde=2026-11-25&hasta=2026-11-25');self.assertEqual(r.status_code,200);self.assertTrue(r.data.startswith(magic));self.assertIn('attachment',r.headers['Content-Disposition']);r.close()
            self.assertEqual(self.client.get('/api/administracion/reportes/ventas/exportar/pdf?desde=2026-11-26&hasta=2026-11-25').status_code,400)
    def test_hash_real(self):
        p='Solo-prueba-segura-2026';h=clave({'contrasena':p});self.assertTrue(h.startswith('scrypt:'));self.assertTrue(check_password_hash(h,p));self.assertNotEqual(h,p)
if __name__=='__main__':unittest.main()
