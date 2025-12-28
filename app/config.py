from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    # Cargar variables de entorno desde .env
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    DB_NAME = os.getenv("DB_NAME", "mi_base_de_datos")
    PORT = int(os.getenv("PORT", 4002))
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

config = Config()
