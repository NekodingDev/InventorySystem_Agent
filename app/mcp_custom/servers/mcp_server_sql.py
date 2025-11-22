import logging
import mysql.connector
from mcp.server.fastmcp import FastMCP
from mysql.connector import Error
from dotenv import load_dotenv
import os

load_dotenv()

# Cargar variables de entorno desde .env
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "mi_base_de_datos")

# Inicializar el servidor MCP
mcp = FastMCP("Cerámica de Altura - Agent", dependencies=["mysql-connector-python"], port=4003)


def connect_to_database(host: str, user: str, password: str, database: str):
    """
    Conecta a una base de datos MySQL y devuelve la conexión.

    :param host: Dirección del servidor MySQL (e.g., 'localhost').
    :param user: Nombre de usuario para la conexión.
    :param password: Contraseña del usuario.
    :param database: Nombre de la base de datos a la que se desea conectar.
    :return: Objeto de conexión si la conexión es exitosa, None en caso de error.
    """
    try:
        connection = mysql.connector.connect(
            host=host, user=user, password=password, database=database
        )
        if connection.is_connected():
            logging.info("Conexión a la base de datos MySQL exitosa.")
            return connection
    except Error as e:
        logging.error(f"Error al conectar a la base de datos: {e}")
        return None

    return None


@mcp.tool()
def execute_sql_query(query: str) -> dict:
    """
    Ejecuta una consulta SQL y devuelve los resultados en formato de diccionario.

    Descripción de la tabla usuarios:
    - id: Identificador único del usuario (int)
    - nombre: Nombre del usuario (str)
    - role_id: Identificador del rol asociado (int)
    - created_at: Fecha de creación del usuario (datetime)

    Descripción de la tabla categorias
    - id: Identificador único de la categoría (int)
    - description: Descripción de la categoría (str)
    - created_at: Fecha de creación de la categoría (datetime)

    Descripción de la tabla detalle_entradas
    - id: Identificador único del detalle de entrada (int)
    - entrada_id: Identificador de la entrada asociada (int)
    - producto_id: Identificador del producto asociado (int)
    - cantidad_ingresada: Cantidad ingresada del producto (decimal 10,3)
    - created_at: Fecha de creación del detalle de entrada (datetime)

    Descripción de la tabla detalle_salidas
    - id: Identificador único del detalle de salida (int)
    - salida_id: Identificador de la salida asociada (int)
    - producto_id: Identificador del producto asociado (int)
    - cantidad_salida: Cantidad salida del producto (decimal 10,3)
    - created_at: Fecha de creación del detalle de salida (datetime)

    Descripción de la tabla entradas
    - id: Identificador único de la entrada (int)
    - establecimiento_id: Identificador del establecimiento asociado (int)
    - proveedor_id: Identificador del proveedor asociado (int, nullable)
    - usuario_id: Identificador del usuario que registró la entrada (int)
    - tipo_entrada: Tipo de entrada (str)
    - created_at: Fecha de creación de la entrada (datetime)

    Descripción de la tabla establecimientos
    - id: Identificador único del establecimiento (int)
    - nombre: Nombre del establecimiento (str)
    - direccion: Dirección del establecimiento (str)
    - created_at: Fecha de creación del establecimiento (datetime)

    Descripción de la tabla productos
    - id: Identificador único del producto (int)
    - cod_producto: Código único del producto (str)
    - nombre: Nombre del producto (str)
    - formato: Formato o presentación del producto (str)
    - categoria_id: Identificador de la categoría asociada (int)
    - precio: Precio del producto (decimal 10,2)
    - activado: Indica si el producto está activo (boolean)
    - created_at: Fecha de creación del producto (datetime)

    Descripción de la tabla proveedores
    - id: Identificador único del proveedor (int)
    - nombre: Nombre del proveedor (str)
    - created_at: Fecha de creación del proveedor (datetime)

    Descripción de la tabla roles
    - id: Identificador único del rol (int)
    - description: Descripción del rol (str)
    - created_at: Fecha de creación del rol (datetime)

    Descripción de la tabla salidas
    - id: Identificador único de la salida (int)
    - establecimiento_id: Identificador del establecimiento asociado (int)
    - usuario_id: Identificador del usuario que registró la salida (int)
    - tipo_salida: Tipo de salida (str)
    - created_at: Fecha de creación de la salida (datetime)

    Descripción de la tabla stock
    - id: Identificador único del registro de stock (int)
    - product_id: Identificador del producto asociado (int)
    - establecimiento_id: Identificador del establecimiento asociado (int)
    - cantidad: Cantidad disponible del producto (int)
    - created_at: Fecha de creación del registro de stock (datetime)

    :param query: Consulta SQL a ejecutar.
    :return: Diccionario con los resultados de la consulta.
    """
    try:
        connection = connect_to_database(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )

        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query)
            results = cursor.fetchall()

            cursor.close()
            connection.close()

            return {"success": True, "data": results}

    except Error as e:
        return {"success": False, "error": str(e)}

    return {
        "success": False,
        "error": "No se pudo establecer conexión con la base de datos",
    }


if __name__ == "__main__":
    try:
        # Ejecutar el servidor MCP
        logging.info("Iniciando el servidor MCP...")
        mcp.run()
    except Exception as e:
        logging.error(f"Ocurrió un error al iniciar el servidor MCP: {str(e)}")
