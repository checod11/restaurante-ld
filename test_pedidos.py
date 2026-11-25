"""Pruebas locales sin alterar MariaDB. SQLite simula SQL, no bloqueos InnoDB."""
import os
import sqlite3
import unittest
from unittest.mock import patch
from backend.pedidos import ErrorPedido, validar_pedido, registrar_pedido, consultar_detalle

NIT='900123456-1'

class Cursor:
    def __init__(self, db): self.c=db.cursor()
    def __enter__(self): return self
    def __exit__(self,*args): self.c.close()
    def execute(self, sql, params=()):
        return self.c.execute(sql.replace('%s','?').replace(' FOR UPDATE','').replace('NOW()','CURRENT_TIMESTAMP'),params)
    def executemany(self,sql,params): return self.c.executemany(sql.replace('%s','?'),params)
    def fetchone(self):
        r=self.c.fetchone(); return dict(r) if r else None
    def fetchall(self): return [dict(r) for r in self.c.fetchall()]

class Conexion:
    def __init__(self,db): self.db=db
    def begin(self): self.db.execute('BEGIN')
    def cursor(self): return Cursor(self.db)
    def commit(self): self.db.commit()
    def rollback(self): self.db.rollback()
    def close(self): pass

class PedidosTest(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:'); self.db.row_factory=sqlite3.Row
        self.addCleanup(self.db.close)
        self.db.executescript('''
        CREATE TABLE Restaurante(NIT TEXT PRIMARY KEY,estado_suscripcion_software TEXT);
        CREATE TABLE Empleado(id_empleado INT,NIT_restaurante TEXT,activo INT);
        CREATE TABLE Mesero(id_empleado INT,NIT_restaurante TEXT);
        CREATE TABLE Mesa(num_mesa INT,NIT_restaurante TEXT,activa INT);
        CREATE TABLE Producto(num_serial INT,NIT_restaurante TEXT,nombre TEXT,precio NUMERIC,disponibilidad TEXT,categoria_plato TEXT);
        CREATE TABLE Receta(num_serial_producto INT,id_insumo INT,NIT_restaurante TEXT,cantidad NUMERIC);
        CREATE TABLE Insumo(id_insumo INT,NIT_restaurante TEXT,cantidad_disponible NUMERIC);
        CREATE TABLE Pedido(num_pedido INT,NIT_restaurante TEXT,id_mesero INT,num_mesa INT,fecha_hora_pedido TEXT,estado_pedido TEXT,PRIMARY KEY(num_pedido,NIT_restaurante));
        CREATE TABLE Detalle_Pedido(num_pedido INT,num_serial_producto INT,NIT_restaurante TEXT,cantidad INT,nota_especial TEXT,precio_unitario NUMERIC,PRIMARY KEY(num_pedido,num_serial_producto,NIT_restaurante));
        CREATE TABLE Factura(num_pedido INT,NIT_restaurante TEXT);
        CREATE TABLE auditoria(num_pedido INT);
        CREATE TRIGGER aud AFTER INSERT ON Pedido BEGIN INSERT INTO auditoria VALUES(NEW.num_pedido); END;
        INSERT INTO Restaurante VALUES('900123456-1','Activo'),('otro','Activo');
        INSERT INTO Empleado VALUES(1,'900123456-1',1),(2,'900123456-1',1);
        INSERT INTO Mesero VALUES(1,'900123456-1'),(2,'900123456-1');
        INSERT INTO Mesa VALUES(6,'900123456-1',1),(7,'900123456-1',0),(99,'otro',1);
        INSERT INTO Producto VALUES(102,'900123456-1','Cabrito',45000,'Disponible','Platos'),(105,'900123456-1','Limonada',8000,'Disponible','Bebidas'),(101,'900123456-1','Sin receta',25000,'Disponible','Sopas'),(500,'otro','Otro',100,'Disponible','Otro');
        INSERT INTO Insumo VALUES(1,'900123456-1',5),(2,'900123456-1',5);
        INSERT INTO Receta VALUES(102,1,'900123456-1',1),(105,1,'900123456-1',1),(105,2,'900123456-1',1);
        INSERT INTO Pedido VALUES(307,'900123456-1',2,6,'2026-01-01','Tomado'),(999,'otro',1,99,'2026-01-01','Tomado');
        INSERT INTO Detalle_Pedido VALUES(307,102,'900123456-1',1,NULL,45000);
        DELETE FROM auditoria;
        ''')
        self.c=Conexion(self.db)
    def crear(self,items=None,mesa=6,mesero=1):
        mesa,items=validar_pedido({'num_mesa':mesa,'productos':items if items is not None else [{'num_serial':102,'cantidad':1},{'num_serial':105,'cantidad':2,'nota_especial':'Sin hielo'}]})
        return registrar_pedido(self.c,NIT,mesero,mesa,items)
    def test_registro_y_precio(self):
        p=self.crear(); self.assertEqual(p['num_pedido'],308); self.assertEqual(p['subtotal'],'61000.00'); self.assertEqual(p['estado_pedido'],'Tomado'); self.assertEqual(p['productos'][1]['nota_especial'],'Sin hielo')
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM auditoria').fetchone()[0],1)
        self.assertEqual(self.db.execute('SELECT cantidad_disponible FROM Insumo WHERE id_insumo=1').fetchone()[0],5)
        self.assertEqual(consultar_detalle(self.c,NIT,1,308)['subtotal'],'61000.00')
    def test_carrito_compartido(self):
        with self.assertRaisesRegex(ErrorPedido,'carrito completo'): self.crear([{'num_serial':102,'cantidad':3},{'num_serial':105,'cantidad':2}])
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM Pedido').fetchone()[0],2)
    def test_reserva_nuevo_pedido(self):
        self.crear();
        with self.assertRaises(ErrorPedido): self.crear()
    def test_mesa_inactiva(self):
        with self.assertRaisesRegex(ErrorPedido,'inactiva'): self.crear(mesa=7)
    def test_mesa_otro_restaurante(self):
        with self.assertRaisesRegex(ErrorPedido,'no encontrada'): self.crear(mesa=99)
    def test_producto_sin_receta(self):
        with self.assertRaises(ErrorPedido): self.crear([{'num_serial':101,'cantidad':1}])
    def test_producto_otro_restaurante(self):
        with self.assertRaises(ErrorPedido) as e: self.crear([{'num_serial':500,'cantidad':1}])
        self.assertEqual(e.exception.estado,404)
    def test_rollback(self):
        self.db.executescript("CREATE TRIGGER fallo BEFORE INSERT ON Detalle_Pedido WHEN NEW.num_serial_producto=105 BEGIN SELECT RAISE(ABORT,'fallo'); END;")
        with self.assertRaises(sqlite3.IntegrityError): self.crear()
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM Pedido').fetchone()[0],2)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM Detalle_Pedido').fetchone()[0],1)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM auditoria').fetchone()[0],0)
    def test_otro_mesero(self):
        with self.assertRaises(ErrorPedido) as e: consultar_detalle(self.c,NIT,1,307)
        self.assertEqual(e.exception.estado,404)
    def test_validaciones(self):
        for items in ([],[{'num_serial':102,'cantidad':0}],[{'num_serial':102,'cantidad':True}],[{'num_serial':102,'cantidad':1,'precio':1}],[{'num_serial':102,'cantidad':1,'nota_especial':'x'*256}],[{'num_serial':102,'cantidad':1}]*2):
            with self.subTest(items=items), self.assertRaises(ErrorPedido): self.crear(items)
    def test_mesero_inactivo(self):
        self.db.execute('UPDATE Empleado SET activo=0 WHERE id_empleado=1');self.db.commit()
        with self.assertRaises(ErrorPedido) as e: self.crear()
        self.assertEqual(e.exception.estado,403)

