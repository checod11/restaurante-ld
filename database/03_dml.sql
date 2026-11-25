-- DATOS SINTETICOS PARA INSTALACION ACADEMICA. No corresponden a ventas reales.
-- Datos originales de prueba; ejecutar una sola vez.
SET NAMES utf8mb4;
USE restaurante_pro_max;
START TRANSACTION;

-- 1. ENTIDADES FUERTES
INSERT INTO Restaurante (NIT, nombre_restaurante, correo, telefono, direccion, estado_suscripcion_software) VALUES
('900123456-1', 'Restaurante Mirador Bumangués', NULL, NULL, 'Floridablanca, Santander', 'Activo'),
('900123456-2', 'Pizzería La Cúspide', NULL, NULL, 'Bucaramanga, Santander', 'Activo'),
('900123456-3', 'Asadero El Fogón', NULL, NULL, 'Piedecuesta, Santander', 'Suspendido'),
('900123456-4', 'Cafetería Central UCC', NULL, NULL, 'Bucaramanga, Santander', 'Activo'),
('900123456-5', 'Heladería Bajo Cero', NULL, NULL, 'Girón, Santander', 'Activo');

INSERT INTO Proveedor (NIT_proveedor, nombre_empresa, telefono, correo) VALUES
('800999111-1', 'Carnes de Santander S.A.', NULL, NULL),
('800999111-2', 'Distribuidora Fruver', NULL, NULL),
('800999111-3', 'Lácteos El Toro', NULL, NULL),
('800999111-4', 'Bebidas del Oriente', NULL, NULL),
('800999111-5', 'Empaques y Plásticos', NULL, NULL);

-- 2. ENTIDADES DÉBILES DIRECTAS
-- Insertamos 20 empleados para el Mirador Bumangués ('900123456-1') para poder surtir los 4 subtipos
INSERT INTO Empleado (id_empleado, NIT_restaurante, nombre_empleado, cedula, telefono, correo, fecha_antiguedad, usuario_software, contraseña_software) VALUES
-- Destinados a Meseros (1-5)
(1, '900123456-1', 'Empleado DEMO 01', 'DEMO000001', NULL, NULL, '2025-01-15', 'cperez', 'hash123'),
(2, '900123456-1', 'Empleado DEMO 02', 'DEMO000002', NULL, NULL, '2025-02-10', 'mgomez', 'hash123'),
(3, '900123456-1', 'Empleado DEMO 03', 'DEMO000003', NULL, NULL, '2025-03-01', 'jtorres', 'hash123'),
(4, '900123456-1', 'Empleado DEMO 04', 'DEMO000004', NULL, NULL, '2025-04-20', 'arojas', 'hash123'),
(5, '900123456-1', 'Empleado DEMO 05', 'DEMO000005', NULL, NULL, '2025-05-05', 'lramirez', 'hash123'),
-- Destinados a Cocineros (6-10)
(6, '900123456-1', 'Empleado DEMO 06', 'DEMO000006', NULL, NULL, '2024-10-10', 'pchef', 'hash123'),
(7, '900123456-1', 'Empleado DEMO 07', 'DEMO000007', NULL, NULL, '2024-11-15', 'scocina', 'hash123'),
(8, '900123456-1', 'Empleado DEMO 08', 'DEMO000008', NULL, NULL, '2024-12-01', 'msabor', 'hash123'),
(9, '900123456-1', 'Empleado DEMO 09', 'DEMO000009', NULL, NULL, '2025-01-20', 'lguiso', 'hash123'),
(10, '900123456-1', 'Empleado DEMO 10', 'DEMO000010', NULL, NULL, '2025-02-25', 'dfuego', 'hash123'),
-- Destinados a Cajeros (11-15)
(11, '900123456-1', 'Empleado DEMO 11', 'DEMO000011', NULL, NULL, '2025-01-10', 'ccaja', 'hash123'),
(12, '900123456-1', 'Empleado DEMO 12', 'DEMO000012', NULL, NULL, '2025-02-15', 'apago', 'hash123'),
(13, '900123456-1', 'Empleado DEMO 13', 'DEMO000013', NULL, NULL, '2025-03-20', 'vcobro', 'hash123'),
(14, '900123456-1', 'Empleado DEMO 14', 'DEMO000014', NULL, NULL, '2025-04-05', 'dbilletes', 'hash123'),
(15, '900123456-1', 'Empleado DEMO 15', 'DEMO000015', NULL, NULL, '2025-05-10', 'smonedas', 'hash123'),
-- Destinados a Administradores (16-20)
(16, '900123456-1', 'Empleado DEMO 16', 'DEMO000016', NULL, NULL, '2024-01-01', 'rjefe', 'hash123'),
(17, '900123456-1', 'Empleado DEMO 17', 'DEMO000017', NULL, NULL, '2024-02-01', 'mgerente', 'hash123'),
(18, '900123456-1', 'Empleado DEMO 18', 'DEMO000018', NULL, NULL, '2024-03-01', 'fadmin', 'hash123'),
(19, '900123456-1', 'Empleado DEMO 19', 'DEMO000019', NULL, NULL, '2024-04-01', 'dcontrol', 'hash123'),
(20, '900123456-1', 'Empleado DEMO 20', 'DEMO000020', NULL, NULL, '2024-05-01', 'hsupervisor', 'hash123');

INSERT INTO Producto (num_serial, NIT_restaurante, nombre, precio, disponibilidad, categoria_plato) VALUES
(101, '900123456-1', 'Mute Santandereano', 25000.00, 'Disponible', 'Sopas'),
(102, '900123456-1', 'Cabrito al Horno', 45000.00, 'Disponible', 'Plato Principal'),
(103, '900123456-1', 'Pepitoria', 15000.00, 'Disponible', 'Acompañamiento'),
(104, '900123456-1', 'Arepa Amarilla', 5000.00, 'Disponible', 'Entradas'),
(105, '900123456-1', 'Limonada de Panela', 8000.00, 'Disponible', 'Bebidas');

