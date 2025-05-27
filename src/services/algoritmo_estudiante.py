from database.neo4jdriver import Neo4jDriver
from models.estudiante import Estudiante

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
        #Validar que la entrada estpé mínimo completa
        if not estudiante.nombre or not estudiante.nombre.strip():
            return {"error": "El nombre del estudiante es requerido"}
        
        # Verificar que no hayan duplicados
        estudiante_existente = self.obtener_estudiante(estudiante.nombre.strip())
        if estudiante_existente:
            return {"error": f"Ya existe un estudiante con el nombre {estudiante.nombre}"}
        
        # Calcular puntuación del estudiante
        puntuacion_total = estudiante.calcular_puntuacion()
        
        # Query en Cypher para la creación del nodo del estudiante
        query = """
        MERGE (e:Estudiante {nombre: $nombre})
        ON CREATE SET 
            e.estilo_aprendizaje = $estilo_aprendizaje,
            e.estilo_clase = $estilo_clase,
            e.promedio = $promedio,
            e.asistencias_curso_anterior = $asistencias,
            e.veces_que_llevo_curso = $veces_curso,
            e.puntuacion_total = $puntuacion_total,
            e.fecha_registro = datetime()
        ON MATCH SET
            e.fecha_actualizacion = datetime()
        RETURN e, 
               CASE WHEN e.fecha_registro = datetime() THEN 'creado' ELSE 'actualizado' END as accion
        """
        
        try:
            result = self.driver.execute_write(
                query,
                nombre=estudiante.nombre.strip(),
                estilo_aprendizaje=estudiante.estilo_aprendizaje,
                estilo_clase=estudiante.estilo_clase,
                promedio=float(estudiante.promedio) if estudiante.promedio else 0.0,
                asistencias=int(estudiante.asistencias) if estudiante.asistencias else 0,
                veces_curso=int(estudiante.veces_curso) if estudiante.veces_curso else 0,
                puntuacion_total=puntuacion_total
            )
            
            if result:
                return {
                    "estudiante": result[0]["e"],
                    "accion": result[0]["accion"]
                }
            return {"error": "No se pudo registrar el estudiante"}
            
        except Exception as e:
            return {"error": f"Error en base de datos: {str(e)}"}
    
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

        #Criterios de similitud
        query = """
        MATCH (e:Estudiante {nombre: $nombre_estudiante})
        MATCH (similar:Estudiante)
        WHERE similar.nombre <> e.nombre
            AND similar.estilo_aprendizaje = e.estilo_aprendizaje
            AND similar.estilo_clase = e.estilo_clase
            AND abs(similar.veces_que_llevo_curso - e.veces_que_llevo_curso) <= $tolerancia_experiencia
            AND abs(similar.promedio - e.promedio) <= $tolerancia_promedio
        WITH similar, e,
             abs(similar.promedio - e.promedio) as diff_promedio,
             abs(similar.veces_que_llevo_curso - e.veces_que_llevo_curso) as diff_experiencia
        RETURN similar, 
               diff_promedio,
               diff_experiencia,
               (1.0 - (diff_promedio / $tolerancia_promedio)) * 0.6 + 
               (1.0 - (diff_experiencia / $tolerancia_experiencia)) * 0.4 as score_similitud
        ORDER BY score_similitud DESC
        """
        
        result = self.driver.execute_read(query, nombre_estudiante=nombre_estudiante)
        
        if result:
            return [record["similar"] for record in result]
        return []
