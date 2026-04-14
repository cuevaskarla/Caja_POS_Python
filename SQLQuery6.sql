USE Caja_Master_DB;
GO

-- 1. DESACTIVAR TODAS LAS RESTRICCIONES DE LLAVE FORANEA
DECLARE @sql NVARCHAR(MAX) = '';
SELECT @sql += 'ALTER TABLE ' + QUOTENAME(SCHEMA_NAME(schema_id)) + '.' + QUOTENAME(OBJECT_NAME(parent_object_id)) + 
               ' DROP CONSTRAINT ' + QUOTENAME(name) + ';'
FROM sys.foreign_keys;
EXEC sp_executesql @sql;
GO

-- 2. BORRAR TABLAS SI EXISTEN
IF OBJECT_ID('dbo.Facturas_Locales', 'U') IS NOT NULL DROP TABLE dbo.Facturas_Locales;
IF OBJECT_ID('dbo.Turnos_Caja', 'U') IS NOT NULL DROP TABLE dbo.Turnos_Caja;
IF OBJECT_ID('dbo.Productos_Cache', 'U') IS NOT NULL DROP TABLE dbo.Productos_Cache;
IF OBJECT_ID('dbo.Usuarios_Locales', 'U') IS NOT NULL DROP TABLE dbo.Usuarios_Locales;
GO

-- 3. CREAR TABLAS CON NOMBRES EXACTOS PARA EL CODIGO
CREATE TABLE Usuarios_Locales (
    ID_Usuario INT PRIMARY KEY,
    Nombre NVARCHAR(150),
    Hash_Clave NVARCHAR(255),
    ID_Sucursal INT,
    Activo BIT DEFAULT 1
);

CREATE TABLE Productos_Cache (
    ID_Producto INT PRIMARY KEY,
    Nombre NVARCHAR(150),
    Precio_Actual DECIMAL(12, 2),
    Tasa_Impuesto DECIMAL(5, 2) DEFAULT 0.18,
    Stock_Local INT
);

CREATE TABLE Turnos_Caja (
    ID_Turno NVARCHAR(50) PRIMARY KEY,
    ID_Empleado INT NOT NULL,
    Monto_Apertura DECIMAL(12, 2) NOT NULL,
    Fecha_Apertura DATETIME DEFAULT GETDATE(),
    Estado NVARCHAR(10) DEFAULT 'ABIERTO'
);

CREATE TABLE Facturas_Locales (
    ID_Factura NVARCHAR(50) PRIMARY KEY,
    NCF NVARCHAR(20),
    RNC_Cliente NVARCHAR(15),
    Fecha DATETIME DEFAULT GETDATE(),
    Total_ITBIS DECIMAL(12, 2),
    Total_Factura DECIMAL(12, 2),
    ID_Empleado INT,
    ID_Turno NVARCHAR(50) REFERENCES Turnos_Caja(ID_Turno)
);
GO

-- 4. INSERTAR DATA DE PRUEBA MINIMA
INSERT INTO Usuarios_Locales (ID_Usuario, Nombre, Hash_Clave, ID_Sucursal) VALUES (101, 'Saul', '1234', 1);
INSERT INTO Productos_Cache (ID_Producto, Nombre, Precio_Actual, Stock_Local) VALUES (1, 'Presidente Grande', 250.00, 50);
GO