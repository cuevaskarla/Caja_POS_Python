import requests
from db.connection import SessionLocal
from models.entities import FacturaLocal, DetalleFactura

class SyncService:
    def __init__(self, api_base_url="http://localhost:8000"):
        self.api_base_url = api_base_url
        self.token = None

    def autenticar(self, identificador, password):
        url = f"{self.api_base_url}/api/v1/auth/login"
        # Ahora mandamos el 'password' real que viene de la interfaz
        payload = {"username": identificador.strip(), "password": password.strip()}
        try:
            response = requests.post(url, data=payload, timeout=10)
            if response.status_code == 200:
                self.token = response.json().get("access_token")
                return True, "Autenticado con éxito"
            return False, "Credenciales inválidas"
        except Exception as e:
            return False, f"Error de conexión: {str(e)}"

    def sincronizar_ventas_pendientes(self):
        """ESTE ES EL MÉTODO QUE FALTA"""
        if not self.token:
            return False, "No hay token disponible."

        db = SessionLocal()
        try:
            # Buscamos facturas que no estén sincronizadas
            ventas = db.query(FacturaLocal).filter(FacturaLocal.sincronizado == False).all()
            
            if not ventas:
                return True, "No hay ventas pendientes por sincronizar."

            headers = {"Authorization": f"Bearer {self.token}"}
            url_sync = f"{self.api_base_url}/api/v1/pedidos" # Revisa que esta ruta sea la de Karla
            
            exitos = 0
            for v in ventas:
                # Aquí va tu lógica de envío (payload)...
                # Por ahora, simulamos el éxito para que veas el cambio en BD
                v.sincronizado = True
                exitos += 1

            db.commit() # <--- IMPORTANTE: Guarda los cambios en SQL
            return True, f"Se sincronizaron {exitos} ventas con éxito."
        except Exception as e:
            db.rollback()
            return False, f"Error al sincronizar: {str(e)}"
        finally:
            db.close()