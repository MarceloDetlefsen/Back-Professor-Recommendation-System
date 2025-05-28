from database.neo4jdriver import Neo4jDriver
from services.algoritmo_estudiante import AlgoritmoEstudiante
from services.algoritmo_profesor import AlgoritmoProfesor
import math
import random

class AlgoritmoRecomendacion:
    """Clase mejorada para ejecutar el algoritmo de recomendación de profesores con rangos amplios"""
    
    def __init__(self):
        self.driver = Neo4jDriver()
        self.algoritmo_estudiante = AlgoritmoEstudiante()
        self.algoritmo_profesor = AlgoritmoProfesor()
    
    def recomendar_profesores(self, nombre_estudiante, codigo_curso=None):
        """
        Recomienda profesores para un estudiante específico, opcionalmente para un curso específico
        """
        # Verificar si el estudiante existe
        estudiante = self.algoritmo_estudiante.obtener_estudiante(nombre_estudiante)
        if not estudiante:
            return {"error": f"No se encontró al estudiante con nombre {nombre_estudiante}"}
        
        print("taco")
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
            
            # 1. Compatibilidad de estilos (35% peso - reducido para dar más variabilidad)
            compatibilidad = self.calcular_compatibilidad_estilos(estudiante, profesor)
            
            # 2. Afinidad basada en estudiantes similares (25% peso)
            afinidad, confianza = self.calcular_afinidad(nombre_estudiante, profesor["nombre"])
            
            # 3. Calidad del profesor (25% peso - aumentado)
            calidad_profesor = self.calcular_calidad_profesor(profesor)
            
            # 4. Rendimiento histórico del estudiante (15% peso - aumentado)
            rendimiento_estudiante = self.calcular_rendimiento_estudiante(estudiante)
            
            # *** DEBUGGING: Verificar valores antes del cálculo ***
            print(f"DEBUG - Profesor: {profesor['nombre']}")
            print(f"  Compatibilidad: {compatibilidad:.3f}")
            print(f"  Afinidad: {afinidad:.3f}, Confianza: {confianza:.3f}")
            print(f"  Calidad: {calidad_profesor:.3f}, Rendimiento: {rendimiento_estudiante:.3f}")
            
            # NUEVO CÁLCULO CON MULTIPLICADORES Y BONIFICACIONES
            indice_base = (
                0.35 * compatibilidad +
                0.25 * (afinidad * 0.8 + confianza * 0.2) +
                0.25 * calidad_profesor +
                0.15 * rendimiento_estudiante
            )
            
            # APLICAR MULTIPLICADORES DINÁMICOS para ampliar rangos
            indice_final = self.aplicar_multiplicadores_dinamicos(
                indice_base, compatibilidad, afinidad, calidad_profesor, 
                rendimiento_estudiante, confianza
            )
            
            print(f"  Índice base: {indice_base:.3f}")
            print(f"  Índice final: {indice_final:.3f}")
            print(f"  Índice final * 100: {indice_final * 100:.3f}")
            print("---")
            
            # Permitir rangos amplios pero distribuidos suavemente
            indice_ajustado = max(5, min(95, indice_final * 100))
            
            # Crear relación de recomendación en la base de datos
            self.registrar_recomendacion(nombre_estudiante, profesor["nombre"], indice_ajustado)
            
            # Agregar a la lista de recomendaciones
            recomendaciones.append({
                "profesor": profesor["nombre"],
                "indice_compatibilidad": round(indice_ajustado, 2),
                "porcentaje_recomendacion": round(indice_ajustado, 2),
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
                "detalles_calculo": {
                    "compatibilidad_bruta": round(compatibilidad, 3),
                    "afinidad_bruta": round(afinidad, 3),
                    "confianza_bruta": round(confianza, 3),
                    "calidad_bruta": round(calidad_profesor, 3),
                    "rendimiento_bruta": round(rendimiento_estudiante, 3),
                    "indice_base": round(indice_base, 3),
                    "indice_con_multiplicadores": round(indice_final, 3)
                }
            })
        
        # Ordenar recomendaciones por índice de compatibilidad (de mayor a menor)
        return sorted(recomendaciones, key=lambda x: x["indice_compatibilidad"], reverse=True)
    
    def aplicar_multiplicadores_dinamicos(self, indice_base, compatibilidad, afinidad, 
                                        calidad_profesor, rendimiento_estudiante, confianza):
        """
        Aplica multiplicadores dinámicos SUAVIZADOS para mejor distribución
        """
        # Función auxiliar para curvas suaves
        def curva_suave(valor, punto_medio=0.5, intensidad=2.0):
            """Crea una curva sigmoidal suave"""
            import math
            return 1 / (1 + math.exp(-intensidad * (valor - punto_medio)))
        
        # BONIFICACIONES GRADUALES Y SUAVES
        # Sinergia entre compatibilidad y calidad (máximo +15%)
        sinergia_factor = (compatibilidad * calidad_profesor) ** 0.8
        bonif_sinergia = min(0.15, sinergia_factor * 0.2)
        
        # Confianza gradual (máximo +10%)
        bonif_confianza = min(0.1, confianza * 0.12)
        
        # Rendimiento combinado (máximo +12%)
        factor_rendimiento = (rendimiento_estudiante * afinidad) ** 0.7
        bonif_rendimiento = min(0.12, factor_rendimiento * 0.15)
        
        # PENALIZACIONES GRADUALES
        # Incompatibilidad suave
        if compatibilidad < 0.5:
            penalizacion_compat = 0.7 + (compatibilidad * 0.6)  # Entre 0.7 y 1.0
        else:
            penalizacion_compat = 1.0
        
        # Calidad baja suave  
        if calidad_profesor < 0.4:
            penalizacion_calidad = 0.8 + (calidad_profesor * 0.5)  # Entre 0.8 y 1.0
        else:
            penalizacion_calidad = 1.0
        
        # CÁLCULO FINAL MÁS SUAVE
        multiplicador_final = (1.0 + bonif_sinergia + bonif_confianza + bonif_rendimiento) * \
                             penalizacion_compat * penalizacion_calidad
        
        # Aplicar con curva logarítmica suave para evitar extremos
        resultado = indice_base * multiplicador_final
        
        # Función de mapeo suave que evita acumulación en extremos
        if resultado > 0.85:
            # Comprimir valores altos para evitar demasiados 100%
            resultado = 0.85 + (resultado - 0.85) * 0.4
        elif resultado < 0.2:
            # Elevar valores muy bajos para evitar demasiados cerca de 0
            resultado = 0.2 + (resultado - 0.2) * 0.6
        
        return max(0.05, min(1.0, resultado))
    
    def calcular_compatibilidad_estilos(self, estudiante, profesor):
        """
        Calcula la compatibilidad de estilos con rangos MUY amplios
        """
        compatibilidad_aprendizaje = {
            'mixto': {
                'mixto': 1.0,       # Perfecto match
                'teorico': 0.75,    # Buena compatibilidad
                'practico': 0.75    # Buena compatibilidad
            },
            'teorico': {
                'teorico': 1.0,     # Perfecto match
                'mixto': 0.8,       # Muy buena compatibilidad
                'practico': 0.15    # MUY baja compatibilidad (era 0.4)
            },
            'practico': {
                'practico': 1.0,    # Perfecto match
                'mixto': 0.8,       # Muy buena compatibilidad
                'teorico': 0.15     # MUY baja compatibilidad (era 0.4)
            }
        }
        
        compatibilidad_clase = {
            'con_tecnologia': {
                'con_tecnologia': 1.0,   # Perfecto match
                'mixto': 0.85,           # Buena compatibilidad
                'sin_tecnologia': 0.1    # EXTREMADAMENTE baja (era 0.3)
            },
            'sin_tecnologia': {
                'sin_tecnologia': 1.0,   # Perfecto match
                'mixto': 0.85,           # Buena compatibilidad
                'con_tecnologia': 0.1    # EXTREMADAMENTE baja (era 0.3)
            },
            'mixto': {
                'mixto': 1.0,            # Perfecto match
                'con_tecnologia': 0.9,   # Excelente compatibilidad
                'sin_tecnologia': 0.9    # Excelente compatibilidad
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
        
        # Ponderación: 70% estilo de aprendizaje, 30% estilo de clase (más peso al aprendizaje)
        compatibilidad_final = (comp_aprendizaje * 0.7 + comp_clase * 0.3)
        
        return compatibilidad_final
    
    def calcular_afinidad(self, nombre_estudiante, nombre_profesor):
        """
        Calcula afinidad con distribución mejorada y manejo robusto de errores
        """
        try:
            print(f"Calculando afinidad para {nombre_estudiante} -> {nombre_profesor}")
            
            # Consulta simplificada con criterios graduales
            query = """
            MATCH (e:Estudiante {nombre: $nombre_estudiante})
            
            // Buscar estudiantes similares con criterios flexibles
            OPTIONAL MATCH (similar:Estudiante)
            WHERE similar.nombre <> e.nombre
                AND (
                    // Criterio 1: Mismo estilo de aprendizaje
                    similar.estilo_aprendizaje = e.estilo_aprendizaje
                    OR
                    // Criterio 2: Estilos compatibles (incluye mixto)
                    (similar.estilo_aprendizaje = 'mixto' OR e.estilo_aprendizaje = 'mixto')
                    OR
                    // Criterio 3: Mismo estilo de clase
                    similar.estilo_clase = e.estilo_clase
                    OR
                    // Criterio 4: Promedio similar (rango amplio)
                    abs(similar.promedio - e.promedio) <= 30
                )
            
            // Buscar éxitos de estudiantes similares con este profesor
            OPTIONAL MATCH (similar)-[:APROBÓ_CON]->(c:Curso)<-[:IMPARTE]-(p:Profesor {nombre: $nombre_profesor})
            
            WITH 
                count(DISTINCT similar) AS total_similares,
                count(DISTINCT CASE WHEN c IS NOT NULL THEN similar ELSE NULL END) AS estudiantes_exitosos,
                e.promedio as promedio_estudiante,
                e.estilo_aprendizaje as estilo_estudiante,
                e.estilo_clase as clase_estudiante
            
            RETURN 
                total_similares,
                estudiantes_exitosos,
                promedio_estudiante,
                estilo_estudiante,
                clase_estudiante,
                CASE 
                    WHEN total_similares > 0 THEN toFloat(estudiantes_exitosos) / toFloat(total_similares)
                    ELSE 0.0
                END AS ratio_exito
            """
            
            result = self.driver.execute_read(
                query,
                nombre_estudiante=nombre_estudiante,
                nombre_profesor=nombre_profesor
            )
            
            if not result or len(result) == 0:
                print("No se encontraron datos, usando fallback")
                return self.calcular_afinidad_fallback(nombre_profesor), 0.1
            
            record = result[0]
            total_similares = record.get("total_similares", 0) or 0
            estudiantes_exitosos = record.get("estudiantes_exitosos", 0) or 0
            ratio_exito = float(record.get("ratio_exito", 0.0) or 0.0)
            
            print(f"  Similares encontrados: {total_similares}")
            print(f"  Estudiantes exitosos: {estudiantes_exitosos}")
            print(f"  Ratio de éxito: {ratio_exito:.3f}")
            
            # Calcular afinidad con lógica graduada
            if total_similares >= 5:
                # Alta confianza: usar ratio de éxito con ajustes
                afinidad_base = 0.25 + (ratio_exito * 0.65)
                confianza = min(0.9, 0.6 + (total_similares * 0.02))
            elif total_similares > 0:
                # Confianza media: usar ratio con más cautela
                afinidad_base = 0.35 + (ratio_exito * 0.45)
                confianza = 0.3 + (total_similares * 0.1)
            else:
                # Sin datos: usar características del profesor
                print("  Sin estudiantes similares, usando fallback")
                return self.calcular_afinidad_fallback(nombre_profesor), 0.15
            
            # Aplicar suavizado para distribución natural
            afinidad_final = self.suavizar_afinidad_simple(afinidad_base, confianza)
            
            print(f"  Afinidad calculada: {afinidad_final:.3f}")
            print(f"  Confianza: {confianza:.3f}")
            
            return afinidad_final, confianza
            
        except Exception as e:
            print(f"ERROR en calcular_afinidad: {str(e)}")
            print(f"Tipo de error: {type(e).__name__}")
            # En caso de error, usar fallback seguro
            return 0.5, 0.2
    
    def calcular_calidad_profesor(self, profesor):
        """
        Calcula un índice de calidad del profesor con CURVAS SUAVES
        """
        # Obtener valores con validaciones
        evaluacion = float(profesor.get("evaluacion_docente", 3.0))
        aprobados = float(profesor.get("porcentaje_aprobados", 60))
        experiencia = float(profesor.get("años_experiencia", 0))
        
        # NORMALIZACIÓN CON CURVAS SUAVES (no escalonadas)
        # Evaluación docente con curva suave
        evaluacion_norm = max(0.05, min(1.0, (evaluacion - 1.0) / 4.0))
        # Aplicar curva sigmoidal para suavizar
        evaluacion_norm = evaluacion_norm ** 1.2  # Curva ligeramente exponencial
        
        # Porcentaje de aprobados con curva suave
        aprobados_norm = max(0.05, min(1.0, aprobados / 100.0))
        # Curva que favorece valores altos pero no extrema
        if aprobados_norm > 0.6:
            aprobados_norm = 0.6 + (aprobados_norm - 0.6) * 1.5
        aprobados_norm = min(1.0, aprobados_norm)
        
        # Experiencia con curva logarítmica suave
        experiencia_norm = max(0.1, min(1.0, math.log(experiencia + 1) / math.log(26)))
        
        # Pesos balanceados
        calidad = (evaluacion_norm * 0.5 + aprobados_norm * 0.35 + experiencia_norm * 0.15)
        
        return max(0.05, min(1.0, calidad))
    
    def calcular_rendimiento_estudiante(self, estudiante):
        """
        Calcula un índice de rendimiento del estudiante con CURVAS SUAVES
        """
        # Obtener valores con validaciones
        promedio = float(estudiante.get("promedio", 70))
        veces_curso = int(estudiante.get("veces_que_llevo_curso", 0))
        
        # NORMALIZACIÓN SUAVE del promedio (no escalonada)
        promedio_norm = max(0.05, min(1.0, promedio / 100.0))
        
        # Aplicar curva que favorece promedios altos pero suavemente
        if promedio_norm > 0.7:
            # Amplificar ligeramente los promedios altos
            promedio_norm = 0.7 + (promedio_norm - 0.7) * 1.3
        elif promedio_norm < 0.6:
            # Penalizar suavemente los promedios bajos
            promedio_norm = promedio_norm * 0.8
        
        promedio_norm = max(0.05, min(1.0, promedio_norm))
        
        # Penalización SUAVE por repetir curso (curva exponencial suave)
        veces_norm = max(0.1, 1.0 / (1.0 + veces_curso * 0.8))
        
        # Combinar métricas: 75% promedio, 25% historial
        rendimiento = (promedio_norm * 0.75 + veces_norm * 0.25)
        
        return max(0.05, min(1.0, rendimiento))
    
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
    
    def suavizar_afinidad_simple(self, afinidad_base, confianza):
        """
        Suavizado simple sin dependencias externas complejas
        """
        try:
            variacion_seed = hash(f"{afinidad_base}_{confianza}") % 100
            variacion = (variacion_seed / 100.0 - 0.5) * 0.15  # -0.075 a +0.075
            
            if confianza > 0.7:
                variacion *= 0.5  # Reducir variación con alta confianza
            elif confianza < 0.3:
                variacion *= 1.5  # Aumentar variación con baja confianza
            
            afinidad_ajustada = afinidad_base + variacion
            
            # Aplicar curva suave para evitar extremos
            if afinidad_ajustada > 0.85:
                afinidad_ajustada = 0.85 + (afinidad_ajustada - 0.85) * 0.4
            elif afinidad_ajustada < 0.15:
                afinidad_ajustada = 0.15 + (afinidad_ajustada - 0.15) * 0.6
            
            return max(0.1, min(0.95, afinidad_ajustada))
            
        except Exception as e:
            print(f"Error en suavizado: {e}")
            return max(0.1, min(0.95, afinidad_base))

    def calcular_afinidad_fallback(self, nombre_profesor):
        """
        Fallback robusto basado en características del profesor
        """
        try:
            query = """
            MATCH (p:Profesor {nombre: $nombre_profesor})
            RETURN 
                coalesce(p.evaluacion_docente, 3.0) as eval,
                coalesce(p.porcentaje_aprobados, 60.0) as aprobados,
                coalesce(p.años_experiencia, 5.0) as experiencia
            """
            
            result = self.driver.execute_read(query, nombre_profesor=nombre_profesor)
            
            if result and len(result) > 0:
                record = result[0]
                eval_docente = float(record.get("eval", 3.0))
                aprobados = float(record.get("aprobados", 60.0))
                experiencia = float(record.get("experiencia", 5.0))
                
                print(f"  Fallback - Eval: {eval_docente}, Aprobados: {aprobados}%, Exp: {experiencia}")
                
                # Normalizar métricas
                eval_norm = max(0.2, min(0.8, (eval_docente - 1.0) / 4.0))
                aprobados_norm = max(0.2, min(0.8, aprobados / 100.0))
                exp_norm = max(0.3, min(0.7, min(experiencia / 20.0, 1.0)))
                
                # Calcular afinidad base
                afinidad_base = (eval_norm * 0.4 + aprobados_norm * 0.4 + exp_norm * 0.2)
                
                # Agregar variabilidad determinística basada en el nombre del profesor
                variacion_seed = hash(nombre_profesor) % 100
                variacion = (variacion_seed / 100.0 - 0.5) * 0.2  # -0.1 a +0.1
                
                afinidad_final = afinidad_base + variacion
                
                return max(0.25, min(0.75, afinidad_final))
            
        except Exception as e:
            print(f"Error en fallback: {e}")
        
        # Último recurso: valor determinístico basado en hash del nombre
        fallback_seed = hash(nombre_profesor) % 100
        return 0.4 + (fallback_seed / 100.0) * 0.3  # Entre 0.4 y 0.7
        