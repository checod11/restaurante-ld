-- Ejecutar como administrador después de 01, antes de 03.
SET NAMES utf8mb4;
SET SESSION default_storage_engine = InnoDB;

CREATE DATABASE audit_pro CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE audit_pro;

-- ============================================================================
-- PARTE 1: CREACIÓN DE LAS 15 TABLAS DE AUDITORÍA (1 POR CADA TABLA DEL PROYECTO)
-- ============================================================================

-- 1. Auditoría de Restaurante
CREATE TABLE IF NOT EXISTS audit_pro.auditoria_Restaurante (
    id_auditoria INT NOT NULL AUTO_INCREMENT,
    NIT VARCHAR(20) NOT NULL,
    operacion CHAR(3) NOT NULL,
    fecha_hora DATETIME NOT NULL,
    usuario_bd VARCHAR(100) NOT NULL,
    detalle_cambio VARCHAR(255),
    PRIMARY KEY (id_auditoria),
    CHECK (operacion = 'INS' OR operacion = 'UPD' OR operacion = 'DEL')
);

-- 2. Auditoría de Proveedor
CREATE TABLE IF NOT EXISTS audit_pro.auditoria_Proveedor (
    id_auditoria INT NOT NULL AUTO_INCREMENT,
    NIT_proveedor VARCHAR(20) NOT NULL,
    operacion CHAR(3) NOT NULL,
    fecha_hora DATETIME NOT NULL,
    usuario_bd VARCHAR(100) NOT NULL,
    detalle_cambio VARCHAR(255),
    PRIMARY KEY (id_auditoria),
    CHECK (operacion = 'INS' OR operacion = 'UPD' OR operacion = 'DEL')
);

-- 3. Auditoría de Empleado
CREATE TABLE IF NOT EXISTS audit_pro.auditoria_Empleado (
    id_auditoria INT NOT NULL AUTO_INCREMENT,
    id_empleado INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    operacion CHAR(3) NOT NULL,
    fecha_hora DATETIME NOT NULL,
    usuario_bd VARCHAR(100) NOT NULL,
    detalle_cambio VARCHAR(255),
    PRIMARY KEY (id_auditoria),
    CHECK (operacion = 'INS' OR operacion = 'UPD' OR operacion = 'DEL')
);

-- 4. Auditoría de Mesero
CREATE TABLE IF NOT EXISTS audit_pro.auditoria_Mesero (
    id_auditoria INT NOT NULL AUTO_INCREMENT,
    id_empleado INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    operacion CHAR(3) NOT NULL,
    fecha_hora DATETIME NOT NULL,
    usuario_bd VARCHAR(100) NOT NULL,
    detalle_cambio VARCHAR(255),
    PRIMARY KEY (id_auditoria),
    CHECK (operacion = 'INS' OR operacion = 'UPD' OR operacion = 'DEL')
);

-- 5. Auditoría de Cocinero
CREATE TABLE IF NOT EXISTS audit_pro.auditoria_Cocinero (
    id_auditoria INT NOT NULL AUTO_INCREMENT,
    id_empleado INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    operacion CHAR(3) NOT NULL,
    fecha_hora DATETIME NOT NULL,
    usuario_bd VARCHAR(100) NOT NULL,
    detalle_cambio VARCHAR(255),
    PRIMARY KEY (id_auditoria),
    CHECK (operacion = 'INS' OR operacion = 'UPD' OR operacion = 'DEL')
);

-- 6. Auditoría de Cajero
CREATE TABLE IF NOT EXISTS audit_pro.auditoria_Cajero (
    id_auditoria INT NOT NULL AUTO_INCREMENT,
    id_empleado INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    operacion CHAR(3) NOT NULL,
    fecha_hora DATETIME NOT NULL,
    usuario_bd VARCHAR(100) NOT NULL,
    detalle_cambio VARCHAR(255),
    PRIMARY KEY (id_auditoria),
    CHECK (operacion = 'INS' OR operacion = 'UPD' OR operacion = 'DEL')
);

-- 7. Auditoría de Administrador
CREATE TABLE IF NOT EXISTS audit_pro.auditoria_Administrador (
    id_auditoria INT NOT NULL AUTO_INCREMENT,
    id_empleado INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    operacion CHAR(3) NOT NULL,
    fecha_hora DATETIME NOT NULL,
    usuario_bd VARCHAR(100) NOT NULL,
    detalle_cambio VARCHAR(255),
    PRIMARY KEY (id_auditoria),
    CHECK (operacion = 'INS' OR operacion = 'UPD' OR operacion = 'DEL')
);

