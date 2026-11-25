"""Pruebas del flujo de cocina. SQLite no reproduce bloqueos InnoDB."""
import os
import sqlite3
import unittest
from unittest.mock import patch
from test_pedidos import Conexion, NIT
from backend.comandas import consultar_tablero, cambiar_estado
from backend.pedidos import ErrorPedido


class ComandasTest(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:'); self.db.row_factory=sqlite3.Row
        self.addCleanup(self.db.close)
        self.db.executescript('''
        CREATE TABLE Restaurante(NIT TEXT PRIMARY KEY,estado_suscripcion_software TEXT);
        CREATE TABLE Empleado(id_empleado INT,NIT_restaurante TEXT,activo INT,nombre_empleado TEXT);
        CREATE TABLE Cocinero(id_empleado INT,NIT_restaurante TEXT);
        CREATE TABLE Mesero(id_empleado INT,NIT_restaurante TEXT);
        CREATE TABLE Pedido(num_pedido INT,NIT_restaurante TEXT,id_mesero INT,num_mesa INT,
          fecha_hora_pedido TEXT,estado_pedido TEXT,id_cocinero INT,fecha_inicio_preparacion TEXT,
          fecha_lista TEXT,fecha_entrega TEXT,PRIMARY KEY(num_pedido,NIT_restaurante));
        CREATE TABLE Detalle_Pedido(num_pedido INT,num_serial_producto INT,NIT_restaurante TEXT,cantidad INT,nota_especial TEXT);
        CREATE TABLE Producto(num_serial INT,NIT_restaurante TEXT,nombre TEXT);
        CREATE TABLE Factura(num_pedido INT,NIT_restaurante TEXT);
        CREATE TABLE auditoria(numero INT,estado TEXT);
        CREATE TRIGGER aud AFTER UPDATE ON Pedido BEGIN INSERT INTO auditoria VALUES(NEW.num_pedido,NEW.estado_pedido); END;
        INSERT INTO Restaurante VALUES('900123456-1','Activo'),('otro','Activo');
        INSERT INTO Empleado VALUES(1,'900123456-1',1,'Carlos'),(2,'900123456-1',1,'Maria'),(6,'900123456-1',1,'Pedro'),(7,'900123456-1',1,'Sonia'),(1,'otro',1,'Otro');
        INSERT INTO Mesero VALUES(1,'900123456-1'),(2,'900123456-1');
        INSERT INTO Cocinero VALUES(6,'900123456-1'),(7,'900123456-1');
        INSERT INTO Pedido VALUES
          (308,'900123456-1',1,6,'2026-01-01 12:00:00','Tomado',NULL,NULL,NULL,NULL),
          (303,'900123456-1',1,2,'2026-01-01 12:00:00','Preparacion',NULL,NULL,NULL,NULL),
          (309,'900123456-1',1,7,'2026-01-01 12:00:00','Cancelado',NULL,NULL,NULL,NULL),
          (999,'otro',1,9,'2026-01-01 12:00:00','Tomado',NULL,NULL,NULL,NULL);
        INSERT INTO Producto VALUES(102,'900123456-1','Cabrito'),(105,'900123456-1','Limonada'),(102,'otro','Otro');
        INSERT INTO Detalle_Pedido VALUES(308,102,'900123456-1',1,NULL),(308,105,'900123456-1',2,'Sin hielo'),(999,102,'otro',1,NULL);
        INSERT INTO Factura VALUES(303,'900123456-1');
        ''')
        self.c=Conexion(self.db)
    def accion(self,a,e=6,n=308): return cambiar_estado(self.c,NIT,e,n,a)
    def error(self,codigo,a,e=6,n=308):
        with self.assertRaises(ErrorPedido) as exc: self.accion(a,e,n)
        self.assertEqual(exc.exception.estado,codigo)
    def test_tablero(self):
        t=consultar_tablero(self.c,NIT); self.assertEqual(t['total'],1)
        self.assertEqual(t['resumen'],{'Tomado':1,'Preparacion':0,'Lista':0})
        self.assertEqual(t['comandas']['Tomado'][0]['productos'][1]['nota_especial'],'Sin hielo')
    def test_ciclo(self):
        p=self.accion('iniciar'); self.assertEqual(p['id_cocinero'],6);self.assertIsNotNone(p['fecha_inicio_preparacion'])
        self.assertEqual(consultar_tablero(self.c,NIT)['resumen']['Preparacion'],1)
        p=self.accion('lista');self.assertEqual(p['estado_pedido'],'Lista');self.assertGreaterEqual(p['duracion_preparacion_segundos'],0)
        self.assertEqual(consultar_tablero(self.c,NIT)['resumen']['Lista'],1)
        p=self.accion('entregar',1);self.assertEqual(p['estado_pedido'],'Entregado');self.assertIsNotNone(p['fecha_entrega'])
        self.assertEqual(consultar_tablero(self.c,NIT)['total'],0)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM auditoria').fetchone()[0],3)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM Factura').fetchone()[0],1)
    def test_salto_estado(self): self.error(409,'lista')
    def test_repetir_inicio(self):
        self.accion('iniciar');self.error(409,'iniciar',7)
        self.assertEqual(self.db.execute('SELECT id_cocinero FROM Pedido WHERE num_pedido=308').fetchone()[0],6)
    def test_otro_cocinero(self): self.accion('iniciar');self.error(403,'lista',7)
    def test_otro_mesero(self): self.accion('iniciar');self.accion('lista');self.error(404,'entregar',2)
    def test_facturado(self): self.error(409,'lista',6,303)
    def test_otro_restaurante(self): self.error(404,'iniciar',6,999)
    def test_cancelado(self): self.error(409,'iniciar',6,309)
    def test_empleado_inactivo(self):
        self.db.execute('UPDATE Empleado SET activo=0 WHERE id_empleado=6');self.db.commit();self.error(403,'iniciar')
    def test_rollback(self):
        self.db.executescript("CREATE TRIGGER fallo AFTER UPDATE ON Pedido BEGIN SELECT RAISE(ABORT,'fallo'); END;")
        with self.assertRaises(sqlite3.IntegrityError): self.accion('iniciar')
        self.assertEqual(self.db.execute('SELECT estado_pedido FROM Pedido WHERE num_pedido=308').fetchone()[0],'Tomado')
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM auditoria').fetchone()[0],0)
    def test_sin_detalle(self):
        self.db.execute('DELETE FROM Detalle_Pedido WHERE num_pedido=308');self.db.commit();self.error(409,'iniciar')


