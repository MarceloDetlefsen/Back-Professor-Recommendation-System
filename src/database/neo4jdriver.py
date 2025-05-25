from neo4j import GraphDatabase
from src.config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

class Neo4jDriver:
    """Clase mejorada para manejar la conexión con Neo4j"""
    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(
                NEO4J_URI, 
                auth=(NEO4J_USER, NEO4J_PASSWORD),
                max_connection_lifetime=3600,
                connection_timeout=30
            )
            with self.driver.session() as session:
                session.run("RETURN 1").single()
            print("✅ Conexión exitosa a Neo4j")
        except Exception as e:
            print(f"🔥 Error de conexión a Neo4j: {e}")
            raise

    def close(self):
        """Cierra la conexión con Neo4j"""
        if hasattr(self, 'driver'):
            self.driver.close()
            print("🔌 Conexión a Neo4j cerrada")

    def execute_read(self, query, **params):
        """Ejecuta una consulta de lectura con manejo de errores mejorado"""
        try:
            with self.driver.session() as session:
                result = session.run(query, **params)
                return list(result)
        except Exception as e:
            print(f"📖 Error en lectura: {query[:50]}... - {str(e)}")
            raise

    def execute_write(self, query, **params):
        """Ejecuta una consulta de escritura con confirmación explícita"""
        try:
            with self.driver.session() as session:
                result = session.run(query, **params)
                records = list(result)
                session.close()
                return records
        except Exception as e:
            print(f"✍️ Error en escritura: {query[:50]}... - {str(e)}")
            raise

    def execute_transaction(self, tx_func, *args, **kwargs):
        """Ejecuta una función compleja en una transacción explícita"""
        with self.driver.session() as session:
            return session.write_transaction(tx_func, *args, **kwargs)

    def verify_connection(self):
        """Verifica que la conexión esté activa"""
        try:
            with self.driver.session() as session:
                return bool(session.run("RETURN 1").single())
        except Exception:
            return False
            
    def get_session(self):
        """Devuelve una nueva sesión de la base de datos"""
        return self.driver.session()