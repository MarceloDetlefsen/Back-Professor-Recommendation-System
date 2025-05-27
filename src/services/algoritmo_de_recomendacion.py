from database.neo4jdriver import Neo4jDriver
from services.algoritmo_estudiante import AlgoritmoEstudiante
from services.algoritmo_profesor import AlgoritmoProfesor
import math 

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
        RETURN p, e.puntuacion_total AS puntuacion_estudiante, e.promedio AS promedio_estudiante, 
               e.veces_que_llevo_curso AS experiencia_estudiante,
               e.estilo_aprendizaje AS est_aprendizaje, e.estilo_clase AS est_clase
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

            #factor de compatibilidad de estilos
            est_aprendizaje = record["est_aprendizaje"]
            est_clase = record["est_clase"]
            prof_enseñanza = profesor["estilo_enseñanza"]
            prof_clase = profesor["estilo_clase"]

            #compatibilidad de estilos
            compatibilidad_aprendizaje = 1.0 if est_aprendizaje == prof_enseñanza else 0.6
            compatibilidad_clase = 1.0 if est_clase == prof_clase else 0.7
            factor_compatibilidad = (compatibilidad_aprendizaje + compatibilidad_clase) / 2.0
            
            # Calcular afinidad basada en estudiantes similares
            query_afinidad = """
            MATCH (e:Estudiante {nombre: $nombre_estudiante})
            OPTIONAL MATCH (similar:Estudiante)
            WHERE similar.nombre <> e.nombre
                AND similar.estilo_aprendizaje = e.estilo_aprendizaje
                AND similar.estilo_clase = e.estilo_clase
                AND abs(similar.veces_que_llevo_curso - e.veces_que_llevo_curso) <= 2
                AND abs(similar.promedio - e.promedio) <= 15
            OPTIONAL MATCH (similar)-[:APROBÓ_CON]->(c:Curso)<-[:IMPARTE]-(p:Profesor {nombre: $nombre_profesor})
            WITH count(DISTINCT similar) AS total_similares,
                 count(DISTINCT CASE WHEN similar IS NOT NULL THEN similar ELSE NULL END) AS similares_que_aprobaron
            RETURN COALESCE(similares_que_aprobaron, 0) AS similares_que_aprobaron, 
                   COALESCE(total_similares, 0) AS total_similares
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

                if total_similares > 0:
                    afinidad = (similares_que_aprobaron / total_similares)
                    confianza_afinidad = min(1.0, total_similares / 10.0)  # Más muestras = más confianza
                else:
                    afinidad = 0.5  # Valor neutro cuando no hay datos
                    confianza_afinidad = 0.0 
            else:
                afinidad = 0.5
                confianza_afinidad = 0.0

            #Pesos dinámicos usando la confianza de los datos
            peso_estudiante = 0.30
            peso_profesor = 0.30
            peso_afinidad = 0.25 * confianza_afinidad
            peso_compatibilidad = 0.15
            peso_restante = 1.0 - (peso_estudiante + peso_profesor + peso_afinidad)
            # el peso restante distribuido 50/50 entre estudiante y profesor jijiji
            peso_estudiante += peso_restante * 0.5
            peso_profesor += peso_restante * 0.5

            #Normalización a escala 0-1 pa que se pueda comparar todos los valores sin miedo
            puntuacion_estudiante_norm = min(1.0, puntuacion_estudiante / 20.0)
            puntuacion_profesor_norm = min(1.0, profesor["puntuacion_total"] / 20.0)
            
            # Calcular índice de compatibilidad pero ahora sí con pesos dinámicos

            indice = (peso_estudiante * puntuacion_estudiante_norm) + \
                     (peso_profesor * puntuacion_profesor_norm) + \
                     (peso_afinidad * afinidad) + \
                     (peso_compatibilidad * factor_compatibilidad)
            
            # Factor de confianza para mostrar al usuario
            factor_confianza = (confianza_afinidad * 0.6) + 0.4  # mínimo de 40% por si acaso
            
            # Crear relación de recomendación en la base de datos
            self.driver.execute_write(
                """
                MATCH (e:Estudiante {nombre: $nombre_estudiante})
                MATCH (p:Profesor {nombre: $nombre_profesor})
                MERGE (e)-[r:RECOMENDADO]->(p)
                SET r.indice_compatibilidad = $indice,
                    r.factor_confianza = $factor_confianza,
                    r.fecha_recomendacion = datetime()
                """,
                nombre_estudiante=nombre_estudiante,
                nombre_profesor=profesor["nombre"],
                indice=indice,
                factor_confianza=factor_confianza
            )
            
            # Agregar a la lista de recomendaciones
            recomendaciones.append({
                "profesor": profesor["nombre"],
                "indice_compatibilidad": indice * 100,
                "factor_confianza": factor_confianza * 100,
                "puntuacion_estudiante": puntuacion_estudiante,
                "puntuacion_profesor": profesor["puntuacion_total"],
                "afinidad": afinidad * 100,
                "compatibilidad_estilos": factor_compatibilidad * 100
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
