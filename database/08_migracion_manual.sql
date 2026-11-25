-- Fase 1 v2: migración de ampliación, MariaDB 10.11+.
-- Ejecutar UNA SOLA VEZ como administrador, tras respaldo, sobre la estructura v1 completa.
-- DDL realiza commits implícitos; si ocurre un error, detenerse y revisar antes de continuar.
-- No elimina registros ni sustituye los identificadores originales.
SET NAMES utf8mb4;
USE restaurante_pro_max;
SELECT CHARACTER_SET_NAME, COLLATION_NAME INTO @nit_charset, @nit_collation
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='Restaurante' AND COLUMN_NAME='NIT';

SET @ddl = CONCAT('CREATE TABLE Mesa (
    num_mesa INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (num_mesa, NIT_restaurante),
    CONSTRAINT fk_mesa_restaurante FOREIGN KEY (NIT_restaurante) REFERENCES Restaurante(NIT),
    CONSTRAINT chk_mesa_activa CHECK (activa IN (0,1))
) ENGINE=InnoDB DEFAULT CHARACTER SET ', @nit_charset, ' COLLATE ', @nit_collation);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @ddl = CONCAT('CREATE TABLE Movimiento_Inventario (
    id_movimiento BIGINT NOT NULL AUTO_INCREMENT,
    NIT_restaurante VARCHAR(20) NOT NULL,
    id_insumo INT NOT NULL,
    id_empleado INT NOT NULL,
    id_factura INT NULL,
    tipo ENUM(''Entrada'',''Salida'',''AjusteEntrada'',''AjusteSalida'') NOT NULL,
    cantidad DECIMAL(10,2) NOT NULL,
    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    motivo VARCHAR(150) NULL,
    PRIMARY KEY (id_movimiento),
    UNIQUE KEY uq_movimiento_factura_insumo (id_factura, id_insumo, NIT_restaurante),
    CONSTRAINT fk_mov_insumo FOREIGN KEY (id_insumo,NIT_restaurante) REFERENCES Insumo(id_insumo,NIT_restaurante),
    CONSTRAINT fk_mov_empleado FOREIGN KEY (id_empleado,NIT_restaurante) REFERENCES Empleado(id_empleado,NIT_restaurante),
    CONSTRAINT fk_mov_factura FOREIGN KEY (id_factura,NIT_restaurante) REFERENCES Factura(id_factura,NIT_restaurante),
    CONSTRAINT chk_mov_cantidad CHECK (cantidad > 0),
    CONSTRAINT chk_mov_factura CHECK (id_factura IS NULL OR tipo = ''Salida'')
) ENGINE=InnoDB DEFAULT CHARACTER SET ', @nit_charset, ' COLLATE ', @nit_collation);
PREPARE stmt FROM @ddl;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

ALTER TABLE Empleado
    ADD COLUMN activo BOOLEAN NOT NULL DEFAULT TRUE,
    ADD CONSTRAINT chk_empleado_activo CHECK (activo IN (0,1));
-- Los empleados existentes quedan activos por defecto: no se dispone de estados históricos.
-- No se modifica hash123: se sustituirá por hashes seguros en la Fase 2.

ALTER TABLE Pedido
    ADD COLUMN id_cocinero INT NULL,
    ADD COLUMN fecha_inicio_preparacion DATETIME NULL,
    ADD COLUMN fecha_lista DATETIME NULL,
    ADD COLUMN fecha_entrega DATETIME NULL,
    ADD CONSTRAINT fk_pedido_cocinero FOREIGN KEY (id_cocinero,NIT_restaurante)
        REFERENCES Cocinero(id_empleado,NIT_restaurante);

ALTER TABLE Detalle_Pedido
    ADD COLUMN nota_especial VARCHAR(255) NULL,
    ADD COLUMN precio_unitario DECIMAL(10,2) NULL;
-- No se asignan precios históricos con los precios actuales del catálogo.