-- 8. Auditoría de Producto
CREATE TABLE IF NOT EXISTS audit_pro.auditoria_Producto (
    id_auditoria INT NOT NULL AUTO_INCREMENT,
    num_serial INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    operacion CHAR(3) NOT NULL,
    fecha_hora DATETIME NOT NULL,
    usuario_bd VARCHAR(100) NOT NULL,
    detalle_cambio VARCHAR(255),
    PRIMARY KEY (id_auditoria),
    CHECK (operacion = 'INS' OR operacion = 'UPD' OR operacion = 'DEL')
);

-- 9. Auditoría de Insumo
CREATE TABLE IF NOT EXISTS audit_pro.auditoria_Insumo (
    id_auditoria INT NOT NULL AUTO_INCREMENT,
    id_insumo INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    operacion CHAR(3) NOT NULL,
    fecha_hora DATETIME NOT NULL,
    usuario_bd VARCHAR(100) NOT NULL,
    detalle_cambio VARCHAR(255),
    PRIMARY KEY (id_auditoria),
    CHECK (operacion = 'INS' OR operacion = 'UPD' OR operacion = 'DEL')
);

-- 10. Auditoría de Pedido
CREATE TABLE IF NOT EXISTS audit_pro.auditoria_Pedido (
    id_auditoria INT NOT NULL AUTO_INCREMENT,
    num_pedido INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    operacion CHAR(3) NOT NULL,
    fecha_hora DATETIME NOT NULL,
    usuario_bd VARCHAR(100) NOT NULL,
    detalle_cambio VARCHAR(255),
    PRIMARY KEY (id_auditoria),
    CHECK (operacion = 'INS' OR operacion = 'UPD' OR operacion = 'DEL')
);

-- 11. Auditoría de Factura
CREATE TABLE IF NOT EXISTS audit_pro.auditoria_Factura (
    id_auditoria INT NOT NULL AUTO_INCREMENT,
    id_factura INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    operacion CHAR(3) NOT NULL,
    fecha_hora DATETIME NOT NULL,
    usuario_bd VARCHAR(100) NOT NULL,
    detalle_cambio VARCHAR(255),
    PRIMARY KEY (id_auditoria),
    CHECK (operacion = 'INS' OR operacion = 'UPD' OR operacion = 'DEL')
);

-- 12. Auditoría de Orden_Compra
CREATE TABLE IF NOT EXISTS audit_pro.auditoria_Orden_Compra (
    id_auditoria INT NOT NULL AUTO_INCREMENT,
    id_orden INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    operacion CHAR(3) NOT NULL,
    fecha_hora DATETIME NOT NULL,
    usuario_bd VARCHAR(100) NOT NULL,
    detalle_cambio VARCHAR(255),
    PRIMARY KEY (id_auditoria),
    CHECK (operacion = 'INS' OR operacion = 'UPD' OR operacion = 'DEL')
);

-- 13. Auditoría de Receta
CREATE TABLE IF NOT EXISTS audit_pro.auditoria_Receta (
    id_auditoria INT NOT NULL AUTO_INCREMENT,
    num_serial_producto INT NOT NULL,
    id_insumo INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    operacion CHAR(3) NOT NULL,
    fecha_hora DATETIME NOT NULL,
    usuario_bd VARCHAR(100) NOT NULL,
    detalle_cambio VARCHAR(255),
    PRIMARY KEY (id_auditoria),
    CHECK (operacion = 'INS' OR operacion = 'UPD' OR operacion = 'DEL')
);

-- 14. Auditoría de Detalle_Pedido
CREATE TABLE IF NOT EXISTS audit_pro.auditoria_Detalle_Pedido (
    id_auditoria INT NOT NULL AUTO_INCREMENT,
    num_pedido INT NOT NULL,
    num_serial_producto INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    operacion CHAR(3) NOT NULL,
    fecha_hora DATETIME NOT NULL,
    usuario_bd VARCHAR(100) NOT NULL,
    detalle_cambio VARCHAR(255),
    PRIMARY KEY (id_auditoria),
    CHECK (operacion = 'INS' OR operacion = 'UPD' OR operacion = 'DEL')
);

