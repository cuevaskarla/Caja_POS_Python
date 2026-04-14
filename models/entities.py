from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey
from db.connection import Base
import datetime
import uuid

class UsuarioLocal(Base):
    __tablename__ = "Usuarios_Locales"
    id_usuario = Column("ID_Usuario", Integer, primary_key=True)
    nombre = Column("Nombre", String(150), nullable=False)
    hash_clave = Column("Hash_Clave", String(255), nullable=False)
    id_sucursal = Column("ID_Sucursal", Integer, nullable=False)
    activo = Column("Activo", Boolean, default=True)
    ultima_actualizacion = Column("Ultima_Actualizacion", DateTime, default=datetime.datetime.now)

class ProductoLocal(Base):
    __tablename__ = "Productos_Cache"
    id_producto = Column("ID_Producto", Integer, primary_key=True)
    nombre = Column("Nombre", String(150), nullable=False)
    precio_actual = Column("Precio_Actual", Numeric(12, 2), nullable=False)
    tasa_impuesto = Column("Tasa_Impuesto", Numeric(5, 2), default=0.18)
    stock_local = Column("Stock_Local", Integer, default=0)
    ultima_actualizacion = Column("Ultima_Actualizacion", DateTime, default=datetime.datetime.now)

class TurnoCaja(Base):
    __tablename__ = "Turnos_Caja"
    id_turno = Column("ID_Turno", String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_usuario = Column("ID_Usuario", Integer, ForeignKey("Usuarios_Locales.ID_Usuario"))
    id_sucursal = Column("ID_Sucursal", Integer, nullable=False)
    fecha_apertura = Column("Fecha_Apertura", DateTime, default=datetime.datetime.now)
    monto_inicial = Column("Monto_Inicial", Numeric(12, 2), nullable=False)
    fecha_cierre = Column("Fecha_Cierre", DateTime, nullable=True)
    monto_calculado = Column("Monto_Calculado", Numeric(12, 2), nullable=True)
    monto_fisico = Column("Monto_Fisico", Numeric(12, 2), nullable=True)
    estado = Column("Estado", String(20), default="ABIERTO")
    sincronizado = Column("Sincronizado", Boolean, default=False)

class MovimientoEfectivo(Base):
    __tablename__ = "Movimientos_Efectivo"
    id_movimiento = Column("ID_Movimiento", String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_turno = Column("ID_Turno", String(50), ForeignKey("Turnos_Caja.ID_Turno"))
    tipo_movimiento = Column("Tipo_Movimiento", String(20), nullable=False)
    monto = Column("Monto", Numeric(12, 2), nullable=False)
    concepto = Column("Concepto", String(255), nullable=False)
    fecha_hora = Column("Fecha_Hora", DateTime, default=datetime.datetime.now)
    sincronizado = Column("Sincronizado", Boolean, default=False)

class FacturaLocal(Base):
    __tablename__ = "Facturas_Locales"
    id_factura = Column("ID_Factura", String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_turno = Column("ID_Turno", String(50), ForeignKey("Turnos_Caja.ID_Turno"))
    id_sucursal = Column("ID_Sucursal", Integer, nullable=False)
    fecha_hora = Column("Fecha_Hora", DateTime, default=datetime.datetime.now)
    subtotal = Column("Subtotal", Numeric(12, 2), nullable=False)
    total_impuestos = Column("Total_Impuestos", Numeric(12, 2), nullable=False)
    total_general = Column("Total_General", Numeric(12, 2), nullable=False)
    metodo_pago = Column("Metodo_Pago", String(50), nullable=False)
    sincronizado = Column("Sincronizado", Boolean, default=False)

class DetalleFactura(Base):
    __tablename__ = "Detalle_Facturas"
    id_detalle = Column("ID_Detalle", String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_factura = Column("ID_Factura", String(50), ForeignKey("Facturas_Locales.ID_Factura"))
    id_producto = Column("ID_Producto", Integer, ForeignKey("Productos_Cache.ID_Producto"))
    cantidad = Column("Cantidad", Integer, nullable=False)
    precio_unitario = Column("Precio_Unitario", Numeric(12, 2), nullable=False)
    monto_impuesto = Column("Monto_Impuesto", Numeric(12, 2), nullable=False)
    subtotal_linea = Column("Subtotal_Linea", Numeric(12, 2), nullable=False)

class LogCaja(Base):
    __tablename__ = "Logs_Caja"
    id_log = Column("ID_Log", String(50), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_usuario = Column("ID_Usuario", Integer, ForeignKey("Usuarios_Locales.ID_Usuario"), nullable=True)
    id_sucursal = Column("ID_Sucursal", Integer, nullable=False)
    nivel = Column("Nivel", String(20), nullable=False)
    accion = Column("Accion", String(100), nullable=False)
    descripcion = Column("Descripcion", String(1000), nullable=False)
    fecha_hora = Column("Fecha_Hora", DateTime, default=datetime.datetime.now)
    sincronizado = Column("Sincronizado", Boolean, default=False)