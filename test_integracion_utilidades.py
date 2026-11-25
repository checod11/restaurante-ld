"""Pruebas del verificador, sin MariaDB y sin utilizar el servidor real."""
import json
import threading
import unittest
from decimal import Decimal as D
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch
import prueba_integracion as p


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.responder(200 if self.headers.get('Cookie')=='demo=1' else 401, {'ok':True})
    def do_POST(self):
        datos=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        self.responder(201, datos, cookie=True)
    def responder(self,codigo,datos,cookie=False):
        self.send_response(codigo)
        self.send_header('Content-Type','application/json')
        if cookie:self.send_header('Set-Cookie','demo=1; Path=/; HttpOnly')
        self.end_headers()
        self.wfile.write(json.dumps(datos).encode())
    def log_message(self,*args):pass


class UtilidadesTest(unittest.TestCase):
    def test_cookies_aisladas_y_codigos(self):
        server=HTTPServer(('127.0.0.1',0),Handler)
        hilo=threading.Thread(target=server.serve_forever,daemon=True);hilo.start()
        try:
            with patch.object(p,'BASE',f'http://127.0.0.1:{server.server_port}'):
                a,b=p.Cliente(),p.Cliente()
                a.pedir('/api/me',esperado=401)
                self.assertEqual(a.pedir('/api/login',{'x':'prueba'},esperado=201),{'x':'prueba'})
                a.pedir('/api/me');b.pedir('/api/me',esperado=401)
                with self.assertRaises(p.Fallo):b.pedir('/api/me')
        finally:
            server.shutdown();server.server_close();hilo.join()
    def test_reserva_y_factura(self):
        antes={1:(D('10'),D('2'),D('8')),2:(D('5'),D('0'),D('5'))}
        receta={1:D('0.5')}
        p.comprobar_stock(antes,{1:(D('10'),D('2.5'),D('7.5')),2:antes[2]},receta,'reserva')
        p.comprobar_stock(antes,{1:(D('9.5'),D('2'),D('7.5')),2:antes[2]},receta,'factura')
        with self.assertRaises(p.Fallo):p.comprobar_stock(antes,antes,receta,'factura')
    def test_mapa_decimal(self):
        self.assertEqual(p.mapa_stock({'insumos':[{'id_insumo':1,'cantidad_disponible':'0.30','comprometido':'0.10','utilizable':'0.20'}]}),{1:(D('0.30'),D('0.10'),D('0.20'))})
    def test_reportes_sin_registros(self):
        self.assertEqual(p.monto_producto({'productos':[]},105),0)
        self.assertEqual(p.consumo_insumo({'insumos':[]},201),D(0))
    def test_reportes_con_registros(self):
        self.assertEqual(p.monto_producto({'productos':[{'num_serial':105,'unidades':2}]},105),2)
        self.assertEqual(p.consumo_insumo({'insumos':[{'id_insumo':201,'cantidad_consumida':'0.50'}]},201),D('0.50'))


if __name__=='__main__':unittest.main()