-- 15. Auditoría de Detalle_Orden_Compra
CREATE TABLE IF NOT EXISTS audit_pro.auditoria_Detalle_Orden_Compra (
    id_auditoria INT NOT NULL AUTO_INCREMENT,
    id_orden INT NOT NULL,
    id_insumo INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    operacion CHAR(3) NOT NULL,
    fecha_hora DATETIME NOT NULL,
    usuario_bd VARCHAR(100) NOT NULL,
    detalle_cambio VARCHAR(255),
    PRIMARY KEY (id_auditoria),
    CHECK (operacion = 'INS' OR operacion = 'UPD' OR operacion = 'DEL')
);


-- ============================================================================
-- PARTE 2: CREACIÓN DE DISPARADORES (INSERT, UPDATE Y DELETE POR CADA TABLA)
-- Base de datos origen: restaurante | Base de datos destino: audit
-- ============================================================================

DELIMITER //

-- ----------------------------------------------------------------------------
-- 1. TRIGGERS PARA TABLA: Restaurante
-- ----------------------------------------------------------------------------
CREATE TRIGGER restaurante_pro_max.tgr_ins_Restaurante
AFTER INSERT ON restaurante_pro_max.Restaurante
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Restaurante (NIT, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.NIT, 'INS', NOW(), USER(), CONCAT('Creado: ', NEW.nombre_restaurante, ' | Estado: ', NEW.estado_suscripcion_software));
END //

CREATE TRIGGER restaurante_pro_max.tgr_upd_Restaurante
AFTER UPDATE ON restaurante_pro_max.Restaurante
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Restaurante (NIT, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.NIT, 'UPD', NOW(), USER(), CONCAT('Nombre: ', OLD.nombre_restaurante, ' -> ', NEW.nombre_restaurante, ' | Estado: ', OLD.estado_suscripcion_software, ' -> ', NEW.estado_suscripcion_software));
END //

