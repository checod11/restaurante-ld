import sqlite3,unittest
from decimal import Decimal
from unittest.mock import patch
from backend.gestion import guardar,catalogos,cantidad,roles_validos
from backend.pedidos import ErrorPedido
from test_pedidos import Conexion,Cursor,NIT

class C(Cursor):
    def execute(self,sql,params=()):return super().execute(sql.replace('CURDATE()','CURRENT_DATE'),tuple(str(x) if isinstance(x,Decimal) else x for x in params))
    def executemany(self,sql,params):return super().executemany(sql,[tuple(str(x) if isinstance(x,Decimal) else x for x in row) for row in params])
class DB(Conexion):
    def cursor(self):return C(self.db)
class GestionTest(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:');self.db.row_factory=sqlite3.Row;self.addCleanup(self.db.close);self.c=DB(self.db)
        self.db.executescript('''
        CREATE TABLE Restaurante(NIT TEXT,estado_suscripcion_software TEXT);
        CREATE TABLE Empleado(id_empleado INT,NIT_restaurante TEXT,nombre_empleado TEXT,cedula TEXT UNIQUE,usuario_software TEXT,`contraseña_software` TEXT,fecha_antiguedad TEXT,activo INT);
        CREATE TABLE Administrador(id_empleado INT,NIT_restaurante TEXT);
        CREATE TABLE Mesero(id_empleado INT,NIT_restaurante TEXT);
        CREATE TABLE Cajero(id_empleado INT,NIT_restaurante TEXT);
        CREATE TABLE Cocinero(id_empleado INT,NIT_restaurante TEXT);
        CREATE TABLE Producto(num_serial INT,NIT_restaurante TEXT,nombre TEXT,precio NUMERIC,categoria_plato TEXT,disponibilidad TEXT);
        CREATE TABLE Insumo(id_insumo INT,NIT_restaurante TEXT,nombre TEXT,unidad_medida TEXT,cantidad_disponible NUMERIC,cantidad_minima NUMERIC);
        CREATE TABLE Receta(num_serial_producto INT,id_insumo INT,NIT_restaurante TEXT,cantidad NUMERIC);
        CREATE TABLE Pedido(num_pedido INT,NIT_restaurante TEXT,estado_pedido TEXT,id_mesero INT,id_cocinero INT);
        CREATE TABLE Detalle_Pedido(num_pedido INT,NIT_restaurante TEXT,num_serial_producto INT,precio_unitario NUMERIC);
        CREATE TABLE Factura(num_pedido INT,NIT_restaurante TEXT,id_cajero INT);
        INSERT INTO Restaurante VALUES('900123456-1','Activo'),('otro','Activo');
        INSERT INTO Empleado VALUES(16,'900123456-1','Admin','1','admin','hash',NULL,1),(1,'900123456-1','Mesero','2','mesero','hash',NULL,1);
        INSERT INTO Administrador VALUES(16,'900123456-1'); INSERT INTO Mesero VALUES(1,'900123456-1');
        INSERT INTO Producto VALUES(102,'900123456-1','Cabrito',45000,'Platos','Disponible'),(105,'900123456-1','Limonada',8000,'Bebidas','Disponible'),(999,'otro','Otro',100,'Plato','Disponible');
        INSERT INTO Insumo VALUES(201,'900123456-1','Carne','Kg',15,5),(202,'900123456-1','Limón','Kg',10,3),(999,'otro','Otro','Kg',1,0);
        INSERT INTO Receta VALUES(102,201,'900123456-1',0.5),(105,202,'900123456-1',0.1);
        INSERT INTO Pedido VALUES(307,'900123456-1','Tomado',1,NULL); INSERT INTO Detalle_Pedido VALUES(307,'900123456-1',102,45000);
        ''')
    def save(self,a,d):return guardar(self.c,NIT,16,a,d)
    def test_catalogos_privados(self):
        r=catalogos(self.c,NIT);self.assertEqual(len(r['productos']),2);self.assertNotIn('contraseña_software',r['empleados'][0]);self.assertNotIn('cedula',r['empleados'][0])
    def test_producto_y_precio_historico(self):
        r=self.save('producto',dict(num_serial=102,nombre='Cabrito',precio='46000',categoria_plato='Platos',disponibilidad='Disponible'));self.assertEqual(r['id'],102);self.assertEqual(self.db.execute('SELECT precio_unitario FROM Detalle_Pedido').fetchone()[0],45000)
    def test_insumo_y_minimo(self):
        i=self.save('insumo',dict(nombre='Sal',unidad_medida='Kg',cantidad_minima='2'))['id'];self.save('minimo',dict(id_insumo=i,cantidad_minima='3'));self.assertEqual(tuple(self.db.execute('SELECT cantidad_disponible,cantidad_minima FROM Insumo WHERE id_insumo=?',(i,)).fetchone()),(0,3))
    def test_receta_abierta(self):
        with self.assertRaisesRegex(ErrorPedido,'pedidos abiertos'):self.save('receta',dict(num_serial=102,ingredientes=[]))
        self.assertEqual(self.db.execute('SELECT cantidad FROM Receta WHERE num_serial_producto=102').fetchone()[0],0.5)
    def test_receta_valida_y_rollback(self):
        self.save('receta',dict(num_serial=105,ingredientes=[dict(id_insumo=202,cantidad='0.20')]))
        self.db.executescript("CREATE TRIGGER falla BEFORE INSERT ON Receta BEGIN SELECT RAISE(ABORT,'fallo'); END;")
        with self.assertRaises(sqlite3.IntegrityError):self.save('receta',dict(num_serial=105,ingredientes=[dict(id_insumo=202,cantidad='0.30')]))
        self.assertEqual(self.db.execute('SELECT cantidad FROM Receta WHERE num_serial_producto=105').fetchone()[0],0.2)
    def test_otro_restaurante(self):
        with self.assertRaises(ErrorPedido):self.save('minimo',dict(id_insumo=999,cantidad_minima='4'))
    def test_desactivar(self):
        for i in (1,16):
            with self.assertRaises(ErrorPedido):self.save('estado-empleado',dict(id_empleado=i,activo=False))
    def test_empleado_roles(self):
        with patch('backend.gestion.clave',return_value='scrypt:simulado'):
            i=self.save('empleado',dict(nombre_empleado='Demo',cedula='3',usuario_software='demo',contrasena='no-se-registra',roles=['Cajero']))['id']
        self.save('roles-empleado',dict(id_empleado=i,roles=['Cocinero']));self.assertEqual(self.db.execute('SELECT COUNT(*) FROM Cajero').fetchone()[0],0)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM Cocinero').fetchone()[0],1)
        with self.assertRaises(ErrorPedido):self.save('roles-empleado',dict(id_empleado=1,roles=['Cocinero']))
        self.save('estado-empleado',dict(id_empleado=i,activo=False));self.assertEqual(self.db.execute('SELECT activo FROM Empleado WHERE id_empleado=?',(i,)).fetchone()[0],0)
    def test_validaciones(self):
        for v in ('-1','1.123',True,'NaN',1.2):
            with self.assertRaises(ErrorPedido):cantidad({'x':v},'x')
        with self.assertRaises(ErrorPedido):roles_validos(['DROP TABLE'])
        with self.assertRaises(ErrorPedido):self.save('roles-empleado',dict(id_empleado=16,roles=['Cajero']))
if __name__=='__main__':unittest.main()
