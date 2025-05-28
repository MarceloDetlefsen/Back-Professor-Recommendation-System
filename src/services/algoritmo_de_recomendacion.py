from database.neo4jdriver import Neo4jDriver
from services.algoritmo_estudiante import AlgoritmoEstudiante
from services.algoritmo_profesor import AlgoritmoProfesor
import math

class AlgoritmoRecomendacion:
    """Clase mejorada para ejecutar el algoritmo de recomendación de profesores"""
    
    def __init__(self):
        self.driver = Neo4jDriver()
        self.algoritmo_estudiante = AlgoritmoEstudiante()
        self.algoritmo_profesor = AlgoritmoProfesor()
    
    def z(self, nombre_estudiante, codigo_curso=None):
        """
        Recomienda profesores para un estudiante específico, opcionalmente para un curso específico
        
        Args:
            nombre_estudiante: Nombre del estudiante
            codigo_curso: (Opcional) Código del curso para filtrar recomendaciones
            
        Returns:
            list: Lista de recomendaciones de profesores ordenada por índice de compatibilidad
        """
        # Verificar si el estudiante existe
        estudiante = self.algoritmo_estudiante.obtener_estudiante(nombre_estudiante)
        if not estudiante:
            return {"error": f"No se encontró al estudiante con nombre {nombre_estudiante}"}
        
        # Obtener profesores que imparten el curso específico (si se especifica)
        if codigo_curso:
            query_profesores = """
            MATCH (p:Profesor)-[:IMPARTE]->(c:Curso {codigo: $codigo_curso})
            RETURN p
            """
            profesores = self.driver.execute_read(query_profesores, codigo_curso=codigo_curso)
            if not profesores:
                return {"error": f"No hay profesores asignados al curso {codigo_curso}"}
        else:
            # Si no se especifica curso, obtener todos los profesores
            query_profesores = "MATCH (p:Profesor) RETURN p"
            profesores = self.driver.execute_read(query_profesores)
            if not profesores:
                return []

        recomendaciones = []
        
        for record in profesores:
            profesor = record["p"]
            
            # 1. Compatibilidad de estilos (40% peso)
            compatibilidad = self.calcular_compatibilidad_estilos(estudiante, profesor)
            
            # 2. Afinidad basada en estudiantes similares (30% peso)
            afinidad, confianza = self.calcular_afinidad(nombre_estudiante, profesor["nombre"])
            
            # 3. Calidad del profesor (20% peso)
            calidad_profesor = self.calcular_calidad_profesor(profesor)
            
            # 4. Rendimiento histórico del estudiante (10% peso)
            rendimiento_estudiante = self.calcular_rendimiento_estudiante(estudiante)
            
            # Calcular índice final con pesos
            indice = (
                0.4 * compatibilidad +
                0.3 * afinidad * confianza +
                0.2 * calidad_profesor +
                0.1 * rendimiento_estudiante
            )
            
            # Ajustar índice a escala 0-100
            indice_ajustado = min(100, max(0, indice * 100))
            
            # Crear relación de recomendación en la base de datos
            self.registrar_recomendacion(nombre_estudiante, profesor["nombre"], indice_ajustado)
            
            # Agregar a la lista de recomendaciones
            recomendaciones.append({
                "profesor": profesor["nombre"],
                "indice_compatibilidad": indice_ajustado,
                "factor_confianza": confianza * 100,
                "compatibilidad_estilos": compatibilidad * 100,
                "calidad_profesor": calidad_profesor * 100,
                "afinidad": afinidad * 100,
                "departamento": profesor.get("departamento", "N/A"),
                "evaluacion_docente": profesor.get("evaluacion_docente", 0),
                "porcentaje_aprobados": profesor.get("porcentaje_aprobados", 0),
                "años_experiencia": profesor.get("años_experiencia", 0),
                "estilo_enseñanza": profesor.get("estilo_enseñanza"),
                "estilo_clase": profesor.get("estilo_clase")
            })
        
        # Ordenar recomendaciones por índice de compatibilidad (de mayor a menor)
        return sorted(recomendaciones, key=lambda x: x["indice_compatibilidad"], reverse=True)
    
    def calcular_compatibilidad_estilos(self, estudiante, profesor):
        """Calcula la compatibilidad de estilos con escala gradual"""
        # Mapeo de compatibilidades entre estilos
        compatibilidad_aprendizaje = {
            'visual': {'visual': 1.0, 'auditivo': 0.7, 'kinestesico': 0.5},
            'auditivo': {'visual': 0.7, 'auditivo': 1.0, 'kinestesico': 0.6},
            'kinestesico': {'visual': 0.5, 'auditivo': 0.6, 'kinestesico': 1.0}
        }
        
        compatibilidad_clase = {
            'presencial': {'presencial': 1.0, 'virtual': 0.6, 'hibrido': 0.8},
            'virtual': {'presencial': 0.6, 'virtual': 1.0, 'hibrido': 0.9},
            'hibrido': {'presencial': 0.8, 'virtual': 0.9, 'hibrido': 1.0}
        }
        
        # Obtener valores con defaults razonables
        estilo_estudiante = estudiante.get("estilo_aprendizaje", "visual").lower()
        estilo_profesor = profesor.get("estilo_enseñanza", "visual").lower()
        clase_estudiante = estudiante.get("estilo_clase", "presencial").lower()
        clase_profesor = profesor.get("estilo_clase", "presencial").lower()
        
        # Calcular compatibilidades
        comp_aprendizaje = compatibilidad_aprendizaje.get(estilo_estudiante, {}).get(estilo_profesor, 0.5)
        comp_clase = compatibilidad_clase.get(clase_estudiante, {}).get(clase_profesor, 0.5)
        
        return (comp_aprendizaje * 0.6 + comp_clase * 0.4)  # Ponderación 60-40
    
    def calcular_afinidad(self, nombre_estudiante, nombre_profesor):
        """Calcula afinidad basada en estudiantes similares"""
        query = """
        MATCH (e:Estudiante {nombre: $nombre_estudiante})
        MATCH (similar:Estudiante)
        WHERE similar.nombre <> e.nombre
            AND similar.estilo_aprendizaje = e.estilo_aprendizaje
            AND similar.estilo_clase = e.estilo_clase
            AND abs(similar.promedio - e.promedio) <= 15
        OPTIONAL MATCH (similar)-[:APROBÓ_CON]->(c:Curso)<-[:IMPARTE]-(p:Profesor {nombre: $nombre_profesor})
        WITH count(DISTINCT similar) AS total_similares,
             count(DISTINCT CASE WHEN similar IS NOT NULL THEN c ELSE NULL END) AS cursos_aprobados
        RETURN 
            CASE 
                WHEN total_similares > 0 THEN cursos_aprobados/toFloat(total_similares)
                ELSE 0.5
            END AS afinidad,
            CASE
                WHEN total_similares >= 10 THEN 1.0
                WHEN total_similares >= 5 THEN 0.8
                WHEN total_similares >= 3 THEN 0.6
                WHEN total_similares > 0 THEN 0.4
                ELSE 0.2
            END AS confianza
        """
        
        result = self.driver.execute_read(
            query,
            nombre_estudiante=nombre_estudiante,
            nombre_profesor=nombre_profesor
        )
        
        if result:
            return result[0]["afinidad"], result[0]["confianza"]
        return 0.5, 0.2
    
    def calcular_calidad_profesor(self, profesor):
        """Calcula un índice de calidad del profesor normalizado a 0-1"""
        evaluacion = profesor.get("evaluacion_docente", 3.0) / 5.0  # Normalizar a 0-1
        aprobados = profesor.get("porcentaje_aprobados", 60) / 100.0  # Normalizar a 0-1
        experiencia = min(profesor.get("años_experiencia", 0), 30) / 30.0  # Normalizar a 0-1 con tope en 30 años
        
        return (evaluacion * 0.5 + aprobados * 0.3 + experiencia * 0.2)
    
    def calcular_rendimiento_estudiante(self, estudiante):
        """Calcula un índice de rendimiento del estudiante normalizado a 0-1"""
        promedio = estudiante.get("promedio", 70) / 100.0  # Normalizar a 0-1
        veces_curso = min(estudiante.get("veces_curso", 0), 3) / 3.0  # Normalizar a 0-1 con tope en 3 veces
        
        return (promedio * 0.7 + veces_curso * 0.3)
    
    def registrar_recomendacion(self, nombre_estudiante, nombre_profesor, indice):
        """Registra la recomendación en la base de datos"""
        self.driver.execute_write(
            """
            MATCH (e:Estudiante {nombre: $nombre_estudiante})
            MATCH (p:Profesor {nombre: $nombre_profesor})
            MERGE (e)-[r:RECOMENDADO]->(p)
            SET r.indice_compatibilidad = $indice,
                r.fecha_recomendacion = datetime()
            """,
            nombre_estudiante=nombre_estudiante,
            nombre_profesor=nombre_profesor,
            indice=indice
        )
    
    def registrar_aprobacion_curso(self, nombre_estudiante, nombre_profesor, codigo_curso):
        """
        Registra que un estudiante aprobó un curso con un profesor específico
        
        Args:
            nombre_estudiante: Nombre del estudiante
            nombre_profesor: Nombre del profesor
            codigo_curso: Código del curso
            
        Returns:
            bool: True si se registró correctamente, False en caso contrario
        """
        query = """
        MATCH (e:Estudiante {nombre: $nombre_estudiante})
        MATCH (p:Profesor {nombre: $nombre_profesor})
        MATCH (c:Curso {codigo: $codigo_curso})
        MERGE (e)-[r:APROBÓ_CON]->(c)
        MERGE (p)-[:IMPARTE]->(c)
        RETURN e, r, c
        """
        
        result = self.driver.execute_write(
            query,
            nombre_estudiante=nombre_estudiante,
            nombre_profesor=nombre_profesor,
            codigo_curso=codigo_curso
        )
        
        return len(result) > 0