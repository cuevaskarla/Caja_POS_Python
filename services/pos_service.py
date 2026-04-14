from db.connection import SessionLocal, transaction_scope
from models.entities import UsuarioLocal, ProductoLocal, TurnoCaja, FacturaLocal, DetalleFactura, LogCaja
from decimal import Decimal
import datetime
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
import os

class POSService:
    active_user = None
    active_turno = None

    def login(self, u_id, clave):
        db = SessionLocal()
        try:
            user = db.query(UsuarioLocal).filter_by(id_usuario=u_id, hash_clave=clave, activo=True).first()
            if user:
                POSService.active_user = user
                return True
            return False
        finally: db.close()

    def abrir_turno(self, monto):
        try:
            with transaction_scope() as db:
                nuevo = TurnoCaja(
                    id_usuario=POSService.active_user.id_usuario,
                    id_sucursal=POSService.active_user.id_sucursal,
                    monto_inicial=Decimal(str(monto)),
                    estado='ABIERTO'
                )
                db.add(nuevo)
                db.flush()
                POSService.active_turno = nuevo
            return True
        except: return False

    def cerrar_turno(self, monto_fisico):
        try:
            db = SessionLocal()
            ventas = db.query(FacturaLocal).filter_by(id_turno=POSService.active_turno.id_turno).all()
            total_ventas = sum(f.total_general for f in ventas)
            monto_esperado = POSService.active_turno.monto_inicial + total_ventas

            with transaction_scope() as db_trans:
                turno = db_trans.query(TurnoCaja).get(POSService.active_turno.id_turno)
                turno.fecha_cierre = datetime.datetime.now()
                turno.monto_calculado = monto_esperado
                turno.monto_fisico = Decimal(str(monto_fisico))
                turno.estado = 'CERRADO'
            
            descuadre = Decimal(str(monto_fisico)) - monto_esperado
            return float(monto_esperado), float(descuadre)
        finally: db.close()

    def buscar_producto(self, termino):
        db = SessionLocal()
        try:
            # Si el término es un número (o un string que parece número), buscamos por ID
            if str(termino).isdigit():
                return db.query(ProductoLocal).filter(ProductoLocal.id_producto == int(termino)).all()
            
            # Si son letras, buscamos por Nombre (como estaba antes)
            return db.query(ProductoLocal).filter(ProductoLocal.nombre.contains(termino)).all()
        finally: 
            db.close()

    def calcular_totales(self, carrito):
        sub = sum(Decimal(str(i['precio'])) * i['cant'] for i in carrito)
        imp = sum((Decimal(str(i['precio'])) * Decimal(str(i['tasa']))) * i['cant'] for i in carrito)
        tot = sub + imp
        return sub, imp, tot

    def procesar_venta(self, carrito, efectivo, metodo, ncf_tipo, ncf_num, rnc, cliente):
        sub, imp, total = self.calcular_totales(carrito)
        efec = Decimal(str(efectivo)) if metodo == "EFECTIVO" else total
        
        if metodo == "EFECTIVO" and efec < total:
            return None, "Efectivo insuficiente"

        try:
            with transaction_scope() as db:
                # Creacion de factura respetando estrictamente el DDL
                factura = FacturaLocal(
                    id_turno=POSService.active_turno.id_turno,
                    id_sucursal=POSService.active_user.id_sucursal,
                    subtotal=sub, 
                    total_impuestos=imp, 
                    total_general=total,
                    metodo_pago=metodo
                )
                db.add(factura)
                db.flush()

                for i in carrito:
                    p_unit = Decimal(str(i['precio']))
                    m_imp = p_unit * Decimal(str(i['tasa']))
                    det = DetalleFactura(
                        id_factura=factura.id_factura, id_producto=i['id'],
                        cantidad=i['cant'], precio_unitario=p_unit,
                        monto_impuesto=m_imp, subtotal_linea=(p_unit + m_imp) * i['cant']
                    )
                    db.add(det)
                
                self.generar_ticket_pdf(factura, carrito, efec, ncf_tipo, ncf_num, rnc, cliente)

                # Auditoria para respaldar datos fiscales
                log_data = f"Factura:{factura.id_factura} | Cliente:{cliente} | RNC:{rnc} | NCF:{ncf_num} | Pago:{metodo}"
                log = LogCaja(id_usuario=POSService.active_user.id_usuario, 
                             id_sucursal=POSService.active_user.id_sucursal,
                             nivel="INFO", accion="VENTA_FISCAL", descripcion=log_data)
                db.add(log)

            return float(efec - total), "Venta Exitosa"
        except Exception as e:
            return None, str(e)

    def generar_ticket_pdf(self, factura, carrito, efec, ncf_tipo, ncf_num, rnc, cliente):
        try:
            # RUTA ABSOLUTA FORZADA
            folder = r"D:\Tareas Intec\Caja_POS_Python\Tickets"
            
            # Si la carpeta no existe, la creamos
            if not os.path.exists(folder):
                os.makedirs(folder)
            
            # 1. Aseguramos que el ID sea string para el nombre del archivo
            id_str = str(factura.id_factura)
            filename = os.path.join(folder, f"Ticket_{id_str}.pdf")
            
            print(f"DEBUG: Intentando guardar ticket en: {filename}")
            
            c = canvas.Canvas(filename, pagesize=(80*mm, 180*mm))
            y = 170*mm
            
            # 2. Manejo de fecha (si es None, usamos la hora actual)
            fecha_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
            if factura.fecha_hora:
                fecha_str = factura.fecha_hora.strftime('%Y-%m-%d %H:%M')

            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(40*mm, y, "CAJA MASTER SYSTEM")
            y -= 5*mm
            c.setFont("Helvetica", 8)
            c.drawCentredString(40*mm, y, "FACTURA DE " + str(ncf_tipo).upper())
            y -= 4*mm
            c.drawCentredString(40*mm, y, f"NCF: {ncf_num}")
            y -= 6*mm
            
            c.line(5*mm, y, 75*mm, y); y -= 4*mm
            c.drawString(5*mm, y, f"Cliente: {str(cliente)[:25]}")
            y -= 4*mm
            c.drawString(5*mm, y, f"RNC/Ced: {rnc}")
            y -= 4*mm
            c.drawString(5*mm, y, f"Fecha: {fecha_str}")
            y -= 4*mm
            c.line(5*mm, y, 75*mm, y); y -= 6*mm
            
            c.setFont("Helvetica-Bold", 7)
            c.drawString(5*mm, y, "CANT    DESCRIPCION")
            c.drawRightString(75*mm, y, "PRECIO")
            y -= 4*mm
            c.setFont("Helvetica", 7)
            
            for item in carrito:
                precio_f = float(item['precio'])
                c.drawString(5*mm, y, f"{item['cant']}x  {str(item['nombre'])[:20]}")
                c.drawRightString(75*mm, y, f"{precio_f:.2f}")
                y -= 4*mm
                if y < 30*mm: 
                    c.showPage()
                    y = 170*mm 
            
            y -= 2*mm
            c.line(5*mm, y, 75*mm, y); y -= 6*mm
            
            c.setFont("Helvetica", 8)
            c.drawString(5*mm, y, "Subtotal:")
            c.drawRightString(75*mm, y, f"RD$ {float(factura.subtotal):.2f}")
            y -= 4*mm
            c.drawString(5*mm, y, "ITBIS (18%):")
            c.drawRightString(75*mm, y, f"RD$ {float(factura.total_impuestos):.2f}")
            y -= 5*mm
            c.setFont("Helvetica-Bold", 10)
            c.drawString(5*mm, y, "TOTAL:")
            c.drawRightString(75*mm, y, f"RD$ {float(factura.total_general):.2f}")
            y -= 7*mm
            
            c.setFont("Helvetica", 8)
            c.drawString(5*mm, y, f"Metodo: {factura.metodo_pago}")
            y -= 4*mm
            c.drawString(5*mm, y, f"Efectivo: RD$ {float(efec):.2f}")
            y -= 4*mm
            cambio = float(efec) - float(factura.total_general)
            c.drawString(5*mm, y, f"Cambio: RD$ {cambio:.2f}")
            y -= 10*mm
            c.drawCentredString(40*mm, y, "Gracias por su compra") 
            
            c.save()
            print(f"✅ Ticket generado exitosamente en: {filename}")
            
        except Exception as e:
            print(f"❌ Error fatal en PDF: {str(e)}")