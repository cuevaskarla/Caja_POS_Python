USE Caja_Master_DB;
GO

-- ------------------------------------------------------------------------------
-- 1. TABLAS DE CACHÉ (Datos que bajan desde el CORE)
-- Control de sincronización vía 'Ultima_Actualizacion'
-- ------------------------------------------------------------------------------

-- Caché de usuarios autorizados para operar en esta sucursal específica
CREATE TABLE Usuarios_Locales (
    ID_Usuario INT PRIMARY KEY, -- ID entero, dictado por el CORE
    Nombre VARCHAR(150) NOT NULL, -- Match con Empleados.NombreCompleto del CORE
    Hash_Clave VARCHAR(255) NOT NULL, -- Match con Empleados.PasswordHash
    ID_Sucursal INT NOT NULL, -- Identificador de la sucursal donde corre esta BD
    Activo BIT DEFAULT 1,
    Ultima_Actualizacion DATETIME DEFAULT GETDATE() 
);

-- Caché del catálogo y stock asignado a la sucursal
CREATE TABLE Productos_Cache (
    ID_Producto INT PRIMARY KEY, -- ID entero, dictado por el CORE
    Nombre VARCHAR(150) NOT NULL, -- Match con Productos.Nombre del CORE
    Precio_Actual DECIMAL(12,2) NOT NULL, -- Match con Productos.PrecioBase del CORE
    Tasa_Impuesto DECIMAL(5,2) NOT NULL DEFAULT 0.18, -- Dato aplanado para evitar JOINs offline
    Stock_Local INT NOT NULL DEFAULT 0, -- Inventario disponible para esta sucursal
    Ultima_Actualizacion DATETIME DEFAULT GETDATE()
);

-- ------------------------------------------------------------------------------
-- 2. TABLAS TRANSACCIONALES (Datos creados en la Caja)
-- Control de sincronización vía 'Sincronizado BIT' y PKs UNIQUEIDENTIFIER
-- ------------------------------------------------------------------------------

-- Control de flujo de caja y cuadre diario
CREATE TABLE Turnos_Caja (
    ID_Turno UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(), -- UUID para evitar colisión en CORE
    ID_Usuario INT NOT NULL,
    ID_Sucursal INT NOT NULL, 
    Fecha_Apertura DATETIME NOT NULL DEFAULT GETDATE(),
    Monto_Inicial DECIMAL(12,2) NOT NULL,
    Fecha_Cierre DATETIME NULL,
    Monto_Calculado DECIMAL(12,2) NULL,
    Monto_Fisico DECIMAL(12,2) NULL,
    Estado VARCHAR(20) NOT NULL DEFAULT 'ABIERTO',
    Sincronizado BIT DEFAULT 0, -- 0 = Pendiente de subir al CORE

    CONSTRAINT FK_Turno_Usuario FOREIGN KEY (ID_Usuario) REFERENCES Usuarios_Locales(ID_Usuario),
    CONSTRAINT CHK_EstadoTurno CHECK (Estado IN ('ABIERTO', 'CERRADO'))
);

-- Entradas y salidas manuales de dinero durante el turno
CREATE TABLE Movimientos_Efectivo (
    ID_Movimiento UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    ID_Turno UNIQUEIDENTIFIER NOT NULL,
    Tipo_Movimiento VARCHAR(20) NOT NULL, 
    Monto DECIMAL(12,2) NOT NULL,
    Concepto VARCHAR(255) NOT NULL,
    Fecha_Hora DATETIME NOT NULL DEFAULT GETDATE(),
    Sincronizado BIT DEFAULT 0,

    CONSTRAINT FK_Movimiento_Turno FOREIGN KEY (ID_Turno) REFERENCES Turnos_Caja(ID_Turno),
    CONSTRAINT CHK_TipoMovimiento CHECK (Tipo_Movimiento IN ('ENTRADA', 'SALIDA'))
);

-- Cabecera de las ventas locales
CREATE TABLE Facturas_Locales (
    ID_Factura UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    ID_Turno UNIQUEIDENTIFIER NOT NULL,
    ID_Sucursal INT NOT NULL, 
    Fecha_Hora DATETIME NOT NULL DEFAULT GETDATE(),
    Subtotal DECIMAL(12,2) NOT NULL,
    Total_Impuestos DECIMAL(12,2) NOT NULL,
    Total_General DECIMAL(12,2) NOT NULL,
    Metodo_Pago VARCHAR(50) NOT NULL, 
    Sincronizado BIT DEFAULT 0,

    CONSTRAINT FK_Factura_Turno FOREIGN KEY (ID_Turno) REFERENCES Turnos_Caja(ID_Turno),
    CONSTRAINT CHK_MetodoPago CHECK (Metodo_Pago IN ('EFECTIVO', 'TARJETA', 'TRANSFERENCIA'))
);

-- Desglose de productos vendidos (Inmutabilidad histórica - 3NF)
CREATE TABLE Detalle_Facturas (
    ID_Detalle UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    ID_Factura UNIQUEIDENTIFIER NOT NULL,
    ID_Producto INT NOT NULL,
    Cantidad INT NOT NULL,
    Precio_Unitario DECIMAL(12,2) NOT NULL, -- Foto histórica del precio
    Monto_Impuesto DECIMAL(12,2) NOT NULL,  -- Foto histórica del impuesto
    Subtotal_Linea DECIMAL(12,2) NOT NULL,  -- (Cantidad * Precio_Unitario) + Monto_Impuesto

    CONSTRAINT FK_Detalle_Factura FOREIGN KEY (ID_Factura) REFERENCES Facturas_Locales(ID_Factura),
    CONSTRAINT FK_Detalle_Producto FOREIGN KEY (ID_Producto) REFERENCES Productos_Cache(ID_Producto),
    CONSTRAINT CHK_CantidadDetalle CHECK (Cantidad > 0)
);

-- ------------------------------------------------------------------------------
-- 3. TABLAS DE AUDITORÍA
-- ------------------------------------------------------------------------------

-- Trazabilidad de la operación de caja para resolución de descuadres
CREATE TABLE Logs_Caja (
    ID_Log UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    ID_Usuario INT NULL, 
    ID_Sucursal INT NOT NULL,
    Nivel VARCHAR(20) NOT NULL, 
    Accion VARCHAR(100) NOT NULL,
    Descripcion NVARCHAR(MAX) NOT NULL,
    Fecha_Hora DATETIME NOT NULL DEFAULT GETDATE(),
    Sincronizado BIT DEFAULT 0,

    CONSTRAINT FK_Log_Usuario FOREIGN KEY (ID_Usuario) REFERENCES Usuarios_Locales(ID_Usuario),
    CONSTRAINT CHK_NivelLog CHECK (Nivel IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL'))
);
GO