class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('SECRET_KEY','clave-exclusiva-de-pruebas-automatizadas-123456')
        from app import app
        cls.app=app
    def setUp(self):
        self.client=self.app.test_client()
        self.empleado=dict(id_empleado=1,NIT_restaurante=NIT,nombre_empleado='Prueba',usuario_software='prueba',activo=1,estado_suscripcion_software='Activo',es_mesero=1,es_cocinero=0,es_cajero=0,es_administrador=0)
        p=patch('backend.auth.buscar_empleado',return_value=self.empleado);p.start();self.addCleanup(p.stop)
        self.body={'num_mesa':6,'productos':[{'num_serial':102,'cantidad':1}]}
    def sesion(self):
        with self.client.session_transaction() as s: s['id_empleado']=1;s['nit']=NIT
    def test_sin_sesion(self): self.assertEqual(self.client.post('/api/salon/pedidos',json=self.body).status_code,401)
    def test_rol(self):
        self.sesion();self.empleado['es_mesero']=0;self.empleado['es_cajero']=1
        self.assertEqual(self.client.post('/api/salon/pedidos',json=self.body).status_code,403)
    def test_crear(self):
        self.sesion()
        with patch('backend.salon.get_connection') as c,patch('backend.salon.registrar_pedido',return_value={'num_pedido':308}) as r:
            self.assertEqual(self.client.post('/api/salon/pedidos',json=self.body).status_code,201)
            self.assertEqual(r.call_args.args[1:4],(NIT,1,6));c.return_value.close.assert_called_once()
    def test_datos_invalidos(self):
        self.sesion()
        self.assertEqual(self.client.post('/api/salon/pedidos',json={**self.body,'nit':'otro'}).status_code,400)

if __name__=='__main__': unittest.main()
