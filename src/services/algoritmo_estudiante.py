from src.database.neo4jdriver import Neo4jDriver
from src.models.estudiante import Estudiante

class AlgoritmoEstudiante:
    """Clase para gestionar operaciones relacionadas con estudiantes en Neo4j"""
    
    def __init__(self):
        self.driver = Neo4jDriver()
    
    def registrar_estudiante(self, estudiante: Estudiante):
        """
        Registra un nuevo estudiante en la base de datos y calcula su puntuación
        
        Args:
            estudiante: Objeto Estudiante con los datos del estudiante
            
        Returns:
            dict: Nodo del estudiante creado en la base de datos
        """
        # Calcular puntuación del estudiante
        puntuacion_total = estudiante.calcular_puntuacion()
        
        # Query en Cypher para la creación del nodo del estudiante
        query = """
        CREATE (e:Estudiante {
            nombre: $nombre,
            estilo_aprendizaje: $estilo_aprendizaje,
            estilo_clase: $estilo_clase,
            promedio: $promedio,
            asistencias_curso_anterior: $asistencias,
            veces_que_llevo_curso: $veces_curso,
            puntuacion_total: $puntuacion_total
        })
        RETURN e
        """
        
        # Ejecutar la consulta en Neo4j
        result = self.driver.execute_write(
            query,
            nombre=estudiante.nombre,
            estilo_aprendizaje=estudiante.estilo_aprendizaje,
            estilo_clase=estudiante.estilo_clase,
            promedio=estudiante.promedio,
            asistencias=estudiante.asistencias,
            veces_curso=estudiante.veces_curso,
            puntuacion_total=puntuacion_total
        )
        
        if result:
            return result[0]["e"]
        return None
    
    def obtener_estudiante(self, nombre):
        """
        Obtiene un estudiante por su nombre
        
        Args:
            nombre: Nombre del estudiante a buscar
            
        Returns:
            dict: Datos del estudiante encontrado o None
        """
        query = """
        MATCH (e:Estudiante {nombre: $nombre})
        RETURN e
        """
        
        result = self.driver.execute_read(query, nombre=nombre)
        
        if result:
            return result[0]["e"]
        return None
    
    def encontrar_estudiantes_similares(self, nombre_estudiante):
        """
        Encuentra estudiantes similares basándose en criterios específicos
        
        Args:
            nombre_estudiante: Nombre del estudiante de referencia
            
        Returns:
            list: Lista de estudiantes similares
        """
        query = """
        MATCH (e:Estudiante {nombre: $nombre_estudiante})
        MATCH (similar:Estudiante)
        WHERE similar.nombre <> e.nombre
            AND similar.estilo_aprendizaje = e.estilo_aprendizaje
            AND similar.estilo_clase = e.estilo_clase
            AND abs(similar.veces_que_llevo_curso - e.veces_que_llevo_curso) <= 1
            AND abs(similar.promedio - e.promedio) <= 5
        RETURN similar
        """
        
        result = self.driver.execute_read(query, nombre_estudiante=nombre_estudiante)
        
        if result:
            return [record["similar"] for record in result]
        return []
