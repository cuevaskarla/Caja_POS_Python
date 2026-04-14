from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QStackedWidget, 
                             QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QListWidget, QListWidgetItem, QInputDialog, QComboBox, QFrame, QInputDialog, QLineEdit)
from PySide6.QtCore import Qt
from services.pos_service import POSService
from services.sync_service import SyncService

STYLESHEET = """
    QMainWindow { background-color: #0b1120; }
    QLabel { color: #e2e8f0; font-family: 'Segoe UI', Consolas, monospace; }
    
    QLineEdit, QComboBox { 
        background-color: #1e293b; 
        color: #38bdf8; 
        padding: 12px; 
        border: 2px solid #334155; 
        border-radius: 6px; 
        font-size: 14px;
        font-weight: bold;
    }
    QLineEdit:focus, QComboBox:focus { border: 2px solid #0ea5e9; background-color: #0f172a; }
    
    QPushButton { 
        background-color: #0284c7; 
        color: white; 
        padding: 12px; 
        font-weight: bold; 
        font-size: 14px;
        border-radius: 6px;
        border: none;
    }
    QPushButton:hover { background-color: #0369a1; }
    
    QPushButton#BtnDanger { background-color: #e11d48; }
    QPushButton#BtnDanger:hover { background-color: #be123c; }
    
    QPushButton#BtnSuccess { background-color: #10b981; font-size: 16px; }
    QPushButton#BtnSuccess:hover { background-color: #059669; }
    
    QTableWidget { 
        background-color: #1e293b; 
        color: #f8fafc; 
        gridline-color: #334155; 
        border: 1px solid #475569;
        border-radius: 6px;
        font-size: 14px;
        selection-background-color: #0ea5e9; 
        selection-color: white;
    }
    QHeaderView::section { 
        background-color: #0f172a; 
        color: #94a3b8; 
        padding: 8px; 
        font-weight: bold;
        border: 1px solid #334155;
    }
    
    QListWidget { 
        background-color: #1e293b; 
        color: #f8fafc; 
        border: 2px solid #0ea5e9; 
        border-radius: 6px; 
        font-size: 14px;
    }
    QListWidget::item { padding: 12px; border-bottom: 1px solid #334155; }
    QListWidget::item:hover, QListWidget::item:selected { background-color: #0284c7; color: white; }
    
    QFrame#CajaFrame {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 8px;
    }
    QFrame#CobroFrame {
        background-color: #0f172a;
        border: 2px solid #38bdf8;
        border-radius: 8px;
    }
"""

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.pos = POSService()
        self.sincronizador = SyncService()
        self.carrito = []
        self.ventas_turno = 0.0  # Variable en memoria para el visor de caja
        self.fondo_inicial = 0.0
        
        self.setFixedSize(1100, 800)
        self.setWindowTitle("SISTEMA POS MASTER - TERMINAL DE CAJA")
        self.setStyleSheet(STYLESHEET)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.init_login()
        self.init_apertura()
        self.init_ventas()

    def init_login(self):
        w = QWidget(); l = QVBoxLayout(w); l.setAlignment(Qt.AlignCenter)
        frame = QFrame(); frame.setObjectName("CajaFrame"); frame.setFixedSize(450, 400)
        fl = QVBoxLayout(frame); fl.setContentsMargins(40, 40, 40, 40)
        
        lbl_titulo = QLabel("AUTENTICACIÓN DE TERMINAL")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #38bdf8;")
        lbl_titulo.setAlignment(Qt.AlignCenter)
        
        self.u = QLineEdit(); self.u.setPlaceholderText("ID de Empleado")
        self.p = QLineEdit(); self.p.setPlaceholderText("Clave de Acceso"); self.p.setEchoMode(QLineEdit.Password)
        btn = QPushButton("INICIAR SESIÓN"); btn.clicked.connect(self.do_login)
        
        fl.addWidget(lbl_titulo); fl.addSpacing(30)
        fl.addWidget(QLabel("CREDENCIALES:")); fl.addWidget(self.u); fl.addWidget(self.p)
        fl.addSpacing(20); fl.addWidget(btn)
        
        l.addWidget(frame)
        self.stack.addWidget(w)

    def init_apertura(self):
        w = QWidget(); l = QVBoxLayout(w); l.setAlignment(Qt.AlignCenter)
        frame = QFrame(); frame.setObjectName("CajaFrame"); frame.setFixedSize(450, 300)
        fl = QVBoxLayout(frame); fl.setContentsMargins(40, 40, 40, 40)
        
        lbl_titulo = QLabel("DECLARACIÓN DE FONDO")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold; color: #10b981;")
        lbl_titulo.setAlignment(Qt.AlignCenter)
        
        self.f = QLineEdit(); self.f.setPlaceholderText("Ej. 5000.00")
        btn = QPushButton("ABRIR CAJA Y COMENZAR"); btn.setObjectName("BtnSuccess")
        btn.clicked.connect(self.do_apertura)
        
        fl.addWidget(lbl_titulo); fl.addSpacing(20)
        fl.addWidget(QLabel("EFECTIVO INICIAL EN GAVETA (RD$):")); fl.addWidget(self.f); fl.addSpacing(10); fl.addWidget(btn)
        
        l.addWidget(frame)
        self.stack.addWidget(w)

    def init_ventas(self):
        w = QWidget(); main_l = QVBoxLayout(w); main_l.setContentsMargins(20, 20, 20, 20)
        
        # --- PANEL SUPERIOR: VISOR DE CAJA Y CONTROLES ---
        top_frame = QFrame(); top_frame.setObjectName("CajaFrame")
        top_layout = QHBoxLayout(top_frame); top_layout.setContentsMargins(15, 10, 15, 10)
        
        # Visor de telemetría de efectivo
        telemetria_layout = QHBoxLayout()
        self.lbl_fondo = QLabel("FONDO: RD$ 0.00"); self.lbl_fondo.setStyleSheet("color: #94a3b8; font-weight: bold; font-size: 16px;")
        self.lbl_ventas = QLabel("VENTAS: RD$ 0.00"); self.lbl_ventas.setStyleSheet("color: #38bdf8; font-weight: bold; font-size: 16px;")
        self.lbl_esperado = QLabel("CAJA DEBE TENER: RD$ 0.00"); self.lbl_esperado.setStyleSheet("color: #10b981; font-weight: bold; font-size: 18px;")
        
        telemetria_layout.addWidget(self.lbl_fondo); telemetria_layout.addSpacing(20)
        telemetria_layout.addWidget(self.lbl_ventas); telemetria_layout.addSpacing(20)
        telemetria_layout.addWidget(self.lbl_esperado)
        
        btn_close = QPushButton("CERRAR CAJA (Z)"); btn_close.setObjectName("BtnDanger"); btn_close.setFixedWidth(200)
        btn_close.clicked.connect(self.do_cierre_caja)

        btn_sync = QPushButton("SINC. CORE"); btn_sync.setStyleSheet("background-color: #6366f1; color: white; border-radius: 6px; padding: 10px; font-weight: bold;")
        btn_sync.clicked.connect(self.do_sincronizacion)
        
        top_layout.addLayout(telemetria_layout); top_layout.addStretch(); top_layout.addWidget(btn_sync); top_layout.addWidget(btn_close)
        main_l.addWidget(top_frame)

        # --- PANEL CENTRAL: BUSCADOR Y TABLA ---
        mid_layout = QHBoxLayout()
        
        # Buscador con autocompletado
        search_l = QVBoxLayout()
        self.search = QLineEdit(); self.search.setPlaceholderText(" Buscar producto por nombre o ID...")
        self.search.textChanged.connect(self.on_typing)
        self.list_res = QListWidget(); self.list_res.hide(); self.list_res.setMaximumHeight(120)
        self.list_res.itemClicked.connect(self.on_item_selected)
        search_l.addWidget(self.search); search_l.addWidget(self.list_res); search_l.addStretch()
        
        btn_delete = QPushButton("ELIMINAR ITEM"); btn_delete.setObjectName("BtnDanger")
        btn_delete.clicked.connect(self.do_delete_item); btn_delete.setFixedHeight(45)
        
        mid_layout.addLayout(search_l, stretch=3); mid_layout.addWidget(btn_delete, stretch=1, alignment=Qt.AlignTop)
        main_l.addLayout(mid_layout)

        self.table = QTableWidget(0, 4); self.table.setHorizontalHeaderLabels(["ID", "PRODUCTO", "PRECIO UNIT.", "CANTIDAD"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setAlternatingRowColors(True)
        main_l.addWidget(self.table)

        # --- PANEL INFERIOR: FACTURACIÓN Y COBRO ---
        bot_layout = QHBoxLayout()
        
        # Datos Fiscales
        fiscal_frame = QFrame(); fiscal_frame.setObjectName("CajaFrame")
        fiscal_l = QVBoxLayout(fiscal_frame)
        self.txt_cliente = QLineEdit(); self.txt_cliente.setPlaceholderText("Nombre del Cliente (Opcional)")
        self.txt_rnc = QLineEdit(); self.txt_rnc.setPlaceholderText("RNC / Cédula")
        self.cb_ncf = QComboBox(); self.cb_ncf.addItems(["CONSUMO (B02)", "CREDITO FISCAL (B01)", "GUBERNAMENTAL (B15)"])
        fiscal_l.addWidget(QLabel("DATOS DE FACTURACIÓN")); fiscal_l.addWidget(self.txt_cliente)
        fiscal_l.addWidget(self.txt_rnc); fiscal_l.addWidget(self.cb_ncf)
        
        # Método de Pago
        pago_frame = QFrame(); pago_frame.setObjectName("CajaFrame")
        pago_l = QVBoxLayout(pago_frame)
        self.cb_metodo = QComboBox(); self.cb_metodo.addItems(["EFECTIVO", "TARJETA", "TRANSFERENCIA"])
        self.cb_metodo.currentTextChanged.connect(self.on_payment_change)
        pago_l.addWidget(QLabel("MÉTODO DE PAGO")); pago_l.addWidget(self.cb_metodo); pago_l.addStretch()
        
        # Resumen y Cobro (Destacado)
        cobro_frame = QFrame(); cobro_frame.setObjectName("CobroFrame")
        calc_l = QVBoxLayout(cobro_frame)
        self.total_lbl = QLabel("TOTAL: RD$ 0.00"); self.total_lbl.setStyleSheet("font-size: 36px; color: #38bdf8; font-weight: bold;")
        self.total_lbl.setAlignment(Qt.AlignRight)
        self.cash = QLineEdit(); self.cash.setPlaceholderText("Efectivo Recibido"); self.cash.setStyleSheet("font-size: 18px;")
        btn_pago = QPushButton("PROCESAR Y FACTURAR"); btn_pago.setObjectName("BtnSuccess"); btn_pago.setFixedHeight(60)
        btn_pago.clicked.connect(self.do_pago)
        calc_l.addWidget(self.total_lbl); calc_l.addWidget(self.cash); calc_l.addWidget(btn_pago)
        
        bot_layout.addWidget(fiscal_frame, 2); bot_layout.addWidget(pago_frame, 1); bot_layout.addWidget(cobro_frame, 2)
        main_l.addLayout(bot_layout)
        
        self.stack.addWidget(w)

    # --- LÓGICA DE INTERFAZ ---

    def do_login(self):
        if self.pos.login(self.u.text(), self.p.text()): 
            self.stack.setCurrentIndex(1)
        else: 
            QMessageBox.critical(self, "Acceso Denegado", "Credenciales incorrectas o usuario inactivo.")

    def do_apertura(self):
        if self.pos.abrir_turno(self.f.text()):
            # Inicializamos el visor de caja
            self.fondo_inicial = float(self.pos.active_turno.monto_inicial)
            self.ventas_turno = 0.0
            self.actualizar_visor_caja()
            self.stack.setCurrentIndex(2)
        else:
            QMessageBox.warning(self, "Error", "Por favor ingrese un monto inicial válido (Ej: 1500.50).")

    def actualizar_visor_caja(self):
        esperado = self.fondo_inicial + self.ventas_turno
        self.lbl_fondo.setText(f"FONDO: RD$ {self.fondo_inicial:,.2f}")
        self.lbl_ventas.setText(f"VENTAS: RD$ {self.ventas_turno:,.2f}")
        self.lbl_esperado.setText(f"CAJA DEBE TENER: RD$ {esperado:,.2f}")

    def on_typing(self, text):
        self.list_res.clear()
        if len(text) >= 2:
            res = self.pos.buscar_producto(text)
            if res:
                self.list_res.show()
                for p in res:
                    item = QListWidgetItem(f"➕ {p.nombre} - RD$ {p.precio_actual}")
                    item.setData(Qt.UserRole, p.id_producto)
                    self.list_res.addItem(item)
            else: self.list_res.hide()
        else: self.list_res.hide()

    def on_item_selected(self, item):
        id_prod = item.data(Qt.UserRole) 
        res = self.pos.buscar_producto(str(id_prod)) 
        if res:
            p = res[0] 
            self.agregar_a_tabla(p)
            # Limpiamos el buscador después de agregar
            self.search.clear()
            self.list_res.hide()
            self.search.setFocus()

    def agregar_a_tabla(self, p):
        idx = next((i for (i, it) in enumerate(self.carrito) if it["id"] == p.id_producto), None)
        if idx is not None:
            self.carrito[idx]['cant'] += 1
            self.table.item(idx, 3).setText(str(self.carrito[idx]['cant']))
        else:
            row = self.table.rowCount(); self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(p.id_producto)))
            self.table.setItem(row, 1, QTableWidgetItem(p.nombre))
            self.table.setItem(row, 2, QTableWidgetItem(str(p.precio_actual)))
            self.table.setItem(row, 3, QTableWidgetItem("1"))
            self.carrito.append({'id': p.id_producto, 'nombre': p.nombre, 'precio': p.precio_actual, 'cant': 1, 'tasa': p.tasa_impuesto})
        self.update_totals()

    def do_delete_item(self):
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            self.carrito.pop(row)
            self.update_totals()
            self.search.setFocus()
        else:
            QMessageBox.warning(self, "Atención", "Seleccione una fila en la tabla para eliminarla.")

    def on_payment_change(self, text):
        if text != "EFECTIVO":
            self.cash.setEnabled(False)
            self.cash.setText("0.00")
            self.cash.setStyleSheet("background-color: #334155; color: #94a3b8; font-size: 18px;")
        else:
            self.cash.setEnabled(True)
            self.cash.clear()
            self.cash.setStyleSheet("font-size: 18px;")

    def update_totals(self):
        _, _, tot = self.pos.calcular_totales(self.carrito)
        self.total_lbl.setText(f"TOTAL: RD$ {tot:,.2f}")

    def do_pago(self):
        if not self.carrito: 
            return QMessageBox.warning(self, "Atención", "No hay productos en el carrito.")
        
        _, _, total_venta = self.pos.calcular_totales(self.carrito)
        ncf_num = "B0200000001" if "B02" in self.cb_ncf.currentText() else "B0100000001"
        metodo = self.cb_metodo.currentText()
        cliente = self.txt_cliente.text() if self.txt_cliente.text() else "CLIENTE DE CONTADO"
        
        cambio, msg = self.pos.procesar_venta(
            self.carrito, self.cash.text(), metodo, self.cb_ncf.currentText(), 
            ncf_num, self.txt_rnc.text(), cliente
        )
        
        if cambio is not None:
            # Actualizamos el visor de caja en memoria
            self.ventas_turno += float(total_venta)
            self.actualizar_visor_caja()
            
            QMessageBox.information(self, "Transacción Exitosa", f"Factura guardada correctamente.\n\nCambio a devolver: RD$ {cambio:,.2f}")
            
            # Limpieza del panel
            self.carrito = []; self.table.setRowCount(0); self.update_totals()
            self.cash.clear(); self.txt_cliente.clear(); self.txt_rnc.clear()
            self.cb_metodo.setCurrentIndex(0); self.cb_ncf.setCurrentIndex(0)
            self.search.setFocus()
        else: 
            QMessageBox.warning(self, "Error en Transacción", msg)

    def do_cierre_caja(self):
        monto_fisico, ok = QInputDialog.getText(self, "Cierre de Caja (Z)", "Digite el monto físico total contado en la gaveta (RD$):")
        if ok and monto_fisico:
            try:
                esperado, descuadre = self.pos.cerrar_turno(monto_fisico)
                reporte = (
                    f"--- REPORTE DE CIERRE Z ---\n\n"
                    f"Monto Esperado en Sistema: RD$ {esperado:,.2f}\n"
                    f"Monto Físico Declarado: RD$ {float(monto_fisico):,.2f}\n"
                    f"Descuadre Detectado: RD$ {descuadre:,.2f}\n\n"
                    f"El turno ha sido cerrado de forma segura."
                )
                QMessageBox.information(self, "Cierre Completado", reporte)
                
                # Reseteamos variables y bloqueamos terminal volviendo al login
                self.ventas_turno = 0.0; self.fondo_inicial = 0.0
                self.u.clear(); self.p.clear(); self.f.clear()
                self.stack.setCurrentIndex(0)
            except Exception as e:
                QMessageBox.critical(self, "Error Fatal", f"No se pudo cerrar la caja: {str(e)}")

    def do_sincronizacion(self):
        """Abre ventanas emergentes para pedir credenciales y sincroniza"""
        try:
            # 1. Ventanita para el correo
            usuario, ok1 = QInputDialog.getText(self, "Login Core", "Gmail del Empleado:", QLineEdit.Normal)
            if not ok1 or not usuario: 
                return

            # 2. Ventanita para la clave
            clave, ok2 = QInputDialog.getText(self, "Login Core", "Contraseña:", QLineEdit.Password)
            if not ok2 or not clave: 
                return

            # 3. Llamada al autenticador del servicio de sincronización
            auth_ok, auth_msg = self.sincronizador.autenticar(usuario, clave)

            if auth_ok:
                print(f"✅ Éxito: {auth_msg}")
                
                # 🚀 Llamamos al método que recorre la base de datos y envía las ventas
                sync_ok, sync_msg = self.sincronizador.sincronizar_ventas_pendientes()
                
                if sync_ok:
                    QMessageBox.information(self, "Sincronización Completada", sync_msg)
                else:
                    QMessageBox.warning(self, "Sincronización Fallida", sync_msg)
            else:
                QMessageBox.critical(self, "Error de Autenticación", auth_msg)

        except Exception as e:
            QMessageBox.critical(self, "Error inesperado", f"Ocurrió un fallo: {str(e)}")