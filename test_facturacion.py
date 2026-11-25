"""Pruebas sin tocar MariaDB; SQLite simula las operaciones, no bloqueos InnoDB."""
import os,sqlite3,unittest
from unittest.mock import patch
from test_pedidos import Conexion,NIT
from backend.facturacion import facturar,precuenta,consultar_pendientes,comprobante,validar_pago
from backend.pedidos import ErrorPedido

PAGO={'metodo_pago':'Efectivo','monto_recibido':'70000.00'}

class FacturacionTest(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:'); self.db.row_factory=sqlite3.Row
        self.addCleanup(self.db.close)
        self.db.executescript('''
        CREATE TABLE Restaurante(NIT TEXT PRIMARY KEY,estado_suscripcion_software TEXT);
        CREATE TABLE Empleado(id_empleado INT,NIT_restaurante TEXT,activo INT);
        CREATE TABLE Cajero(id_empleado INT,NIT_restaurante TEXT);
        CREATE TABLE Mesa(num_mesa INT,NIT_restaurante TEXT,activa INT);
        CREATE TABLE Pedido(num_pedido INT,NIT_restaurante TEXT,id_mesero INT,num_mesa INT,fecha_hora_pedido TEXT,estado_pedido TEXT,PRIMARY KEY(num_pedido,NIT_restaurante));
        CREATE TABLE Producto(num_serial INT,NIT_restaurante TEXT,nombre TEXT,precio NUMERIC);
        CREATE TABLE Detalle_Pedido(num_pedido INT,num_serial_producto INT,NIT_restaurante TEXT,cantidad INT,nota_especial TEXT,precio_unitario NUMERIC);
        CREATE TABLE Receta(num_serial_producto INT,id_insumo INT,NIT_restaurante TEXT,cantidad NUMERIC);
        CREATE TABLE Insumo(id_insumo INT,NIT_restaurante TEXT,cantidad_disponible NUMERIC);
        CREATE TABLE Factura(id_factura INT,NIT_restaurante TEXT,num_pedido INT,id_cajero INT,nombre_cliente TEXT,valor_total NUMERIC,subvalor_total NUMERIC,fecha_emision TEXT,metodo_pago TEXT,tipo_documento TEXT,estado_validacion TEXT,monto_recibido NUMERIC,PRIMARY KEY(id_factura,NIT_restaurante),UNIQUE(num_pedido,NIT_restaurante));
        CREATE TABLE Movimiento_Inventario(NIT_restaurante TEXT,id_insumo INT,id_empleado INT,id_factura INT,tipo TEXT,cantidad NUMERIC,fecha_hora TEXT,motivo TEXT,UNIQUE(id_factura,id_insumo,NIT_restaurante));
        CREATE TABLE auditoria(tipo TEXT);
        CREATE TRIGGER aud_fact AFTER INSERT ON Factura BEGIN INSERT INTO auditoria VALUES('factura'); END;
        CREATE TRIGGER aud_ins AFTER UPDATE ON Insumo BEGIN INSERT INTO auditoria VALUES('insumo'); END;
        CREATE VIEW v_estado_mesas AS SELECT m.*,CASE WHEN m.activa=0 THEN 'Inactiva' WHEN EXISTS(SELECT 1 FROM Pedido p WHERE p.NIT_restaurante=m.NIT_restaurante AND p.num_mesa=m.num_mesa AND p.estado_pedido NOT IN ('Cerrado','Cancelado') AND NOT EXISTS(SELECT 1 FROM Factura f WHERE f.NIT_restaurante=p.NIT_restaurante AND f.num_pedido=p.num_pedido)) THEN 'Ocupada' ELSE 'Libre' END AS estado_mesa FROM Mesa m;
        INSERT INTO Restaurante VALUES('900123456-1','Activo'),('otro','Activo');
        INSERT INTO Empleado VALUES(11,'900123456-1',1),(12,'900123456-1',0);
        INSERT INTO Cajero VALUES(11,'900123456-1'),(12,'900123456-1');
        INSERT INTO Mesa VALUES(6,'900123456-1',1),(7,'900123456-1',1);
        INSERT INTO Pedido VALUES(308,'900123456-1',1,6,'2026-01-01','Entregado'),(309,'900123456-1',1,7,'2026-01-01','Tomado'),(999,'otro',1,6,'2026-01-01','Entregado');
        INSERT INTO Producto VALUES(102,'900123456-1','Cabrito',99000),(105,'900123456-1','Limonada',9999);
        INSERT INTO Detalle_Pedido VALUES(308,102,'900123456-1',1,NULL,45000),(308,105,'900123456-1',2,'Sin hielo',8000);
        INSERT INTO Receta VALUES(102,1,'900123456-1',0.5),(105,1,'900123456-1',0.25),(105,2,'900123456-1',1);
        INSERT INTO Insumo VALUES(1,'900123456-1',5),(2,'900123456-1',10),(1,'otro',99);
        ''')
        self.c=Conexion(self.db)
    def pagar(self,datos=None,n=308,e=11): return facturar(self.c,NIT,e,n,PAGO if datos is None else datos)
    def error(self,codigo,datos=None,n=308,e=11):
        with self.assertRaises(ErrorPedido) as ex: self.pagar(datos,n,e)
        self.assertEqual(ex.exception.estado,codigo)
    def sql(self,s): self.db.execute(s);self.db.commit()
    def count(self,t): return self.db.execute('SELECT COUNT(*) FROM '+t).fetchone()[0]
    def test_pendientes(self): self.assertEqual([p['num_pedido'] for p in consultar_pendientes(self.c,NIT)['pedidos']],[308])
    def test_precio_historico(self): self.assertEqual(precuenta(self.c,NIT,308)['total'],'61000.00')
    def test_pago_y_comprobante(self):
        f=self.pagar();self.assertEqual(f['cambio'],'9000.00');self.assertEqual(f['estado_mesa'],'Libre');self.assertEqual(f['estado_pedido'],'Cerrado');self.assertEqual(f['estado_validacion'],'Demo');self.assertEqual(comprobante(self.c,NIT,308)['total'],'61000.00');self.assertEqual(consultar_pendientes(self.c,NIT)['total'],0)
    def test_descuento_compartido(self):
        self.pagar();self.assertEqual([x[0] for x in self.db.execute("SELECT cantidad_disponible FROM Insumo WHERE NIT_restaurante='900123456-1' ORDER BY id_insumo")],[4,8]);self.assertEqual(self.count('Movimiento_Inventario'),2);self.assertEqual(self.count('auditoria'),3)
    def test_pago_doble(self): self.pagar();self.error(409);self.assertEqual(self.count('Factura'),1);self.assertEqual(self.count('Movimiento_Inventario'),2)
    def test_pago_insuficiente(self): self.error(409,{'metodo_pago':'Efectivo','monto_recibido':'1000'});self.assertEqual(self.count('Factura'),0)
    def test_tarjeta_exacta(self):
        self.error(409,{'metodo_pago':'Tarjeta','monto_recibido':'70000'});self.assertEqual(self.pagar({'metodo_pago':'Tarjeta','monto_recibido':'61000'})['cambio'],'0.00')
    def test_mesa_sigue_ocupada(self): self.sql('UPDATE Pedido SET num_mesa=6 WHERE num_pedido=309');self.assertEqual(self.pagar()['estado_mesa'],'Ocupada')
    def test_no_entregado(self): self.error(409,n=309)
    def test_otro_restaurante(self): self.error(404,n=999)
    def test_cajero_inactivo(self): self.error(403,e=12)
    def test_sin_precio(self): self.sql('UPDATE Detalle_Pedido SET precio_unitario=NULL');self.error(409)
    def test_sin_receta(self): self.sql('DELETE FROM Receta WHERE num_serial_producto=102');self.error(409)
    def test_stock_insuficiente(self): self.sql('UPDATE Insumo SET cantidad_disponible=0 WHERE id_insumo=2');self.error(409);self.assertEqual(self.count('Factura'),0)
    def test_rollback(self):
        self.db.executescript("CREATE TRIGGER fallo BEFORE INSERT ON Movimiento_Inventario WHEN NEW.id_insumo=2 BEGIN SELECT RAISE(ABORT,'fallo'); END;")
        with self.assertRaises(sqlite3.IntegrityError): self.pagar()
        self.assertEqual(self.count('Factura'),0);self.assertEqual(self.count('Movimiento_Inventario'),0);self.assertEqual(self.count('auditoria'),0);self.assertEqual(self.db.execute("SELECT cantidad_disponible FROM Insumo WHERE id_insumo=1 AND NIT_restaurante='900123456-1'").fetchone()[0],5);self.assertEqual(precuenta(self.c,NIT,308)['estado_pedido'],'Entregado')
    def test_validacion(self):
        for datos in ({'metodo_pago':'Efectivo','monto_recibido':True},{'metodo_pago':'Efectivo','monto_recibido':'1.001'},{'metodo_pago':'Bitcoin','monto_recibido':'61000'},{**PAGO,'id_cajero':99},{**PAGO,'total':1}):
            with self.subTest(datos=datos),self.assertRaises(ErrorPedido): validar_pago(datos)

class ApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('SECRET_KEY','clave-exclusiva-de-pruebas-automatizadas-123456')
        from app import app
        cls.app=app
    def setUp(self):
        self.client=self.app.test_client()
        self.empleado=dict(id_empleado=11,NIT_restaurante=NIT,nombre_empleado='Camila',usuario_software='ccaja',activo=1,estado_suscripcion_software='Activo',es_mesero=0,es_cocinero=0,es_cajero=1,es_administrador=0)
        p=patch('backend.auth.buscar_empleado',return_value=self.empleado);p.start();self.addCleanup(p.stop)
    def sesion(self):
        with self.client.session_transaction() as s: s['id_empleado']=11;s['nit']=NIT
    def test_sin_sesion(self): self.assertEqual(self.client.get('/api/caja/pendientes').status_code,401)
    def test_rol_incorrecto(self):
        self.sesion();self.empleado.update(es_cajero=0,es_mesero=1);self.assertEqual(self.client.post('/api/caja/pedidos/308/pagar',json=PAGO).status_code,403)
    def test_pago_api(self):
        self.sesion()
        with patch('backend.caja.get_connection') as c,patch('backend.caja.facturar',return_value={'id_factura':406}) as f:
            r=self.client.post('/api/caja/pedidos/308/pagar',json=PAGO);self.assertEqual(r.status_code,201);self.assertEqual(r.json['factura']['id_factura'],406);self.assertEqual(f.call_args.args[1:],(NIT,11,308,PAGO));c.return_value.close.assert_called_once()
    def test_tipo_contenido(self): self.sesion();self.assertEqual(self.client.post('/api/caja/pedidos/308/pagar',data='x').status_code,415)
    def test_prec_api(self):
        self.sesion()
        with patch('backend.caja.get_connection'),patch('backend.caja.precuenta',return_value={'total':'61000.00'}) as f:
            self.assertEqual(self.client.get('/api/caja/pedidos/308/precuenta').status_code,200);self.assertEqual(f.call_args.args[1:],(NIT,308))

if __name__=='__main__': unittest.main()
