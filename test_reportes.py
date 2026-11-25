"""Pruebas aisladas; SQLite simula consultas, Flask comprueba permisos."""
import os
import sqlite3
import unittest
from unittest.mock import patch
from test_pedidos import Conexion,NIT
from backend.reportes import periodo,ventas,productos,consumo,cierre_caja,dashboard
from backend.pedidos import ErrorPedido

class ReportesTest(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:'); self.db.row_factory=sqlite3.Row
        self.addCleanup(self.db.close); self.c=Conexion(self.db)
        self.p=periodo('2026-11-24','2026-11-25')
        self.db.executescript('''
        CREATE TABLE Factura(id_factura INT,NIT_restaurante TEXT,num_pedido INT,id_cajero INT,valor_total NUMERIC,subvalor_total NUMERIC,fecha_emision TEXT,metodo_pago TEXT,monto_recibido NUMERIC);
        CREATE VIEW v_resumen_facturacion_pedidos AS SELECT * FROM Factura;
        CREATE TABLE Producto(num_serial INT,NIT_restaurante TEXT,nombre TEXT,categoria_plato TEXT);
        CREATE TABLE Detalle_Pedido(num_pedido INT,num_serial_producto INT,NIT_restaurante TEXT,cantidad INT,precio_unitario NUMERIC);
        CREATE TABLE Insumo(id_insumo INT,NIT_restaurante TEXT,nombre TEXT,unidad_medida TEXT,cantidad_disponible NUMERIC,cantidad_minima NUMERIC);
        CREATE TABLE Movimiento_Inventario(id_movimiento INT,NIT_restaurante TEXT,id_insumo INT,id_factura INT,tipo TEXT,cantidad NUMERIC,fecha_hora TEXT);
        CREATE TABLE Empleado(id_empleado INT,NIT_restaurante TEXT,nombre_empleado TEXT);
        CREATE TABLE Pedido(num_pedido INT,NIT_restaurante TEXT,estado_pedido TEXT,fecha_inicio_preparacion TEXT,fecha_lista TEXT);
        CREATE TABLE Receta(num_serial_producto INT,id_insumo INT,NIT_restaurante TEXT,cantidad NUMERIC);
        CREATE TABLE v_estado_mesas(NIT_restaurante TEXT,estado_mesa TEXT);
        INSERT INTO Factura VALUES (406,'900123456-1',308,11,61000,61000,'2026-11-25 23:59:59','Efectivo',70000),
        (407,'900123456-1',309,11,15000,15000,'2026-11-25 00:00:00','Tarjeta',15000),
        (408,'900123456-1',310,11,10000,9000,'2026-11-26 00:00:00','Efectivo',NULL),
        (401,'900123456-1',301,11,70000,60000,'2026-10-31 13:00:00','Efectivo',NULL),
        (406,'otro',308,11,999999,999999,'2026-11-25 12:00:00','Efectivo',1000000);
        INSERT INTO Producto VALUES(102,'900123456-1','Cabrito','Plato'),(105,'900123456-1','Limonada','Bebida'),(102,'otro','Otro','Otro');
        INSERT INTO Detalle_Pedido VALUES(308,102,'900123456-1',1,45000),(308,105,'900123456-1',2,8000),(309,105,'900123456-1',3,5000),(301,102,'900123456-1',2,NULL),(307,102,'900123456-1',1,45000),(308,102,'otro',99,9999);
        INSERT INTO Insumo VALUES(201,'900123456-1','Carne','Kg',5,5),(203,'900123456-1','Panela','Und',10,2),(201,'otro','Otro','Kg',100,1);
        INSERT INTO Movimiento_Inventario VALUES(1,'900123456-1',201,406,'Salida',0.5,'2026-11-25 10:00:00'),(2,'900123456-1',203,406,'Salida',2,'2026-11-25 10:00:00'),(3,'900123456-1',201,NULL,'AjusteSalida',3,'2026-11-25 11:00:00'),(4,'otro',201,406,'Salida',99,'2026-11-25 10:00:00'),(5,'900123456-1',201,408,'Salida',0.5,'2026-11-26 00:00:00');
        INSERT INTO Empleado VALUES(11,'900123456-1','Camila'),(11,'otro','Otro');
        INSERT INTO Pedido VALUES(308,'900123456-1','Cerrado','2026-11-25 10:00:00','2026-11-25 10:08:00'),(309,'900123456-1','Cerrado','2026-11-25 10:00:00','2026-11-25 10:12:00'),(307,'900123456-1','Tomado',NULL,NULL),(301,'900123456-1','Tomado',NULL,NULL),(311,'900123456-1','Lista','2026-11-25 11:00:00','2026-11-25 10:00:00'),(312,'900123456-1','Cancelado','2026-11-25 10:00:00','2026-11-25 10:01:00'),(308,'otro','Tomado',NULL,NULL);
        INSERT INTO Receta VALUES(102,201,'900123456-1',0.5);
        INSERT INTO v_estado_mesas VALUES('900123456-1','Libre'),('900123456-1','Ocupada'),('900123456-1','Inactiva'),('otro','Ocupada');
        ''')
    def test_fechas(self):
        self.assertEqual(self.p,('2026-11-24','2026-11-25','2026-11-26'))
        self.assertEqual(periodo('2024-02-29','2024-02-29')[2],'2024-03-01')
        for a,b in [('2026-2-1','2026-02-02'),('2026-02-30','2026-03-01'),('2026-02-02','2026-02-01'),('2024-01-01','2026-01-01'),(None,'2026-01-01'),('9999-12-31','9999-12-31')]:
            with self.subTest(a=a,b=b),self.assertRaises(ErrorPedido):periodo(a,b)
    def test_ventas_limites_y_nit(self):
        r=ventas(self.c,NIT,self.p);self.assertEqual(r['resumen'],dict(facturas=2,ventas_totales='76000.00',subtotal='76000.00',ticket_promedio='38000.00'));self.assertEqual(r['serie_diaria'][0]['total'],'0.00')
    def test_sin_ventas(self):
        r=ventas(self.c,NIT,periodo('2025-01-01','2025-01-01'));self.assertEqual(r['resumen']['ticket_promedio'],'0.00');self.assertEqual(r['resumen']['facturas'],0)
    def test_productos_facturados(self):
        r=productos(self.c,NIT,self.p);self.assertEqual(r['total_unidades'],6);self.assertEqual(r['productos'][0]['unidades'],5);self.assertEqual(r['productos'][0]['importe_conocido'],'31000.00')
    def test_precio_historico_desconocido(self):
        r=productos(self.c,NIT,periodo('2026-10-31','2026-10-31'))['productos'][0];self.assertIsNone(r['importe_conocido']);self.assertEqual(r['unidades_sin_precio'],2)
    def test_consumo_no_ajustes(self):
        r=consumo(self.c,NIT,self.p);self.assertEqual(r['insumos'][0]['cantidad_consumida'],'0.50');self.assertEqual(r['insumos'][1]['cantidad_consumida'],'2.00');self.assertEqual(r['facturas_sin_movimientos'],1)
    def test_consumo_historico(self):
        r=consumo(self.c,NIT,periodo('2026-10-31','2026-10-31'));self.assertEqual(r['insumos'],[]);self.assertEqual(r['facturas_sin_movimientos'],1)
    def test_cierre(self):
        r=cierre_caja(self.c,NIT,self.p);self.assertEqual(r['total'],'76000.00');self.assertEqual(r['por_cajero_metodo'][0]['cambio'],'9000.00');self.assertIsNone(r['por_cajero_metodo'][1]['cambio']);self.assertEqual(r['por_cajero_metodo'][0]['cajero'],'Camila')
    def test_cierre_historico(self):
        r=cierre_caja(self.c,NIT,periodo('2026-10-31','2026-10-31'))['por_cajero_metodo'][0];self.assertEqual(r['efectivo_sin_dato'],1);self.assertIsNone(r['efectivo_recibido'])
    def test_dashboard(self):
        r=dashboard(self.c,NIT,self.p);self.assertEqual(r['preparacion'],{'muestra':2,'promedio_segundos':600.0});self.assertEqual(r['estado_actual']['mesas'],{'Libre':1,'Ocupada':1,'Inactiva':1});self.assertEqual(r['estado_actual']['pedidos_pendientes']['Tomado'],1);self.assertEqual(r['estado_actual']['inventario']['Bajo'],1)
    def test_dashboard_sin_tiempos(self):
        r=dashboard(self.c,NIT,periodo('2025-01-01','2025-01-01'));self.assertIsNone(r['preparacion']['promedio_segundos']);self.assertEqual(r['estado_actual']['mesas']['Libre'],1)
    def test_solo_lectura(self):
        antes=self.db.total_changes;dashboard(self.c,NIT,self.p);consumo(self.c,NIT,self.p);self.assertEqual(self.db.total_changes,antes)

class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('SECRET_KEY','clave-exclusiva-de-pruebas-automatizadas-123456')
        from app import app
        cls.app=app
    def setUp(self):
        self.client=self.app.test_client()
        self.empleado=dict(id_empleado=16,NIT_restaurante=NIT,nombre_empleado='Roberto',usuario_software='rjefe',activo=1,estado_suscripcion_software='Activo',es_mesero=0,es_cocinero=0,es_cajero=0,es_administrador=1)
        p=patch('backend.auth.buscar_empleado',return_value=self.empleado);p.start();self.addCleanup(p.stop)
        self.rutas={'dashboard':'dashboard','reportes/ventas':'ventas','reportes/productos':'productos','reportes/consumo':'consumo','reportes/cierre-caja':'cierre_caja'}
    def sesion(self):
        with self.client.session_transaction() as s:s['id_empleado']=16;s['nit']=NIT
    def url(self,r):return '/api/administracion/'+r
    def test_sin_sesion(self):
        for r in self.rutas:self.assertEqual(self.client.get(self.url(r)).status_code,401)
    def test_otro_rol(self):
        self.sesion();self.empleado.update(es_administrador=0,es_cajero=1)
        for r in self.rutas:self.assertEqual(self.client.get(self.url(r)).status_code,403)
    def test_rutas(self):
        self.sesion()
        for r,f in self.rutas.items():
            with self.subTest(r=r),patch('backend.administracion.get_connection') as c,patch('backend.administracion.'+f,return_value={'ok':True}) as fn:
                res=self.client.get(self.url(r)+'?desde=2026-11-24&hasta=2026-11-25');self.assertEqual(res.status_code,200);self.assertEqual(fn.call_args.args[1:],(NIT,('2026-11-24','2026-11-25','2026-11-26')));c.return_value.close.assert_called_once()
    def test_parametros(self):
        self.sesion()
        for q in ('?desde=2026-11-25','?nit=otro','?desde=x&hasta=y','?desde=2026-11-25&desde=2026-11-24&hasta=2026-11-25'):
            self.assertEqual(self.client.get(self.url('dashboard')+q).status_code,400)
    def test_fallo_bd(self):
        self.sesion()
        with patch('backend.administracion.get_connection',side_effect=RuntimeError('privado')):
            res=self.client.get(self.url('dashboard'));self.assertEqual(res.status_code,503);self.assertNotIn('privado',str(res.json))

if __name__=='__main__':unittest.main()