CREATE TRIGGER restaurante_pro_max.tgr_del_Restaurante
AFTER DELETE ON restaurante_pro_max.Restaurante
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Restaurante (NIT, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (OLD.NIT, 'DEL', NOW(), USER(), CONCAT('Eliminado: ', OLD.nombre_restaurante, ' | Estado: ', OLD.estado_suscripcion_software));
END //

-- ----------------------------------------------------------------------------
-- 2. TRIGGERS PARA TABLA: Proveedor
-- ----------------------------------------------------------------------------
CREATE TRIGGER restaurante_pro_max.tgr_ins_Proveedor
AFTER INSERT ON restaurante_pro_max.Proveedor
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Proveedor (NIT_proveedor, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.NIT_proveedor, 'INS', NOW(), USER(), CONCAT('Creado: ', NEW.nombre_empresa, ' | Tel: ', IFNULL(NEW.telefono, 'N/A')));
END //

CREATE TRIGGER restaurante_pro_max.tgr_upd_Proveedor
AFTER UPDATE ON restaurante_pro_max.Proveedor
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Proveedor (NIT_proveedor, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.NIT_proveedor, 'UPD', NOW(), USER(), CONCAT('Empresa: ', OLD.nombre_empresa, ' -> ', NEW.nombre_empresa));
END //

CREATE TRIGGER restaurante_pro_max.tgr_del_Proveedor
AFTER DELETE ON restaurante_pro_max.Proveedor
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Proveedor (NIT_proveedor, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (OLD.NIT_proveedor, 'DEL', NOW(), USER(), CONCAT('Eliminado: ', OLD.nombre_empresa));
END //

-- ----------------------------------------------------------------------------
-- 3. TRIGGERS PARA TABLA: Empleado
-- ----------------------------------------------------------------------------
CREATE TRIGGER restaurante_pro_max.tgr_ins_Empleado
AFTER INSERT ON restaurante_pro_max.Empleado
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Empleado (id_empleado, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.id_empleado, NEW.NIT_restaurante, 'INS', NOW(), USER(), CONCAT('Creado: ', NEW.nombre_empleado, ' | Cedula: ', NEW.cedula));
END //

CREATE TRIGGER restaurante_pro_max.tgr_upd_Empleado
AFTER UPDATE ON restaurante_pro_max.Empleado
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Empleado (id_empleado, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.id_empleado, NEW.NIT_restaurante, 'UPD', NOW(), USER(), CONCAT('Nombre: ', OLD.nombre_empleado, ' -> ', NEW.nombre_empleado, ' | User: ', IFNULL(NEW.usuario_software, 'N/A')));
END //

CREATE TRIGGER restaurante_pro_max.tgr_del_Empleado
AFTER DELETE ON restaurante_pro_max.Empleado
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Empleado (id_empleado, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (OLD.id_empleado, OLD.NIT_restaurante, 'DEL', NOW(), USER(), CONCAT('Eliminado: ', OLD.nombre_empleado, ' | Cedula: ', OLD.cedula));
END //

-- ----------------------------------------------------------------------------
-- 4. TRIGGERS PARA TABLA: Mesero
-- ----------------------------------------------------------------------------
CREATE TRIGGER restaurante_pro_max.tgr_ins_Mesero
AFTER INSERT ON restaurante_pro_max.Mesero
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Mesero (id_empleado, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.id_empleado, NEW.NIT_restaurante, 'INS', NOW(), USER(), CONCAT('Rol Mesero asignado a empleado ID: ', NEW.id_empleado));
END //

CREATE TRIGGER restaurante_pro_max.tgr_upd_Mesero
AFTER UPDATE ON restaurante_pro_max.Mesero
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Mesero (id_empleado, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.id_empleado, NEW.NIT_restaurante, 'UPD', NOW(), USER(), CONCAT('Rol Mesero actualizado ID: ', OLD.id_empleado, ' -> ', NEW.id_empleado));
END //

CREATE TRIGGER restaurante_pro_max.tgr_del_Mesero
AFTER DELETE ON restaurante_pro_max.Mesero
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Mesero (id_empleado, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (OLD.id_empleado, OLD.NIT_restaurante, 'DEL', NOW(), USER(), CONCAT('Rol Mesero eliminado de empleado ID: ', OLD.id_empleado));
END //

-- ----------------------------------------------------------------------------
-- 5. TRIGGERS PARA TABLA: Cocinero
-- ----------------------------------------------------------------------------
CREATE TRIGGER restaurante_pro_max.tgr_ins_Cocinero
AFTER INSERT ON restaurante_pro_max.Cocinero
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Cocinero (id_empleado, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.id_empleado, NEW.NIT_restaurante, 'INS', NOW(), USER(), CONCAT('Rol Cocinero asignado a empleado ID: ', NEW.id_empleado));
END //

CREATE TRIGGER restaurante_pro_max.tgr_upd_Cocinero
AFTER UPDATE ON restaurante_pro_max.Cocinero
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Cocinero (id_empleado, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.id_empleado, NEW.NIT_restaurante, 'UPD', NOW(), USER(), CONCAT('Rol Cocinero actualizado ID: ', OLD.id_empleado, ' -> ', NEW.id_empleado));
END //

CREATE TRIGGER restaurante_pro_max.tgr_del_Cocinero
AFTER DELETE ON restaurante_pro_max.Cocinero
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Cocinero (id_empleado, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (OLD.id_empleado, OLD.NIT_restaurante, 'DEL', NOW(), USER(), CONCAT('Rol Cocinero eliminado de empleado ID: ', OLD.id_empleado));
END //

-- ----------------------------------------------------------------------------
-- 6. TRIGGERS PARA TABLA: Cajero
-- ----------------------------------------------------------------------------
CREATE TRIGGER restaurante_pro_max.tgr_ins_Cajero
AFTER INSERT ON restaurante_pro_max.Cajero
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Cajero (id_empleado, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.id_empleado, NEW.NIT_restaurante, 'INS', NOW(), USER(), CONCAT('Rol Cajero asignado a empleado ID: ', NEW.id_empleado));
END //

CREATE TRIGGER restaurante_pro_max.tgr_upd_Cajero
AFTER UPDATE ON restaurante_pro_max.Cajero
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Cajero (id_empleado, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.id_empleado, NEW.NIT_restaurante, 'UPD', NOW(), USER(), CONCAT('Rol Cajero actualizado ID: ', OLD.id_empleado, ' -> ', NEW.id_empleado));
END //

CREATE TRIGGER restaurante_pro_max.tgr_del_Cajero
AFTER DELETE ON restaurante_pro_max.Cajero
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Cajero (id_empleado, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (OLD.id_empleado, OLD.NIT_restaurante, 'DEL', NOW(), USER(), CONCAT('Rol Cajero eliminado de empleado ID: ', OLD.id_empleado));
END //

-- ----------------------------------------------------------------------------
-- 7. TRIGGERS PARA TABLA: Administrador
-- ----------------------------------------------------------------------------
CREATE TRIGGER restaurante_pro_max.tgr_ins_Administrador
AFTER INSERT ON restaurante_pro_max.Administrador
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Administrador (id_empleado, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.id_empleado, NEW.NIT_restaurante, 'INS', NOW(), USER(), CONCAT('Rol Administrador asignado a empleado ID: ', NEW.id_empleado));
END //

CREATE TRIGGER restaurante_pro_max.tgr_upd_Administrador
AFTER UPDATE ON restaurante_pro_max.Administrador
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Administrador (id_empleado, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.id_empleado, NEW.NIT_restaurante, 'UPD', NOW(), USER(), CONCAT('Rol Administrador actualizado ID: ', OLD.id_empleado, ' -> ', NEW.id_empleado));
END //

CREATE TRIGGER restaurante_pro_max.tgr_del_Administrador
AFTER DELETE ON restaurante_pro_max.Administrador
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Administrador (id_empleado, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (OLD.id_empleado, OLD.NIT_restaurante, 'DEL', NOW(), USER(), CONCAT('Rol Administrador eliminado de empleado ID: ', OLD.id_empleado));
END //

-- ----------------------------------------------------------------------------
-- 8. TRIGGERS PARA TABLA: Producto
-- ----------------------------------------------------------------------------
CREATE TRIGGER restaurante_pro_max.tgr_ins_Producto
AFTER INSERT ON restaurante_pro_max.Producto
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Producto (num_serial, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.num_serial, NEW.NIT_restaurante, 'INS', NOW(), USER(), CONCAT('Creado: ', NEW.nombre, ' | Precio: ', NEW.precio, ' | Disp: ', NEW.disponibilidad));
END //

CREATE TRIGGER restaurante_pro_max.tgr_upd_Producto
AFTER UPDATE ON restaurante_pro_max.Producto
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Producto (num_serial, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.num_serial, NEW.NIT_restaurante, 'UPD', NOW(), USER(), CONCAT(NEW.nombre, ' | Precio: ', OLD.precio, ' -> ', NEW.precio, ' | Disp: ', OLD.disponibilidad, ' -> ', NEW.disponibilidad));
END //

CREATE TRIGGER restaurante_pro_max.tgr_del_Producto
AFTER DELETE ON restaurante_pro_max.Producto
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Producto (num_serial, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (OLD.num_serial, OLD.NIT_restaurante, 'DEL', NOW(), USER(), CONCAT('Eliminado: ', OLD.nombre, ' | Precio: ', OLD.precio));
END //

-- ----------------------------------------------------------------------------
-- 9. TRIGGERS PARA TABLA: Insumo
-- ----------------------------------------------------------------------------
CREATE TRIGGER restaurante_pro_max.tgr_ins_Insumo
AFTER INSERT ON restaurante_pro_max.Insumo
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Insumo (id_insumo, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.id_insumo, NEW.NIT_restaurante, 'INS', NOW(), USER(), CONCAT('Creado: ', NEW.nombre, ' | Stock: ', NEW.cantidad_disponible, ' ', NEW.unidad_medida));
END //

CREATE TRIGGER restaurante_pro_max.tgr_upd_Insumo
AFTER UPDATE ON restaurante_pro_max.Insumo
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Insumo (id_insumo, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.id_insumo, NEW.NIT_restaurante, 'UPD', NOW(), USER(), CONCAT(NEW.nombre, ' | Stock: ', OLD.cantidad_disponible, ' -> ', NEW.cantidad_disponible, ' ', NEW.unidad_medida));
END //

CREATE TRIGGER restaurante_pro_max.tgr_del_Insumo
AFTER DELETE ON restaurante_pro_max.Insumo
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Insumo (id_insumo, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (OLD.id_insumo, OLD.NIT_restaurante, 'DEL', NOW(), USER(), CONCAT('Eliminado: ', OLD.nombre, ' | Stock final: ', OLD.cantidad_disponible));
END //

-- ----------------------------------------------------------------------------
-- 10. TRIGGERS PARA TABLA: Pedido
-- ----------------------------------------------------------------------------
CREATE TRIGGER restaurante_pro_max.tgr_ins_Pedido
AFTER INSERT ON restaurante_pro_max.Pedido
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Pedido (num_pedido, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.num_pedido, NEW.NIT_restaurante, 'INS', NOW(), USER(), CONCAT('Mesa: ', NEW.num_mesa, ' | Mesero: ', NEW.id_mesero, ' | Estado: ', NEW.estado_pedido));
END //

CREATE TRIGGER restaurante_pro_max.tgr_upd_Pedido
AFTER UPDATE ON restaurante_pro_max.Pedido
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Pedido (num_pedido, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.num_pedido, NEW.NIT_restaurante, 'UPD', NOW(), USER(), CONCAT('Mesa: ', NEW.num_mesa, ' | Estado: ', OLD.estado_pedido, ' -> ', NEW.estado_pedido));
END //

CREATE TRIGGER restaurante_pro_max.tgr_del_Pedido
AFTER DELETE ON restaurante_pro_max.Pedido
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Pedido (num_pedido, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (OLD.num_pedido, OLD.NIT_restaurante, 'DEL', NOW(), USER(), CONCAT('Eliminado Mesa: ', OLD.num_mesa, ' | Estado: ', OLD.estado_pedido));
END //

-- ----------------------------------------------------------------------------
-- 11. TRIGGERS PARA TABLA: Factura
-- ----------------------------------------------------------------------------
CREATE TRIGGER restaurante_pro_max.tgr_ins_Factura
AFTER INSERT ON restaurante_pro_max.Factura
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Factura (id_factura, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.id_factura, NEW.NIT_restaurante, 'INS', NOW(), USER(), CONCAT('Pedido: ', NEW.num_pedido, ' | Total: ', NEW.valor_total, ' | Pago: ', NEW.metodo_pago));
END //

CREATE TRIGGER restaurante_pro_max.tgr_upd_Factura
AFTER UPDATE ON restaurante_pro_max.Factura
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Factura (id_factura, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.id_factura, NEW.NIT_restaurante, 'UPD', NOW(), USER(), CONCAT('Total: ', OLD.valor_total, ' -> ', NEW.valor_total, ' | Pago: ', OLD.metodo_pago, ' -> ', NEW.metodo_pago));
END //

CREATE TRIGGER restaurante_pro_max.tgr_del_Factura
AFTER DELETE ON restaurante_pro_max.Factura
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Factura (id_factura, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (OLD.id_factura, OLD.NIT_restaurante, 'DEL', NOW(), USER(), CONCAT('Eliminada Pedido: ', OLD.num_pedido, ' | Total: ', OLD.valor_total));
END //

-- ----------------------------------------------------------------------------
-- 12. TRIGGERS PARA TABLA: Orden_Compra
-- ----------------------------------------------------------------------------
CREATE TRIGGER restaurante_pro_max.tgr_ins_Orden_Compra
AFTER INSERT ON restaurante_pro_max.Orden_Compra
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Orden_Compra (id_orden, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.id_orden, NEW.NIT_restaurante, 'INS', NOW(), USER(), CONCAT('Proveedor: ', NEW.NIT_proveedor, ' | Fecha orden: ', NEW.fecha_orden));
END //

CREATE TRIGGER restaurante_pro_max.tgr_upd_Orden_Compra
AFTER UPDATE ON restaurante_pro_max.Orden_Compra
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Orden_Compra (id_orden, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.id_orden, NEW.NIT_restaurante, 'UPD', NOW(), USER(), CONCAT('Llegada: ', IFNULL(OLD.fecha_llegada, 'Pendiente'), ' -> ', IFNULL(NEW.fecha_llegada, 'Pendiente')));
END //

CREATE TRIGGER restaurante_pro_max.tgr_del_Orden_Compra
AFTER DELETE ON restaurante_pro_max.Orden_Compra
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Orden_Compra (id_orden, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (OLD.id_orden, OLD.NIT_restaurante, 'DEL', NOW(), USER(), CONCAT('Eliminada Proveedor: ', OLD.NIT_proveedor, ' | Fecha: ', OLD.fecha_orden));
END //

-- ----------------------------------------------------------------------------
-- 13. TRIGGERS PARA TABLA: Receta
-- ----------------------------------------------------------------------------
CREATE TRIGGER restaurante_pro_max.tgr_ins_Receta
AFTER INSERT ON restaurante_pro_max.Receta
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Receta (num_serial_producto, id_insumo, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.num_serial_producto, NEW.id_insumo, NEW.NIT_restaurante, 'INS', NOW(), USER(), CONCAT('Ingrediente agregado - Cantidad: ', NEW.cantidad));
END //

CREATE TRIGGER restaurante_pro_max.tgr_upd_Receta
AFTER UPDATE ON restaurante_pro_max.Receta
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Receta (num_serial_producto, id_insumo, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.num_serial_producto, NEW.id_insumo, NEW.NIT_restaurante, 'UPD', NOW(), USER(), CONCAT('Cantidad receta: ', OLD.cantidad, ' -> ', NEW.cantidad));
END //

CREATE TRIGGER restaurante_pro_max.tgr_del_Receta
AFTER DELETE ON restaurante_pro_max.Receta
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Receta (num_serial_producto, id_insumo, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (OLD.num_serial_producto, OLD.id_insumo, OLD.NIT_restaurante, 'DEL', NOW(), USER(), CONCAT('Ingrediente eliminado - Cantidad: ', OLD.cantidad));
END //

-- ----------------------------------------------------------------------------
-- 14. TRIGGERS PARA TABLA: Detalle_Pedido
-- ----------------------------------------------------------------------------
CREATE TRIGGER restaurante_pro_max.tgr_ins_Detalle_Pedido
AFTER INSERT ON restaurante_pro_max.Detalle_Pedido
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Detalle_Pedido (num_pedido, num_serial_producto, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.num_pedido, NEW.num_serial_producto, NEW.NIT_restaurante, 'INS', NOW(), USER(), CONCAT('Item agregado - Cantidad: ', NEW.cantidad));
END //

CREATE TRIGGER restaurante_pro_max.tgr_upd_Detalle_Pedido
AFTER UPDATE ON restaurante_pro_max.Detalle_Pedido
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Detalle_Pedido (num_pedido, num_serial_producto, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.num_pedido, NEW.num_serial_producto, NEW.NIT_restaurante, 'UPD', NOW(), USER(), CONCAT('Cantidad item: ', OLD.cantidad, ' -> ', NEW.cantidad));
END //

CREATE TRIGGER restaurante_pro_max.tgr_del_Detalle_Pedido
AFTER DELETE ON restaurante_pro_max.Detalle_Pedido
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Detalle_Pedido (num_pedido, num_serial_producto, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (OLD.num_pedido, OLD.num_serial_producto, OLD.NIT_restaurante, 'DEL', NOW(), USER(), CONCAT('Item eliminado - Cantidad: ', OLD.cantidad));
END //

-- ----------------------------------------------------------------------------
-- 15. TRIGGERS PARA TABLA: Detalle_Orden_Compra
-- ----------------------------------------------------------------------------
CREATE TRIGGER restaurante_pro_max.tgr_ins_Detalle_Orden_Compra
AFTER INSERT ON restaurante_pro_max.Detalle_Orden_Compra
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Detalle_Orden_Compra (id_orden, id_insumo, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.id_orden, NEW.id_insumo, NEW.NIT_restaurante, 'INS', NOW(), USER(), CONCAT('Cant: ', NEW.cantidad, ' | Precio unit: ', NEW.precio_unitario));
END //

CREATE TRIGGER restaurante_pro_max.tgr_upd_Detalle_Orden_Compra
AFTER UPDATE ON restaurante_pro_max.Detalle_Orden_Compra
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Detalle_Orden_Compra (id_orden, id_insumo, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.id_orden, NEW.id_insumo, NEW.NIT_restaurante, 'UPD', NOW(), USER(), CONCAT('Cant: ', OLD.cantidad, ' -> ', NEW.cantidad, ' | Precio: ', OLD.precio_unitario, ' -> ', NEW.precio_unitario));
END //

CREATE TRIGGER restaurante_pro_max.tgr_del_Detalle_Orden_Compra
AFTER DELETE ON restaurante_pro_max.Detalle_Orden_Compra
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Detalle_Orden_Compra (id_orden, id_insumo, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (OLD.id_orden, OLD.id_insumo, OLD.NIT_restaurante, 'DEL', NOW(), USER(), CONCAT('Eliminado Cant: ', OLD.cantidad, ' | Precio unit: ', OLD.precio_unitario));
END //

DELIMITER ;
