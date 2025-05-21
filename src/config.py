import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de Neo4j
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "12345678") # Esta es mi contraseña (esto es lo unico que tienen que cambiar)

# Configuración de API
API_PREFIX = "/api/v1"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"