"""Pruebas sin modificar MariaDB: cálculo/SQL portable y API con mocks."""
import os
import sqlite3
import unittest
from unittest.mock import patch

from backend.catalogo import SQL_CATEGORIAS, consulta_productos, preparar_productos

NIT = '900123456-1'


class CatalogoTest(unittest.TestCase):
    def setUp(self):
        # SQLite se usa SOLO como doble de prueba de las consultas SELECT;
        # la aplicación sigue utilizando MariaDB y su esquema original.
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        self.addCleanup(self.db.close)
        self.db.executescript('''
            CREATE TABLE Producto(num_serial INT, NIT_restaurante TEXT,
                nombre TEXT, precio NUMERIC, disponibilidad TEXT, categoria_plato TEXT);
            CREATE TABLE Receta(num_serial_producto INT, id_insumo INT,
                NIT_restaurante TEXT, cantidad NUMERIC);
            CREATE TABLE Insumo(id_insumo INT, NIT_restaurante TEXT, cantidad_disponible NUMERIC);
            CREATE TABLE Pedido(num_pedido INT, NIT_restaurante TEXT, estado_pedido TEXT);
            CREATE TABLE Detalle_Pedido(num_pedido INT, num_serial_producto INT,
                NIT_restaurante TEXT, cantidad INT);
            CREATE TABLE Factura(num_pedido INT, NIT_restaurante TEXT);
            INSERT INTO Producto VALUES
                (1,'900123456-1','Plato A',45000,'Disponible','Comidas'),
                (2,'900123456-1','Plato B',8000,'Disponible','Bebidas'),
                (3,'900123456-1','Sin receta',25000,'Disponible','Comidas'),
                (4,'900123456-1','Deshabilitado',1000,'No Disponible','Comidas'),
                (5,'900123456-1','Receta invalida',1000,'Disponible','Comidas'),
                (1,'otro','Otro local',9,'Disponible','Otro');
            INSERT INTO Insumo VALUES (1,'900123456-1',15.5), (2,'900123456-1',5), (1,'otro',100);
            INSERT INTO Receta VALUES
                (1,1,'900123456-1',0.5), (1,2,'900123456-1',1),
                (2,1,'900123456-1',0.5), (4,1,'900123456-1',0.5),
                (5,1,'900123456-1',0), (1,1,'otro',1);
            INSERT INTO Pedido VALUES (1,'900123456-1','Tomado'),
                (2,'900123456-1','Preparacion'), (3,'900123456-1','Cancelado'),
                (4,'900123456-1','Cerrado'), (1,'otro','Tomado');
            INSERT INTO Detalle_Pedido VALUES (1,2,'900123456-1',2),
                (2,1,'900123456-1',100), (3,1,'900123456-1',100),
                (4,1,'900123456-1',100), (1,1,'otro',100);
            INSERT INTO Factura VALUES (2,'900123456-1'), (1,'otro');
        ''')

    def productos(self, categoria=None):
        sql, params = consulta_productos(NIT, categoria)
        filas = [dict(f) for f in self.db.execute(sql.replace('%s', '?'), params)]
        return {p['num_serial']: p for p in preparar_productos(filas)}

    def test_ingrediente_limitante(self):
        self.assertEqual(self.productos()[1]['max_unidades'], 5)
        self.assertEqual(self.productos()[1]['precio'], '45000.00')

    def test_reserva_compartida_y_exclusiones(self):
        # 15.5 kg - 2 * 0.5 kg = 14.5 kg; 29 unidades nuevas.
        self.assertEqual(self.productos()[2]['max_unidades'], 29)

    def test_sin_receta(self):
        self.assertEqual(self.productos()[3]['motivo_no_disponible'], 'SinReceta')
        self.assertFalse(self.productos()[3]['disponible'])

    def test_deshabilitado(self):
        self.assertEqual(self.productos()[4]['motivo_no_disponible'], 'ProductoDeshabilitado')

    def test_receta_invalida(self):
        self.assertEqual(self.productos()[5]['motivo_no_disponible'], 'RecetaInvalida')

    def test_stock_insuficiente(self):
        self.db.execute('UPDATE Insumo SET cantidad_disponible=0.25 WHERE id_insumo=2 AND NIT_restaurante=?', (NIT,))
        p = self.productos()[1]
        self.assertEqual(p['max_unidades'], 0)
        self.assertEqual(p['motivo_no_disponible'], 'StockInsuficiente')

    def test_filtro_y_aislamiento(self):
        self.assertEqual(set(self.productos('Bebidas')), {2})
        self.assertEqual(len(self.productos()), 5)
        self.assertEqual(self.productos("' OR 1=1 --"), {})
        self.assertEqual(self.productos('Otro'), {})

    def test_categorias(self):
        filas = self.db.execute(SQL_CATEGORIAS.replace('%s', '?'), (NIT,))
        self.assertEqual([f[0] for f in filas], ['Bebidas', 'Comidas'])


class SalonAPITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault('SECRET_KEY', 'clave-exclusiva-de-pruebas-automatizadas-123456')
        from app import app
        cls.app = app

    def setUp(self):
        self.client = self.app.test_client()
        self.empleado = dict(id_empleado=1, NIT_restaurante=NIT,
            nombre_empleado='Prueba', usuario_software='prueba', activo=1,
            estado_suscripcion_software='Activo', es_mesero=1, es_cocinero=0,
            es_cajero=0, es_administrador=0)
        p = patch('backend.auth.buscar_empleado', return_value=self.empleado)
        p.start()
        self.addCleanup(p.stop)
        q = patch('backend.salon.consultar', return_value=[])
        self.consultar = q.start()
        self.addCleanup(q.stop)

    def sesion(self):
        with self.client.session_transaction() as s:
            s['id_empleado'] = 1
            s['nit'] = NIT

    def test_sin_sesion(self):
        for ruta in ('mesas', 'categorias', 'productos'):
            self.assertEqual(self.client.get('/api/salon/' + ruta).status_code, 401)
        self.consultar.assert_not_called()

    def test_roles_no_autorizados(self):
        self.sesion()
        self.empleado['es_mesero'] = 0
        for rol in ('es_cocinero', 'es_cajero', 'es_administrador'):
            self.empleado[rol] = 1
            for ruta in ('mesas', 'categorias', 'productos'):
                self.assertEqual(self.client.get('/api/salon/' + ruta).status_code, 403)
            self.empleado[rol] = 0
        self.consultar.assert_not_called()

    def test_mesas_y_nit_de_sesion(self):
        self.sesion()
        self.consultar.return_value = [
            dict(num_mesa=1, activa=1, estado_mesa='Libre'),
            dict(num_mesa=2, activa=1, estado_mesa='Ocupada'),
            dict(num_mesa=3, activa=0, estado_mesa='Inactiva')]
        r = self.client.get('/api/salon/mesas?nit=otro')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json['resumen'], dict(libres=1, ocupadas=1, inactivas=1))
        self.assertEqual(self.consultar.call_args.args[1], (NIT,))

    def test_categorias(self):
        self.sesion()
        self.consultar.return_value = [dict(categoria_plato='Bebidas')]
        r = self.client.get('/api/salon/categorias')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json['categorias'], ['Bebidas'])

    def test_productos_y_filtro(self):
        self.sesion()
        r = self.client.get('/api/salon/productos?categoria=Bebidas')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json, dict(total=0, productos=[]))
        self.assertEqual(self.consultar.call_args.args[1], (NIT, NIT, 'Bebidas'))
        self.assertEqual(self.client.get('/api/salon/productos?categoria=').status_code, 400)

    def test_falla_bd(self):
        self.sesion()
        self.consultar.side_effect = RuntimeError('Fallo simulado')
        self.assertEqual(self.client.get('/api/salon/mesas').status_code, 503)


if __name__ == '__main__':
    unittest.main()
