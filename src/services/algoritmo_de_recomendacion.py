from database.neo4jdriver import Neo4jDriver
from services.algoritmo_estudiante import AlgoritmoEstudiante
from services.algoritmo_profesor import AlgoritmoProfesor

class AlgoritmoRecomendacion:
    """Clase principal para ejecutar el algoritmo de recomendación de profesores"""
    
    def __init__(self):
        self.driver = Neo4jDriver()
        self.algoritmo_estudiante = AlgoritmoEstudiante()
        self.algoritmo_profesor = AlgoritmoProfesor()
    
    def recomendar_profesores(self, nombre_estudiante):
        """
        Recomienda profesores para un estudiante específico
        
        Args:
            nombre_estudiante: Nombre del estudiante
            
        Returns:
            list: Lista de recomendaciones de profesores ordenada por índice de compatibilidad
        """
        # Verificar si el estudiante existe
        estudiante = self.algoritmo_estudiante.obtener_estudiante(nombre_estudiante)
        if not estudiante:
            return {"error": f"No se encontró al estudiante con nombre {nombre_estudiante}"}
        
        # Encontrar profesores válidos (mismo estilo aprendizaje y clase)
        query_validaciones = """
        MATCH (e:Estudiante {nombre: $nombre_estudiante})
        MATCH (p:Profesor)
        WHERE p.estilo_enseñanza = e.estilo_aprendizaje 
            AND p.estilo_clase = e.estilo_clase
        RETURN p, e.puntuacion_total AS puntuacion_estudiante
        """
        
        profesores_validos = self.driver.execute_read(
            query_validaciones, 
            nombre_estudiante=nombre_estudiante
        )
        
        if not profesores_validos:
            return []
        
        recomendaciones = []
        for record in profesores_validos:
            profesor = record["p"]
            puntuacion_estudiante = record["puntuacion_estudiante"]
            
            # Calcular afinidad basada en estudiantes similares
            query_afinidad = """
            MATCH (e:Estudiante {nombre: $nombre_estudiante})
            OPTIONAL MATCH (similar:Estudiante)
            WHERE similar.nombre <> e.nombre
                AND similar.estilo_aprendizaje = e.estilo_aprendizaje
                AND similar.estilo_clase = e.estilo_clase
                AND abs(similar.veces_que_llevo_curso - e.veces_que_llevo_curso) <= 1
                AND abs(similar.promedio - e.promedio) <= 5
            OPTIONAL MATCH (similar)-[:APROBÓ_CON]->(c:Curso)<-[:IMPARTE]-(p:Profesor {nombre: $nombre_profesor})
            WITH count(DISTINCT similar) AS total_similares,
                 count(DISTINCT CASE WHEN similar IS NOT NULL THEN similar ELSE NULL END) AS similares_que_aprobaron
            RETURN similares_que_aprobaron, total_similares
            """
            
            afinidad_data = self.driver.execute_read(
                query_afinidad,
                nombre_estudiante=nombre_estudiante,
                nombre_profesor=profesor["nombre"]
            )
            
            if afinidad_data:
                data = afinidad_data[0]
                similares_que_aprobaron = data.get("similares_que_aprobaron", 0)
                total_similares = data.get("total_similares", 0)
                
                afinidad = (similares_que_aprobaron / total_similares * 100) if total_similares > 0 else 0
            else:
                afinidad = 0
            
            # Calcular índice de compatibilidad
            if total_similares > 0:
                indice = (0.3 * (puntuacion_estudiante / 20)) + \
                         (0.3 * (profesor["puntuacion_total"] / 20)) + \
                         (0.4 * (afinidad / 100))
            else:
                indice = (0.5 * (puntuacion_estudiante / 20)) + \
                         (0.5 * (profesor["puntuacion_total"] / 20))
            
            # Crear relación de recomendación en la base de datos
            self.driver.execute_write(
                """
                MATCH (e:Estudiante {nombre: $nombre_estudiante})
                MATCH (p:Profesor {nombre: $nombre_profesor})
                MERGE (e)-[r:RECOMENDADO]->(p)
                SET r.indice_compatibilidad = $indice,
                    r.fecha_recomendacion = datetime()
                """,
                nombre_estudiante=nombre_estudiante,
                nombre_profesor=profesor["nombre"],
                indice=indice
            )
            
            # Agregar a la lista de recomendaciones
            recomendaciones.append({
                "profesor": profesor["nombre"],
                "indice_compatibilidad": indice * 100,
                "puntuacion_estudiante": puntuacion_estudiante,
                "puntuacion_profesor": profesor["puntuacion_total"],
                "afinidad": afinidad
            })
        
        # Ordenar recomendaciones por índice de compatibilidad (de mayor a menor)
        return sorted(recomendaciones, key=lambda x: x["indice_compatibilidad"], reverse=True)
    
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
