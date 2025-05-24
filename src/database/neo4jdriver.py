from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

class Neo4jDriver:
    """Clase para manejar la conexión con Neo4j y ejecutar consultas"""
    
    _instance = None
    
    def __new__(cls):
        """Implementación del patrón Singleton para la conexión a la base de datos"""
        if cls._instance is None:
            cls._instance = super(Neo4jDriver, cls).__new__(cls)
            try:
                cls._instance.driver = GraphDatabase.driver(
                    NEO4J_URI, 
                    auth=(NEO4J_USER, NEO4J_PASSWORD)
                )
                cls._instance.driver.verify_connectivity()
                print("Conexión exitosa a la base de datos Neo4j")
            except Exception as e:
                print(f"Error de conexión a Neo4j: {e}")
                raise
        return cls._instance
    
    def close(self):
        """Cierra la conexión con Neo4j"""
        if hasattr(self, 'driver'):
            self.driver.close()
            print("Conexión a Neo4j cerrada")
    
    def get_session(self):
        """Retorna una nueva sesión de Neo4j"""
        return self.driver.session()
    
    def execute_read(self, query, **params):
        """Ejecuta una consulta de lectura en Neo4j"""
        with self.driver.session() as session:
            result = session.run(query, **params)
            return [record for record in result]
    
    def execute_write(self, query, **params):
        """Ejecuta una consulta de escritura en Neo4j"""
        with self.driver.session() as session:
            result = session.run(query, **params)
            return [record for record in result]
    
    def execute_transaction(self, func, *args, **kwargs):
        """Ejecuta una función dentro de una transacción"""
        with self.driver.session() as session:
            return session.execute_write(func, *args, **kwargs)
    
    def run_query(self, query, **params):
        """Método alternativo para ejecutar consultas (compatibilidad)"""
        with self.driver.session() as session:
            result = session.run(query, **params)
            return [record for record in result]