ALTER TABLE Factura
    ADD COLUMN documento_cliente VARCHAR(30) NULL,
    ADD COLUMN correo_cliente VARCHAR(100) NULL,
    ADD COLUMN cufe VARCHAR(128) NULL,
    ADD COLUMN estado_validacion VARCHAR(25) NULL,
    ADD COLUMN referencia_proveedor VARCHAR(150) NULL,
    ADD COLUMN monto_recibido DECIMAL(12,2) NULL;
-- NULL en registros antiguos significa información no disponible, no una validación fiscal.

-- Crear el modelo de auditoría de las dos tablas nuevas antes de poblar mesas.
CREATE TABLE audit_pro.auditoria_Mesa (
    id_auditoria BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    num_mesa INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    operacion CHAR(3) NOT NULL,
    fecha_hora DATETIME NOT NULL,
    usuario_bd VARCHAR(100) NOT NULL,
    detalle_cambio VARCHAR(255),
    CHECK (operacion IN ('INS','UPD','DEL'))
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4;

CREATE TABLE audit_pro.auditoria_Movimiento_Inventario (
    id_auditoria BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    id_movimiento BIGINT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    operacion CHAR(3) NOT NULL,
    fecha_hora DATETIME NOT NULL,
    usuario_bd VARCHAR(100) NOT NULL,
    detalle_cambio VARCHAR(255),
    CHECK (operacion IN ('INS','UPD','DEL'))
) ENGINE=InnoDB DEFAULT CHARACTER SET utf8mb4;

DELIMITER //
CREATE TRIGGER restaurante_pro_max.tgr_ins_Mesa
AFTER INSERT ON restaurante_pro_max.Mesa
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Mesa (num_mesa, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.num_mesa, NEW.NIT_restaurante, 'INS', NOW(), USER(), LEFT(CONCAT('activa: ', COALESCE(CAST(NEW.activa AS CHAR),'NULL'), ' | '),255));
END //

CREATE TRIGGER restaurante_pro_max.tgr_upd_Mesa
AFTER UPDATE ON restaurante_pro_max.Mesa
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Mesa (num_mesa, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.num_mesa, NEW.NIT_restaurante, 'UPD', NOW(), USER(), LEFT(CONCAT('activa: ', COALESCE(CAST(OLD.activa AS CHAR),'NULL'), ' -> ', COALESCE(CAST(NEW.activa AS CHAR),'NULL'), ' | '),255));
END //

CREATE TRIGGER restaurante_pro_max.tgr_del_Mesa
AFTER DELETE ON restaurante_pro_max.Mesa
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Mesa (num_mesa, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (OLD.num_mesa, OLD.NIT_restaurante, 'DEL', NOW(), USER(), LEFT(CONCAT('activa: ', COALESCE(CAST(OLD.activa AS CHAR),'NULL'), ' | '),255));
END //

CREATE TRIGGER restaurante_pro_max.tgr_ins_Movimiento_Inventario
AFTER INSERT ON restaurante_pro_max.Movimiento_Inventario
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Movimiento_Inventario (id_movimiento, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.id_movimiento, NEW.NIT_restaurante, 'INS', NOW(), USER(), LEFT(CONCAT('id_insumo: ', COALESCE(CAST(NEW.id_insumo AS CHAR),'NULL'), ' | ', 'id_empleado: ', COALESCE(CAST(NEW.id_empleado AS CHAR),'NULL'), ' | ', 'id_factura: ', COALESCE(CAST(NEW.id_factura AS CHAR),'NULL'), ' | ', 'tipo: ', COALESCE(CAST(NEW.tipo AS CHAR),'NULL'), ' | ', 'cantidad: ', COALESCE(CAST(NEW.cantidad AS CHAR),'NULL'), ' | ', 'fecha_hora: ', COALESCE(CAST(NEW.fecha_hora AS CHAR),'NULL'), ' | '),255));
END //

CREATE TRIGGER restaurante_pro_max.tgr_upd_Movimiento_Inventario
AFTER UPDATE ON restaurante_pro_max.Movimiento_Inventario
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Movimiento_Inventario (id_movimiento, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.id_movimiento, NEW.NIT_restaurante, 'UPD', NOW(), USER(), LEFT(CONCAT('id_insumo: ', COALESCE(CAST(OLD.id_insumo AS CHAR),'NULL'), ' -> ', COALESCE(CAST(NEW.id_insumo AS CHAR),'NULL'), ' | ', 'id_empleado: ', COALESCE(CAST(OLD.id_empleado AS CHAR),'NULL'), ' -> ', COALESCE(CAST(NEW.id_empleado AS CHAR),'NULL'), ' | ', 'id_factura: ', COALESCE(CAST(OLD.id_factura AS CHAR),'NULL'), ' -> ', COALESCE(CAST(NEW.id_factura AS CHAR),'NULL'), ' | ', 'tipo: ', COALESCE(CAST(OLD.tipo AS CHAR),'NULL'), ' -> ', COALESCE(CAST(NEW.tipo AS CHAR),'NULL'), ' | ', 'cantidad: ', COALESCE(CAST(OLD.cantidad AS CHAR),'NULL'), ' -> ', COALESCE(CAST(NEW.cantidad AS CHAR),'NULL'), ' | ', 'fecha_hora: ', COALESCE(CAST(OLD.fecha_hora AS CHAR),'NULL'), ' -> ', COALESCE(CAST(NEW.fecha_hora AS CHAR),'NULL'), ' | '),255));
END //

CREATE TRIGGER restaurante_pro_max.tgr_del_Movimiento_Inventario
AFTER DELETE ON restaurante_pro_max.Movimiento_Inventario
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Movimiento_Inventario (id_movimiento, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (OLD.id_movimiento, OLD.NIT_restaurante, 'DEL', NOW(), USER(), LEFT(CONCAT('id_insumo: ', COALESCE(CAST(OLD.id_insumo AS CHAR),'NULL'), ' | ', 'id_empleado: ', COALESCE(CAST(OLD.id_empleado AS CHAR),'NULL'), ' | ', 'id_factura: ', COALESCE(CAST(OLD.id_factura AS CHAR),'NULL'), ' | ', 'tipo: ', COALESCE(CAST(OLD.tipo AS CHAR),'NULL'), ' | ', 'cantidad: ', COALESCE(CAST(OLD.cantidad AS CHAR),'NULL'), ' | ', 'fecha_hora: ', COALESCE(CAST(OLD.fecha_hora AS CHAR),'NULL'), ' | '),255));
END //

DELIMITER ;

-- Recuperar todas las mesas conocidas a partir de pedidos históricos, sin inventar capacidad.
INSERT INTO Mesa (num_mesa,NIT_restaurante)
SELECT DISTINCT num_mesa,NIT_restaurante FROM Pedido;
ALTER TABLE Pedido ADD CONSTRAINT fk_pedido_mesa FOREIGN KEY (num_mesa,NIT_restaurante)
    REFERENCES Mesa(num_mesa,NIT_restaurante);

-- La ocupación se calcula, no se duplica como atributo mutable.
-- Una factura existente tiene prioridad sobre estados antiguos inconsistentes.
CREATE OR REPLACE SQL SECURITY INVOKER VIEW v_estado_mesas AS
SELECT m.NIT_restaurante, m.num_mesa, m.activa,
    CASE WHEN m.activa=0 THEN 'Inactiva'
         WHEN EXISTS (
           SELECT 1 FROM Pedido p
           WHERE p.num_mesa=m.num_mesa AND p.NIT_restaurante=m.NIT_restaurante
             AND p.estado_pedido NOT IN ('Cancelado','Cerrado')
             AND NOT EXISTS (SELECT 1 FROM Factura f WHERE f.num_pedido=p.num_pedido AND f.NIT_restaurante=p.NIT_restaurante)
         ) THEN 'Ocupada' ELSE 'Libre' END AS estado_mesa
FROM Mesa m;

-- No hay descuento automático aún: se implementará en una transacción del backend.
-- Las tablas originales de auditoría registran operaciones; sus textos no son un historial completo de cada columna.

-- Actualizar el resumen de auditoría UPDATE de las tablas ampliadas; no guardar claves ni notas personales.
DELIMITER //
CREATE OR REPLACE TRIGGER restaurante_pro_max.tgr_upd_Empleado
AFTER UPDATE ON restaurante_pro_max.Empleado
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Empleado (id_empleado, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.id_empleado, NEW.NIT_restaurante, 'UPD', NOW(), USER(), LEFT(CONCAT('Empleado ID: ', NEW.id_empleado, ' | Nombre modificado: ', NOT (OLD.nombre_empleado <=> NEW.nombre_empleado), ' | Activo: ', OLD.activo, ' -> ', NEW.activo, ' | Usuario modificado: ', NOT (OLD.usuario_software <=> NEW.usuario_software), ' | Credencial modificada: ', NOT (OLD.`contraseña_software` <=> NEW.`contraseña_software`)),255));
END //

CREATE OR REPLACE TRIGGER restaurante_pro_max.tgr_upd_Pedido
AFTER UPDATE ON restaurante_pro_max.Pedido
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Pedido (num_pedido, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.num_pedido, NEW.NIT_restaurante, 'UPD', NOW(), USER(), LEFT(CONCAT('Mesa: ', NEW.num_mesa, ' | Estado: ', OLD.estado_pedido, ' -> ', NEW.estado_pedido, ' | Cocinero: ', COALESCE(NEW.id_cocinero,0), ' | Tiempos modificados: ', NOT (OLD.fecha_inicio_preparacion <=> NEW.fecha_inicio_preparacion) OR NOT (OLD.fecha_lista <=> NEW.fecha_lista) OR NOT (OLD.fecha_entrega <=> NEW.fecha_entrega)),255));
END //

CREATE OR REPLACE TRIGGER restaurante_pro_max.tgr_upd_Detalle_Pedido
AFTER UPDATE ON restaurante_pro_max.Detalle_Pedido
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Detalle_Pedido (num_pedido, num_serial_producto, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.num_pedido, NEW.num_serial_producto, NEW.NIT_restaurante, 'UPD', NOW(), USER(), LEFT(CONCAT('Cantidad: ', OLD.cantidad, ' -> ', NEW.cantidad, ' | Precio: ', COALESCE(CAST(OLD.precio_unitario AS CHAR),'NULL'), ' -> ', COALESCE(CAST(NEW.precio_unitario AS CHAR),'NULL'), ' | Nota modificada: ', NOT (OLD.nota_especial <=> NEW.nota_especial)),255));
END //

CREATE OR REPLACE TRIGGER restaurante_pro_max.tgr_upd_Factura
AFTER UPDATE ON restaurante_pro_max.Factura
FOR EACH ROW
BEGIN
    INSERT INTO audit_pro.auditoria_Factura (id_factura, NIT_restaurante, operacion, fecha_hora, usuario_bd, detalle_cambio)
    VALUES (NEW.id_factura, NEW.NIT_restaurante, 'UPD', NOW(), USER(), LEFT(CONCAT('Total: ', OLD.valor_total, ' -> ', NEW.valor_total, ' | Pago: ', OLD.metodo_pago, ' -> ', NEW.metodo_pago, ' | Estado fiscal: ', COALESCE(NEW.estado_validacion,'Sin dato'), ' | Datos fiscales modificados: ', NOT (OLD.documento_cliente <=> NEW.documento_cliente) OR NOT (OLD.correo_cliente <=> NEW.correo_cliente) OR NOT (OLD.cufe <=> NEW.cufe) OR NOT (OLD.referencia_proveedor <=> NEW.referencia_proveedor)),255));
END //

DELIMITER ;
