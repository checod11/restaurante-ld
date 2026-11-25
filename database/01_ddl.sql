-- Instalación nueva solamente. No elimina datos.
SET NAMES utf8mb4;
SET SESSION default_storage_engine = InnoDB;
CREATE DATABASE restaurante_pro_max CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE restaurante_pro_max;

-- 1. ENTIDADES FUERTES (Raíz y Externas)
CREATE TABLE Restaurante (
    NIT VARCHAR(20) NOT NULL,
    nombre_restaurante VARCHAR(100) NOT NULL,
    correo VARCHAR(100),
    telefono VARCHAR(20),
    direccion VARCHAR(150),
    estado_suscripcion_software VARCHAR(20) NOT NULL,
    PRIMARY KEY (NIT)
);

CREATE TABLE Proveedor (
    NIT_proveedor VARCHAR(20) NOT NULL,
    nombre_empresa VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    correo VARCHAR(100),
    PRIMARY KEY (NIT_proveedor)
);

-- 2. ENTIDADES DÉBILES DIRECTAS (Dependientes de Restaurante)
CREATE TABLE Empleado (
    id_empleado INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    nombre_empleado VARCHAR(100) NOT NULL,
    cedula VARCHAR(20) NOT NULL UNIQUE,
    telefono VARCHAR(20),
    correo VARCHAR(100),
    fecha_antiguedad DATE,
    usuario_software VARCHAR(50),
    contraseña_software VARCHAR(255),
    PRIMARY KEY (id_empleado, NIT_restaurante),
    FOREIGN KEY (NIT_restaurante) REFERENCES Restaurante(NIT) ON DELETE CASCADE
);

CREATE TABLE Producto (
    num_serial INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    precio DECIMAL(10,2) NOT NULL,
    disponibilidad VARCHAR(20) NOT NULL,
    categoria_plato VARCHAR(50),
    PRIMARY KEY (num_serial, NIT_restaurante),
    FOREIGN KEY (NIT_restaurante) REFERENCES Restaurante(NIT) ON DELETE CASCADE
);

CREATE TABLE Insumo (
    id_insumo INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    unidad_medida VARCHAR(20) NOT NULL,
    cantidad_disponible DECIMAL(10,2) NOT NULL,
    cantidad_minima DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (id_insumo, NIT_restaurante),
    FOREIGN KEY (NIT_restaurante) REFERENCES Restaurante(NIT) ON DELETE CASCADE
);

-- 3. SUBTIPOS DE EMPLEADO (Herencia parcial y superpuesta)
CREATE TABLE Mesero (
    id_empleado INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    PRIMARY KEY (id_empleado, NIT_restaurante),
    FOREIGN KEY (id_empleado, NIT_restaurante) REFERENCES Empleado(id_empleado, NIT_restaurante) ON DELETE CASCADE
);

CREATE TABLE Cocinero (
    id_empleado INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    PRIMARY KEY (id_empleado, NIT_restaurante),
    FOREIGN KEY (id_empleado, NIT_restaurante) REFERENCES Empleado(id_empleado, NIT_restaurante) ON DELETE CASCADE
);

CREATE TABLE Cajero (
    id_empleado INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    PRIMARY KEY (id_empleado, NIT_restaurante),
    FOREIGN KEY (id_empleado, NIT_restaurante) REFERENCES Empleado(id_empleado, NIT_restaurante) ON DELETE CASCADE
);

CREATE TABLE Administrador (
    id_empleado INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    PRIMARY KEY (id_empleado, NIT_restaurante),
    FOREIGN KEY (id_empleado, NIT_restaurante) REFERENCES Empleado(id_empleado, NIT_restaurante) ON DELETE CASCADE
);

