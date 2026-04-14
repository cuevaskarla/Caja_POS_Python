#  Terminal POS 

Este proyecto consiste en una terminal de punto de venta (POS) desarrollada en **Python**, diseñada para operar de forma local y sincronizar datos de ventas con un núcleo centralizado.

## Características de Seguridad
Como parte de la formación en ciberseguridad, se implementaron las siguientes medidas:
* **Autenticación Segura:** Validación de usuarios mediante **Bcrypt** para el hashing de contraseñas.
* **Integración JWT:** Comunicación con el Gateway central protegida por tokens de sesión.
* **Auditoría de Transacciones:** Registro detallado de cada operación en una tabla de logs local.

## Tecnologías Utilizadas
* **Lenguaje:** Python 3.13
* **GUI:** PySide6 (Qt)
* **Base de Datos:** SQL Server (SQLAlchemy / SQLModel)
* **Reportes:** ReportLab para generación de facturas legales en PDF.
* **Sincronización:** Requests para comunicación con API REST.

## Estructura del Proyecto
* `/db`: Configuración de la conexión y sesión local.
* `/models`: Definición de entidades de base de datos.
* `/services`: Lógica de negocio (POS, Autenticación, Sincronización).
* `/views`: Interfaz gráfica de usuario.
* `/Tickets`: (Ignorado en Git) Carpeta local de almacenamiento de recibos PDF.
