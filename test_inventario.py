"""Pruebas aisladas: SQLite simula SQL; las pruebas Flask usan mocks."""
import os
import sqlite3
import unittest
from unittest.mock import patch
from test_pedidos import Conexion,NIT
from backend.inventario import consultar_inventario,consultar_movimientos,registrar_movimiento,validar_movimiento
from backend.pedidos import ErrorPedido


class InventarioTest(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:');self.db.row_factory=sqlite3.Row
        self.addCleanup(self.db.close)
        self.db.create_function('LAST_INSERT_ID',0,lambda:self.db.execute('SELECT last_insert_rowid()').fetchone()[0])
        self.db.executescript('''
        CREATE TABLE Restaurante(NIT TEXT PRIMARY KEY,estado_suscripcion_software TEXT);
        CREATE TABLE Empleado(id_empleado INT,NIT_restaurante TEXT,activo INT,nombre_empleado TEXT);
        CREATE TABLE Administrador(id_empleado INT,NIT_restaurante TEXT);
        CREATE TABLE Insumo(id_insumo INT,NIT_restaurante TEXT,nombre TEXT,unidad_medida TEXT,cantidad_disponible NUMERIC,cantidad_minima NUMERIC);
        CREATE TABLE Pedido(num_pedido INT,NIT_restaurante TEXT,estado_pedido TEXT);
        CREATE TABLE Detalle_Pedido(num_pedido INT,num_serial_producto INT,NIT_restaurante TEXT,cantidad INT);
        CREATE TABLE Receta(num_serial_producto INT,id_insumo INT,NIT_restaurante TEXT,cantidad NUMERIC);
        CREATE TABLE Factura(num_pedido INT,NIT_restaurante TEXT);
        CREATE TABLE Movimiento_Inventario(id_movimiento INTEGER PRIMARY KEY AUTOINCREMENT,NIT_restaurante TEXT,id_insumo INT,id_empleado INT,id_factura INT,tipo TEXT,cantidad NUMERIC,fecha_hora TEXT,motivo TEXT);
        CREATE TABLE auditoria(tipo TEXT);
        CREATE TRIGGER aud_stock AFTER UPDATE ON Insumo BEGIN INSERT INTO auditoria VALUES('stock'); END;
        CREATE TRIGGER aud_mov AFTER INSERT ON Movimiento_Inventario BEGIN INSERT INTO auditoria VALUES('mov'); END;
        INSERT INTO Restaurante VALUES('900123456-1','Activo'),('otro','Activo');
        INSERT INTO Empleado VALUES(16,'900123456-1',1,'Roberto'),(17,'900123456-1',0,'Inactivo'),(11,'900123456-1',1,'Caja');
        INSERT INTO Administrador VALUES(16,'900123456-1'),(17,'900123456-1');
        INSERT INTO Insumo VALUES(201,'900123456-1','Carne','Kg',15,5),(202,'900123456-1','Maiz','Kg',0,10),(203,'900123456-1','Panela','Und',15,15),(201,'otro','Otro','Kg',100,1),(999,'otro','Otro','Kg',100,1);
        INSERT INTO Pedido VALUES(307,'900123456-1','Preparacion'),(308,'900123456-1','Cerrado'),(309,'900123456-1','Cancelado'),(310,'900123456-1','Entregado'),(307,'otro','Tomado');
        INSERT INTO Detalle_Pedido VALUES(307,102,'900123456-1',1),(308,102,'900123456-1',2),(309,102,'900123456-1',8),(310,102,'900123456-1',9),(307,102,'otro',50);
        INSERT INTO Receta VALUES(102,201,'900123456-1',0.5),(102,201,'otro',2);
        INSERT INTO Factura VALUES(310,'900123456-1');
        INSERT INTO Movimiento_Inventario(NIT_restaurante,id_insumo,id_empleado,id_factura,tipo,cantidad,fecha_hora,motivo) VALUES('900123456-1',201,11,406,'Salida',0.5,'2026-11-25','Venta');
        DELETE FROM auditoria;
        ''');self.c=Conexion(self.db)
    def mov(self,tipo='Entrada',cantidad='2.50',insumo=201,empleado=16,motivo='Prueba'):
        return registrar_movimiento(self.c,NIT,empleado,dict(id_insumo=insumo,tipo=tipo,cantidad=cantidad,motivo=motivo))
    def stock(self): return consultar_inventario(self.c,NIT)['insumos'][0]
    def count(self,t): return self.db.execute('SELECT COUNT(*) FROM '+t).fetchone()[0]
    def error(self,estado,**args):
        with self.assertRaises(ErrorPedido) as e:self.mov(**args)
        self.assertEqual(e.exception.estado,estado)
    def test_reservas_y_separacion(self):
        r=consultar_inventario(self.c,NIT);self.assertEqual(r['total'],3);self.assertEqual(self.stock()['comprometido'],'0.50');self.assertEqual(self.stock()['utilizable'],'14.50')
    def test_alertas(self):
        r=consultar_inventario(self.c,NIT,True);self.assertEqual(r['total'],2);self.assertEqual(r['resumen'],{'Normal':1,'Bajo':1,'Agotado':1})
    def test_entrada(self):
        r=self.mov();self.assertEqual(r['stock_anterior'],'15.00');self.assertEqual(r['stock_nuevo'],'17.50');self.assertEqual(r['id_movimiento'],2);self.assertIsNone(r['id_factura']);self.assertEqual(self.count('auditoria'),2)
    def test_ajuste_entrada(self):self.assertEqual(self.mov(tipo='AjusteEntrada')['stock_nuevo'],'17.50')
    def test_ajuste_salida(self):self.assertEqual(self.mov(tipo='AjusteSalida',cantidad='9.50')['insumo']['estado_stock'],'Bajo')
    def test_reserva_protegida(self):
        self.error(409,tipo='AjusteSalida',cantidad='14.51');self.assertEqual(self.stock()['cantidad_disponible'],'15.00');self.assertEqual(self.count('Movimiento_Inventario'),1)
    def test_agotado_con_reserva(self):self.assertEqual(self.mov(tipo='AjusteSalida',cantidad='14.50')['insumo']['estado_stock'],'Agotado')
    def test_stock_negativo(self):self.error(409,tipo='AjusteSalida',cantidad='16')
    def test_limite_decimal(self):self.error(409,cantidad='99999999.99')
    def test_inactivo(self):self.error(403,empleado=17)
    def test_no_admin(self):self.error(403,empleado=11)
    def test_otro_restaurante(self):self.error(404,insumo=999)
    def test_historial(self):
        self.mov();r=consultar_movimientos(self.c,NIT,201);self.assertEqual([x['tipo'] for x in r['movimientos']],['Entrada','Salida']);self.assertEqual(r['movimientos'][1]['id_factura'],406);self.assertEqual(consultar_movimientos(self.c,NIT,202)['total'],0)
    def test_paginacion(self):
        for _ in range(101):self.mov(cantidad='1')
        r=consultar_movimientos(self.c,NIT);self.assertEqual(r['total'],100);self.assertEqual(consultar_movimientos(self.c,NIT,antes_de=r['siguiente_antes_de'])['total'],2)
    def test_rollback(self):
        self.db.executescript("CREATE TRIGGER fallo BEFORE INSERT ON Movimiento_Inventario BEGIN SELECT RAISE(ABORT,'fallo'); END;")
        with self.assertRaises(sqlite3.IntegrityError):self.mov()
        self.assertEqual(self.stock()['cantidad_disponible'],'15.00');self.assertEqual(self.count('auditoria'),0);self.assertEqual(self.count('Movimiento_Inventario'),1)
    def test_validaciones(self):
        base=dict(id_insumo=201,tipo='Entrada',cantidad='1',motivo='Prueba')
        for cambio in ({'cantidad':True},{'cantidad':0},{'cantidad':'1.001'},{'cantidad':'NaN'},{'cantidad':'-1'},{'tipo':'Salida'},{'tipo':[]},{'motivo':' '},{'motivo':'a'*151},{'id_insumo':True},{'id_empleado':9},{'id_factura':406}):
            with self.subTest(cambio=cambio),self.assertRaises(ErrorPedido):validar_movimiento({**base,**cambio})


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
    def sesion(self):
        with self.client.session_transaction() as s:s['id_empleado']=16;s['nit']=NIT
    def test_sin_sesion(self):self.assertEqual(self.client.get('/api/administracion/inventario').status_code,401)
    def test_otro_rol(self):
        self.sesion();self.empleado.update(es_administrador=0,es_cajero=1);self.assertEqual(self.client.post('/api/administracion/inventario/movimientos',json={}).status_code,403)
    def test_alertas_api(self):
        self.sesion()
        with patch('backend.administracion.get_connection') as c,patch('backend.administracion.consultar_inventario',return_value={'total':0}) as f:
            self.assertEqual(self.client.get('/api/administracion/inventario/alertas').status_code,200);self.assertEqual(f.call_args.args[1:],(NIT,True));c.return_value.close.assert_called_once()
    def test_registro_api(self):
        self.sesion();datos=dict(id_insumo=201,tipo='Entrada',cantidad='1',motivo='Prueba')
        with patch('backend.administracion.get_connection'),patch('backend.administracion.registrar_movimiento',return_value={'id_movimiento':1}) as f:
            r=self.client.post('/api/administracion/inventario/movimientos',json=datos);self.assertEqual(r.status_code,201);self.assertEqual(r.json['movimiento']['id_movimiento'],1);self.assertEqual(f.call_args.args[1:],(NIT,16,datos))
    def test_filtro_invalido(self):
        self.sesion();self.assertEqual(self.client.get('/api/administracion/inventario/movimientos?id_insumo=-1').status_code,400)
    def test_tipo_contenido(self):
        self.sesion();self.assertEqual(self.client.post('/api/administracion/inventario/movimientos',data='x').status_code,415)

if __name__=='__main__':unittest.main()