-- 4. ENTIDADES TRANSACCIONALES DÉBILES
CREATE TABLE Pedido (
    num_pedido INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    id_mesero INT NOT NULL, -- FK a Mesero
    num_mesa INT NOT NULL,
    fecha_hora_pedido DATETIME NOT NULL,
    estado_pedido VARCHAR(20) NOT NULL,
    PRIMARY KEY (num_pedido, NIT_restaurante),
    FOREIGN KEY (NIT_restaurante) REFERENCES Restaurante(NIT) ON DELETE CASCADE,
    FOREIGN KEY (id_mesero, NIT_restaurante) REFERENCES Mesero(id_empleado, NIT_restaurante)
);

CREATE TABLE Factura (
    id_factura INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    num_pedido INT NOT NULL, -- FK a Pedido (Relación 1:1)
    id_cajero INT NOT NULL,  -- FK a Cajero
    nombre_cliente VARCHAR(100),
    valor_total DECIMAL(12,2) NOT NULL,
    subvalor_total DECIMAL(12,2) NOT NULL,
    fecha_emision DATETIME NOT NULL,
    metodo_pago VARCHAR(50) NOT NULL,
    tipo_documento VARCHAR(50) NOT NULL,
    PRIMARY KEY (id_factura, NIT_restaurante),
    UNIQUE (num_pedido, NIT_restaurante), -- Garantiza la relación 1:1 con Pedido
    FOREIGN KEY (NIT_restaurante) REFERENCES Restaurante(NIT) ON DELETE CASCADE,
    FOREIGN KEY (num_pedido, NIT_restaurante) REFERENCES Pedido(num_pedido, NIT_restaurante),
    FOREIGN KEY (id_cajero, NIT_restaurante) REFERENCES Cajero(id_empleado, NIT_restaurante)
);

CREATE TABLE Orden_Compra (
    id_orden INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    NIT_proveedor VARCHAR(20) NOT NULL,
    direccion_llegada VARCHAR(150),
    fecha_llegada DATE,
    fecha_orden DATE NOT NULL,
    PRIMARY KEY (id_orden, NIT_restaurante),
    FOREIGN KEY (NIT_restaurante) REFERENCES Restaurante(NIT) ON DELETE CASCADE,
    FOREIGN KEY (NIT_proveedor) REFERENCES Proveedor(NIT_proveedor)
);

-- 5. ENTIDADES ASOCIATIVAS (Resolución de N:M)
CREATE TABLE Receta (
    num_serial_producto INT NOT NULL,
    id_insumo INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    cantidad DECIMAL(10,2) NOT NULL,
    PRIMARY KEY (num_serial_producto, id_insumo, NIT_restaurante),
    FOREIGN KEY (num_serial_producto, NIT_restaurante) REFERENCES Producto(num_serial, NIT_restaurante) ON DELETE CASCADE,
    FOREIGN KEY (id_insumo, NIT_restaurante) REFERENCES Insumo(id_insumo, NIT_restaurante) ON DELETE CASCADE
);

CREATE TABLE Detalle_Pedido (
    num_pedido INT NOT NULL,
    num_serial_producto INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    cantidad INT NOT NULL,
    PRIMARY KEY (num_pedido, num_serial_producto, NIT_restaurante),
    FOREIGN KEY (num_pedido, NIT_restaurante) REFERENCES Pedido(num_pedido, NIT_restaurante) ON DELETE CASCADE,
    FOREIGN KEY (num_serial_producto, NIT_restaurante) REFERENCES Producto(num_serial, NIT_restaurante)
);

CREATE TABLE Detalle_Orden_Compra (
    id_orden INT NOT NULL,
    id_insumo INT NOT NULL,
    NIT_restaurante VARCHAR(20) NOT NULL,
    cantidad DECIMAL(10,2) NOT NULL,
    precio_unitario DECIMAL(12,2) NOT NULL,
    PRIMARY KEY (id_orden, id_insumo, NIT_restaurante),
    FOREIGN KEY (id_orden, NIT_restaurante) REFERENCES Orden_Compra(id_orden, NIT_restaurante) ON DELETE CASCADE,
    FOREIGN KEY (id_insumo, NIT_restaurante) REFERENCES Insumo(id_insumo, NIT_restaurante)
);