INSERT INTO Insumo (id_insumo, NIT_restaurante, nombre, unidad_medida, cantidad_disponible, cantidad_minima) VALUES
(201, '900123456-1', 'Carne de Cabrito', 'Kg', 15.5, 5.0),
(202, '900123456-1', 'Maíz Pelado', 'Kg', 30.0, 10.0),
(203, '900123456-1', 'Panela', 'Und', 50.0, 15.0),
(204, '900123456-1', 'Limón', 'Kg', 10.0, 3.0),
(205, '900123456-1', 'Arroz', 'Kg', 40.0, 10.0);

-- 3. SUBTIPOS DE EMPLEADO
INSERT INTO Mesero (id_empleado, NIT_restaurante) VALUES (1, '900123456-1'), (2, '900123456-1'), (3, '900123456-1'), (4, '900123456-1'), (5, '900123456-1');
INSERT INTO Cocinero (id_empleado, NIT_restaurante) VALUES (6, '900123456-1'), (7, '900123456-1'), (8, '900123456-1'), (9, '900123456-1'), (10, '900123456-1');
INSERT INTO Cajero (id_empleado, NIT_restaurante) VALUES (11, '900123456-1'), (12, '900123456-1'), (13, '900123456-1'), (14, '900123456-1'), (15, '900123456-1');
INSERT INTO Administrador (id_empleado, NIT_restaurante) VALUES (16, '900123456-1'), (17, '900123456-1'), (18, '900123456-1'), (19, '900123456-1'), (20, '900123456-1');

-- 4. ENTIDADES TRANSACCIONALES
INSERT INTO Pedido (num_pedido, NIT_restaurante, id_mesero, num_mesa, fecha_hora_pedido, estado_pedido) VALUES
(301, '900123456-1', 1, 5, '2026-10-31 12:30:00', 'Entregado'),
(302, '900123456-1', 2, 8, '2026-10-31 13:00:00', 'Entregado'),
(303, '900123456-1', 3, 2, '2026-10-31 13:15:00', 'Preparacion'),
(304, '900123456-1', 4, 10, '2026-10-31 13:45:00', 'Tomado'),
(305, '900123456-1', 5, 1, '2026-10-31 14:00:00', 'Entregado');

INSERT INTO Factura (id_factura, NIT_restaurante, num_pedido, id_cajero, nombre_cliente, valor_total, subvalor_total, fecha_emision, metodo_pago, tipo_documento) VALUES
(401, '900123456-1', 301, 11, 'Consumidor Final', 70000.00, 60000.00, '2026-10-31 13:30:00', 'Efectivo', 'Factura POS'),
(402, '900123456-1', 302, 12, 'Consumidor Final', 50000.00, 42000.00, '2026-10-31 14:00:00', 'Tarjeta', 'Factura POS'),
(403, '900123456-1', 303, 13, 'Consumidor Final', 25000.00, 21000.00, '2026-10-31 14:30:00', 'Nequi', 'Factura POS'),
(404, '900123456-1', 304, 14, 'Consumidor Final', 15000.00, 12000.00, '2026-10-31 15:00:00', 'Efectivo', 'Factura POS'),
(405, '900123456-1', 305, 15, 'Consumidor Final', 58000.00, 49000.00, '2026-10-31 15:30:00', 'Tarjeta', 'Factura Electrónica');

INSERT INTO Orden_Compra (id_orden, NIT_restaurante, NIT_proveedor, direccion_llegada, fecha_llegada, fecha_orden) VALUES
(501, '900123456-1', '800999111-1', 'Bodega Principal', '2026-10-25', '2026-10-24'),
(502, '900123456-1', '800999111-2', 'Bodega Principal', '2026-10-26', '2026-10-25'),
(503, '900123456-1', '800999111-3', 'Refrigeradores Cocina', '2026-10-27', '2026-10-26'),
(504, '900123456-1', '800999111-4', 'Barra de bebidas', '2026-10-28', '2026-10-27'),
(505, '900123456-1', '800999111-5', 'Bodega Empaques', '2026-10-29', '2026-10-28');

-- 5. ENTIDADES ASOCIATIVAS
INSERT INTO Receta (num_serial_producto, id_insumo, NIT_restaurante, cantidad) VALUES
(102, 201, '900123456-1', 0.50), -- Cabrito al Horno requiere Carne de Cabrito
(104, 202, '900123456-1', 0.20), -- Arepa Amarilla requiere Maíz Pelado
(105, 203, '900123456-1', 1.00), -- Limonada requiere Panela
(105, 204, '900123456-1', 0.10), -- Limonada requiere Limón
(103, 205, '900123456-1', 0.30); -- Pepitoria requiere Arroz

INSERT INTO Detalle_Pedido (num_pedido, num_serial_producto, NIT_restaurante, cantidad) VALUES
(301, 101, '900123456-1', 2),
(302, 102, '900123456-1', 1),
(303, 105, '900123456-1', 4),
(304, 104, '900123456-1', 2),
(305, 103, '900123456-1', 1);

INSERT INTO Detalle_Orden_Compra (id_orden, id_insumo, NIT_restaurante, cantidad, precio_unitario) VALUES
(501, 201, '900123456-1', 10.0, 20000.00),
(502, 202, '900123456-1', 20.0, 2500.00),
(503, 203, '900123456-1', 50.0, 1500.00),
(504, 204, '900123456-1', 15.0, 3000.00),
(505, 205, '900123456-1', 30.0, 2000.00);
COMMIT;