class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('SECRET_KEY','clave-exclusiva-de-pruebas-automatizadas-123456')
        from app import app
        cls.app=app
    def setUp(self):
        self.client=self.app.test_client()
        self.empleado=dict(id_empleado=6,NIT_restaurante=NIT,nombre_empleado='Pedro',usuario_software='pchef',activo=1,estado_suscripcion_software='Activo',es_mesero=0,es_cocinero=1,es_cajero=0,es_administrador=0)
        p=patch('backend.auth.buscar_empleado',return_value=self.empleado);p.start();self.addCleanup(p.stop)
    def sesion(self):
        with self.client.session_transaction() as s: s['id_empleado']=self.empleado['id_empleado'];s['nit']=NIT
    def test_sin_sesion(self): self.assertEqual(self.client.get('/api/cocina/comandas').status_code,401)
    def test_rol_incorrecto(self):
        self.empleado.update(es_cocinero=0,es_cajero=1);self.sesion()
        self.assertEqual(self.client.post('/api/cocina/comandas/308/iniciar',json={}).status_code,403)
    def test_tablero_api(self):
        self.sesion()
        with patch('backend.cocina.get_connection') as c,patch('backend.cocina.consultar_tablero',return_value={'total':0}) as f:
            self.assertEqual(self.client.get('/api/cocina/comandas').status_code,200);self.assertEqual(f.call_args.args[1],NIT);c.return_value.close.assert_called_once()
    def test_accion_api(self):
        self.sesion()
        with patch('backend.cocina.get_connection') as c,patch('backend.cocina.cambiar_estado',return_value={'num_pedido':308}) as f:
            self.assertEqual(self.client.post('/api/cocina/comandas/308/iniciar',json={}).status_code,200);self.assertEqual(f.call_args.args[1:],(NIT,6,308,'iniciar'));c.return_value.close.assert_called_once()
    def test_identidad_no_manipulable(self):
        self.sesion();self.assertEqual(self.client.post('/api/cocina/comandas/308/lista',json={'id_cocinero':7}).status_code,400)
    def test_entrega_por_mesero(self):
        self.empleado.update(id_empleado=1,es_cocinero=0,es_mesero=1);self.sesion()
        with patch('backend.cocina.get_connection'),patch('backend.cocina.cambiar_estado',return_value={'num_pedido':308}) as f:
            self.assertEqual(self.client.post('/api/salon/pedidos/308/entregar',json={}).status_code,200);self.assertEqual(f.call_args.args[1:],(NIT,1,308,'entregar'))
        self.assertEqual(self.client.get('/api/cocina/comandas').status_code,403)

if __name__=='__main__': unittest.main()
