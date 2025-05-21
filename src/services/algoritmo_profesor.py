from src.database.neo4jdriver import Neo4jDriver
from src.models.profesor import Profesor

class AlgoritmoProfesor:
    """Clase para gestionar operaciones relacionadas con profesores en Neo4j"""
    
    def __init__(self):
        self.driver = Neo4jDriver()
    
    def registrar_profesor(self, profesor: Profesor):
        """
        Registra un nuevo profesor en la base de datos y calcula su puntuación
        
        Args:
            profesor: Objeto Profesor con los datos del profesor
            
        Returns:
            dict: Nodo del profesor creado en la base de datos
        """
        # Calcular puntuación del profesor
        puntuacion_total = profesor.calcular_puntuacion()
        
        # Query en Cypher para la creación del nodo del profesor
        query = """
        CREATE (p:Profesor {
            nombre: $nombre,
            estilo_enseñanza: $estilo_enseñanza,
            estilo_clase: $estilo_clase,
            años_experiencia: $años_experiencia,
            evaluacion_docente: $evaluacion_docente,
            porcentaje_aprobados: $porcentaje_aprobados,
            disponibilidad: $disponibilidad,
            puntuacion_total: $puntuacion_total
        })
        RETURN p
        """
        
        # Ejecutar la consulta en Neo4j
        result = self.driver.execute_write(
            query,
            nombre=profesor.nombre,
            estilo_enseñanza=profesor.estilo_enseñanza,
            estilo_clase=profesor.estilo_clase,
            años_experiencia=profesor.años_experiencia,
            evaluacion_docente=profesor.evaluacion_docente,
            porcentaje_aprobados=profesor.porcentaje_aprobados,
            disponibilidad=profesor.disponibilidad,
            puntuacion_total=puntuacion_total
        )
        
        if result:
            return result[0]["p"]
        return None
    
    def obtener_profesor(self, nombre):
        """
        Obtiene un profesor por su nombre
        
        Args:
            nombre: Nombre del profesor a buscar
            
        Returns:
            dict: Datos del profesor encontrado o None
        """
        query = """
        MATCH (p:Profesor {nombre: $nombre})
        RETURN p
        """
        
        result = self.driver.execute_read(query, nombre=nombre)
        
        if result:
            return result[0]["p"]
        return None
    
    def obtener_profesores_compatibles(self, estilo_aprendizaje, estilo_clase):
        """
        Obtiene profesores que son compatibles con un estilo de aprendizaje y clase
        
        Args:
            estilo_aprendizaje: Estilo de aprendizaje del estudiante
            estilo_clase: Estilo de clase preferido
            
        Returns:
            list: Lista de profesores compatibles
        """
        query = """
        MATCH (p:Profesor)
        WHERE p.estilo_enseñanza = $estilo_aprendizaje 
            AND p.estilo_clase = $estilo_clase
        RETURN p
        """
        
        result = self.driver.execute_read(
            query, 
            estilo_aprendizaje=estilo_aprendizaje,
            estilo_clase=estilo_clase
        )
        
        if result:
            return [record["p"] for record in result]
        return []
    
    def registrar_curso_impartido(self, nombre_profesor, codigo_curso):
        """
        Registra que un profesor imparte un curso
        
        Args:
            nombre_profesor: Nombre del profesor
            codigo_curso: Código del curso
            
        Returns:
            bool: True si se registró correctamente, False en caso contrario
        """
        query = """
        MATCH (p:Profesor {nombre: $nombre_profesor})
        MATCH (c:Curso {codigo: $codigo_curso})
        MERGE (p)-[r:IMPARTE]->(c)
        RETURN p, r, c
        """
        
        result = self.driver.execute_write(
            query,
            nombre_profesor=nombre_profesor,
            codigo_curso=codigo_curso
        )
        
        return len(result) > 0
