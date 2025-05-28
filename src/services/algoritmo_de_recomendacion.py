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
    
    def recomendar_profesores(self, nombre_estudiante, codigo_curso=None):
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
                "indice_compatibilidad": round(indice_ajustado, 2),
                "porcentaje_recomendacion": round(indice_ajustado, 2),  # Campo para el frontend
                "factor_confianza": round(confianza * 100, 2),
                "compatibilidad_estilos": round(compatibilidad * 100, 2),
                "calidad_profesor": round(calidad_profesor * 100, 2),
                "afinidad": round(afinidad * 100, 2),
                "departamento": profesor.get("departamento", "N/A"),
                "evaluacion_docente": profesor.get("evaluacion_docente", 3.0),
                "porcentaje_aprobados": profesor.get("porcentaje_aprobados", 60),
                "años_experiencia": profesor.get("años_experiencia", 0),
                "estilo_enseñanza": profesor.get("estilo_enseñanza", "mixto"),
                "estilo_clase": profesor.get("estilo_clase", "mixto"),
                # Detalles adicionales para debugging
                "detalles_calculo": {
                    "compatibilidad_bruta": round(compatibilidad, 3),
                    "afinidad_bruta": round(afinidad, 3),
                    "confianza_bruta": round(confianza, 3),
                    "calidad_bruta": round(calidad_profesor, 3),
                    "rendimiento_bruta": round(rendimiento_estudiante, 3)
                }
            })
        
        # Ordenar recomendaciones por índice de compatibilidad (de mayor a menor)
        return sorted(recomendaciones, key=lambda x: x["indice_compatibilidad"], reverse=True)
    
    def calcular_compatibilidad_estilos(self, estudiante, profesor):
        """
        Calcula la compatibilidad de estilos con escala gradual y valores corregidos
        """
        # Mapeo de compatibilidades entre estilos de aprendizaje/enseñanza
        compatibilidad_aprendizaje = {
            'mixto': {
                'mixto': 1.0,      # Perfecto match
                'teorico': 0.8,    # Muy buena compatibilidad  
                'practico': 0.8    # Muy buena compatibilidad
            },
            'teorico': {
                'teorico': 1.0,    # Perfecto match
                'mixto': 0.8,      # Muy buena compatibilidad
                'practico': 0.4    # Baja compatibilidad
            },
            'practico': {
                'practico': 1.0,   # Perfecto match
                'mixto': 0.8,      # Muy buena compatibilidad
                'teorico': 0.4     # Baja compatibilidad
            }
        }
        
        # Mapeo de compatibilidades entre estilos de clase
        compatibilidad_clase = {
            'con_tecnologia': {
                'con_tecnologia': 1.0,  # Perfecto match
                'mixto': 0.9,           # Excelente compatibilidad
                'sin_tecnologia': 0.3   # Baja compatibilidad
            },
            'sin_tecnologia': {
                'sin_tecnologia': 1.0,  # Perfecto match
                'mixto': 0.9,           # Excelente compatibilidad
                'con_tecnologia': 0.3   # Baja compatibilidad
            },
            'mixto': {
                'mixto': 1.0,           # Perfecto match
                'con_tecnologia': 0.9,  # Excelente compatibilidad
                'sin_tecnologia': 0.9   # Excelente compatibilidad
            }
        }
        
        # Obtener valores con defaults y normalizar a minúsculas
        estilo_estudiante = str(estudiante.get("estilo_aprendizaje", "mixto")).lower().strip()
        estilo_profesor = str(profesor.get("estilo_enseñanza", "mixto")).lower().strip()
        clase_estudiante = str(estudiante.get("estilo_clase", "mixto")).lower().strip()
        clase_profesor = str(profesor.get("estilo_clase", "mixto")).lower().strip()
        
        # Validar que los estilos sean válidos
        estilos_validos_aprendizaje = ['mixto', 'teorico', 'practico']
        estilos_validos_clase = ['con_tecnologia', 'sin_tecnologia', 'mixto']
        
        if estilo_estudiante not in estilos_validos_aprendizaje:
            estilo_estudiante = 'mixto'
        if estilo_profesor not in estilos_validos_aprendizaje:
            estilo_profesor = 'mixto'
        if clase_estudiante not in estilos_validos_clase:
            clase_estudiante = 'mixto'
        if clase_profesor not in estilos_validos_clase:
            clase_profesor = 'mixto'
        
        # Calcular compatibilidades
        comp_aprendizaje = compatibilidad_aprendizaje[estilo_estudiante][estilo_profesor]
        comp_clase = compatibilidad_clase[clase_estudiante][clase_profesor]
        
        # Ponderación: 60% estilo de aprendizaje, 40% estilo de clase
        compatibilidad_final = (comp_aprendizaje * 0.6 + comp_clase * 0.4)
        
        return compatibilidad_final
    
    def calcular_afinidad(self, nombre_estudiante, nombre_profesor):
        """
        Calcula afinidad basada en estudiantes similares con mejor tolerancia
        """
        query = """
        MATCH (e:Estudiante {nombre: $nombre_estudiante})
        MATCH (similar:Estudiante)
        WHERE similar.nombre <> e.nombre
            AND similar.estilo_aprendizaje = e.estilo_aprendizaje
            AND similar.estilo_clase = e.estilo_clase
            AND abs(similar.promedio - e.promedio) <= 20
        OPTIONAL MATCH (similar)-[:APROBÓ_CON]->(c:Curso)<-[:IMPARTE]-(p:Profesor {nombre: $nombre_profesor})
        WITH count(DISTINCT similar) AS total_similares,
             count(DISTINCT CASE WHEN c IS NOT NULL THEN c ELSE NULL END) AS cursos_aprobados
        RETURN 
            CASE 
                WHEN total_similares > 0 THEN toFloat(cursos_aprobados)/toFloat(total_similares)
                ELSE 0.5
            END AS afinidad,
            CASE
                WHEN total_similares >= 15 THEN 1.0
                WHEN total_similares >= 10 THEN 0.9
                WHEN total_similares >= 5 THEN 0.7
                WHEN total_similares >= 3 THEN 0.5
                WHEN total_similares > 0 THEN 0.3
                ELSE 0.1
            END AS confianza
        """
        
        result = self.driver.execute_read(
            query,
            nombre_estudiante=nombre_estudiante,
            nombre_profesor=nombre_profesor
        )
        
        if result and len(result) > 0:
            return float(result[0]["afinidad"]), float(result[0]["confianza"])
        return 0.5, 0.1
    
    def calcular_calidad_profesor(self, profesor):
        """
        Calcula un índice de calidad del profesor normalizado a 0-1 con validaciones
        """
        # Obtener valores con validaciones
        evaluacion = float(profesor.get("evaluacion_docente", 3.0))
        aprobados = float(profesor.get("porcentaje_aprobados", 60))
        experiencia = float(profesor.get("años_experiencia", 0))
        
        # Normalizar evaluación docente (escala 1-5 a 0-1)
        evaluacion_norm = max(0, min(1, (evaluacion - 1) / 4.0))
        
        # Normalizar porcentaje de aprobados (0-100 a 0-1)
        aprobados_norm = max(0, min(1, aprobados / 100.0))
        
        # Normalizar experiencia (tope en 25 años)
        experiencia_norm = max(0, min(1, experiencia / 25.0))
        
        # Calcular índice final con pesos ajustados
        calidad = (evaluacion_norm * 0.5 + aprobados_norm * 0.3 + experiencia_norm * 0.2)
        
        return calidad
    
    def calcular_rendimiento_estudiante(self, estudiante):
        """
        Calcula un índice de rendimiento del estudiante normalizado a 0-1
        """
        # Obtener valores con validaciones
        promedio = float(estudiante.get("promedio", 70))
        veces_curso = int(estudiante.get("veces_que_llevo_curso", 0))
        
        # Normalizar promedio (0-100 a 0-1)
        promedio_norm = max(0, min(1, promedio / 100.0))
        
        # Penalización por repetir curso (menos veces es mejor)
        # 0 veces = 1.0, 1 vez = 0.7, 2 veces = 0.4, 3+ veces = 0.1
        if veces_curso == 0:
            veces_norm = 1.0
        elif veces_curso == 1:
            veces_norm = 0.7
        elif veces_curso == 2:
            veces_norm = 0.4
        else:
            veces_norm = 0.1
        
        # Combinar métricas: 80% promedio, 20% historial de repetición
        rendimiento = (promedio_norm * 0.8 + veces_norm * 0.2)
        
        return rendimiento
    
    def registrar_recomendacion(self, nombre_estudiante, nombre_profesor, indice):
        """Registra la recomendación en la base de datos"""
        try:
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
        except Exception as e:
            print(f"Error al registrar recomendación: {e}")
    
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
        try:
            query = """
            MATCH (e:Estudiante {nombre: $nombre_estudiante})
            MATCH (p:Profesor {nombre: $nombre_profesor})
            MATCH (c:Curso {codigo: $codigo_curso})
            MERGE (e)-[r:APROBÓ_CON]->(c)
            SET r.fecha_aprobacion = datetime()
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
        except Exception as e:
            print(f"Error al registrar aprobación: {e}")
            return False
    
    def obtener_estadisticas_algoritmo(self, nombre_estudiante):
        """
        Obtiene estadísticas del algoritmo para debugging y análisis
        
        Args:
            nombre_estudiante: Nombre del estudiante
            
        Returns:
            dict: Estadísticas del algoritmo
        """
        query = """
        MATCH (e:Estudiante {nombre: $nombre_estudiante})
        OPTIONAL MATCH (e)-[r:RECOMENDADO]->(p:Profesor)
        OPTIONAL MATCH (similar:Estudiante)
        WHERE similar.nombre <> e.nombre
            AND similar.estilo_aprendizaje = e.estilo_aprendizaje
            AND similar.estilo_clase = e.estilo_clase
            AND abs(similar.promedio - e.promedio) <= 20
        RETURN 
            e,
            count(DISTINCT r) as total_recomendaciones,
            count(DISTINCT similar) as estudiantes_similares,
            avg(r.indice_compatibilidad) as promedio_compatibilidad
        """
        
        result = self.driver.execute_read(query, nombre_estudiante=nombre_estudiante)
        
        if result and len(result) > 0:
            record = result[0]
            return {
                "estudiante": record["e"],
                "total_recomendaciones": record["total_recomendaciones"] or 0,
                "estudiantes_similares": record["estudiantes_similares"] or 0,
                "promedio_compatibilidad": round(float(record["promedio_compatibilidad"] or 0), 2)
            }
        
        return {
            "error": f"No se encontró información para el estudiante {nombre_estudiante}"
        }