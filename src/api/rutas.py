from database.neo4jdriver import Neo4jDriver
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from services.algoritmo_de_recomendacion import AlgoritmoRecomendacion
from utils.helpers import create_response

router = APIRouter()

@router.get("/recomendaciones/{nombre_estudiante}")
async def obtener_recomendaciones(
    nombre_estudiante: str,
    curso: Optional[str] = Query(None, description="Código del curso para filtrar recomendaciones"),
    limite: Optional[int] = Query(None, description="Número máximo de recomendaciones a devolver"),
    incluir_detalles: Optional[bool] = Query(False, description="Incluir detalles del cálculo")
):
    """
    Obtiene recomendaciones de profesores para un estudiante específico
    
    Args:
        nombre_estudiante: Nombre del estudiante
        curso: Código del curso para filtrar recomendaciones
        limite: Número máximo de recomendaciones a devolver
        incluir_detalles: Si incluir detalles del cálculo para debugging
        
    Returns:
        Lista de recomendaciones de profesores ordenadas por compatibilidad
    """
    try:
        algoritmo = AlgoritmoRecomendacion()
        recomendaciones = algoritmo.recomendar_profesores(nombre_estudiante, codigo_curso=curso)
        
        if isinstance(recomendaciones, dict) and "error" in recomendaciones:
            raise HTTPException(status_code=404, detail=recomendaciones["error"])
        
        # Aplicar límite si se especifica
        if limite is not None and limite > 0:
            recomendaciones = recomendaciones[:limite]
        
        # Remover detalles si no se solicitan
        if not incluir_detalles:
            for rec in recomendaciones:
                rec.pop('detalles_calculo', None)
        
        # Preparar respuesta con metadatos adicionales
        respuesta_data = {
            "recomendaciones": recomendaciones,
            "metadatos": {
                "total_encontradas": len(recomendaciones),
                "estudiante": nombre_estudiante,
                "curso_filtrado": curso,
                "limite_aplicado": limite,
                "mejor_compatibilidad": recomendaciones[0]["porcentaje_recomendacion"] if recomendaciones else 0,
                "promedio_compatibilidad": round(
                    sum(r["porcentaje_recomendacion"] for r in recomendaciones) / len(recomendaciones), 2
                ) if recomendaciones else 0
            }
        }
            
        return create_response(
            data=respuesta_data,
            message=f"Se encontraron {len(recomendaciones)} recomendaciones para {nombre_estudiante}" + 
                   (f" en el curso {curso}" if curso else "")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener recomendaciones: {str(e)}")

@router.get("/recomendacion/{nombre_estudiante}/{nombre_profesor}")
async def obtener_recomendacion_especifica(
    nombre_estudiante: str,
    nombre_profesor: str
):
    """
    Obtiene la recomendación específica entre un estudiante y un profesor
    
    Args:
        nombre_estudiante: Nombre del estudiante
        nombre_profesor: Nombre del profesor
        
    Returns:
        Recomendación específica con porcentaje de compatibilidad
    """
    try:
        algoritmo = AlgoritmoRecomendacion()
        recomendaciones = algoritmo.recomendar_profesores(nombre_estudiante)
        
        if isinstance(recomendaciones, dict) and "error" in recomendaciones:
            raise HTTPException(status_code=404, detail=recomendaciones["error"])
        
        # Buscar la recomendación específica
        recomendacion_especifica = None
        for rec in recomendaciones:
            if rec["profesor"].lower() == nombre_profesor.lower():
                recomendacion_especifica = rec
                break
        
        if not recomendacion_especifica:
            raise HTTPException(
                status_code=404, 
                detail=f"No se encontró recomendación entre {nombre_estudiante} y {nombre_profesor}"
            )
        
        return create_response(
            data=recomendacion_especifica,
            message=f"Compatibilidad entre {nombre_estudiante} y {nombre_profesor}: {recomendacion_especifica['porcentaje_recomendacion']}%"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener recomendación específica: {str(e)}")

@router.post("/aprobacion")
async def registrar_aprobacion(
    nombre_estudiante: str,
    nombre_profesor: str,
    codigo_curso: str
):
    """
    Registra que un estudiante aprobó un curso con un profesor específico
    
    Args:
        nombre_estudiante: Nombre del estudiante
        nombre_profesor: Nombre del profesor
        codigo_curso: Código del curso
        
    Returns:
        Confirmación del registro
    """
    try:
        algoritmo = AlgoritmoRecomendacion()
        resultado = algoritmo.registrar_aprobacion_curso(
            nombre_estudiante=nombre_estudiante,
            nombre_profesor=nombre_profesor,
            codigo_curso=codigo_curso
        )
        
        if resultado:
            return create_response(
                data={
                    "estudiante": nombre_estudiante,
                    "profesor": nombre_profesor,
                    "curso": codigo_curso,
                    "fecha_registro": "registrado"
                },
                message=f"Se registró correctamente que {nombre_estudiante} aprobó el curso {codigo_curso} con {nombre_profesor}"
            )
        else:
            raise HTTPException(status_code=400, detail="No se pudo registrar la aprobación")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar aprobación: {str(e)}")

@router.get("/estadisticas/{nombre_estudiante}")
async def obtener_estadisticas_estudiante(nombre_estudiante: str):
    """
    Obtiene estadísticas del algoritmo para un estudiante específico
    
    Args:
        nombre_estudiante: Nombre del estudiante
        
    Returns:
        Estadísticas del algoritmo para el estudiante
    """
    try:
        algoritmo = AlgoritmoRecomendacion()
        estadisticas = algoritmo.obtener_estadisticas_algoritmo(nombre_estudiante)
        
        if "error" in estadisticas:
            raise HTTPException(status_code=404, detail=estadisticas["error"])
            
        return create_response(
            data=estadisticas,
            message=f"Estadísticas obtenidas para {nombre_estudiante}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")

@router.get("/porcentaje/{nombre_estudiante}/{nombre_profesor}")
async def obtener_porcentaje_recomendacion(
    nombre_estudiante: str,
    nombre_profesor: str
):
    """
    Obtiene solo el porcentaje de recomendación entre un estudiante y profesor
    Endpoint específico para el frontend que necesita solo el número
    
    Args:
        nombre_estudiante: Nombre del estudiante
        nombre_profesor: Nombre del profesor
        
    Returns:
        Porcentaje de recomendación como número
    """
    try:
        algoritmo = AlgoritmoRecomendacion()
        recomendaciones = algoritmo.recomendar_profesores(nombre_estudiante)
        
        if isinstance(recomendaciones, dict) and "error" in recomendaciones:
            raise HTTPException(status_code=404, detail=recomendaciones["error"])
        
        # Buscar la recomendación específica
        for rec in recomendaciones:
            if rec["profesor"].lower() == nombre_profesor.lower():
                return create_response(
                    data={
                        "porcentaje": rec["porcentaje_recomendacion"],
                        "estudiante": nombre_estudiante,
                        "profesor": nombre_profesor
                    },
                    message=f"Porcentaje de recomendación: {rec['porcentaje_recomendacion']}%"
                )
        
        raise HTTPException(
            status_code=404, 
            detail=f"No se encontró recomendación entre {nombre_estudiante} y {nombre_profesor}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener porcentaje: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Verifica el estado de la API y del algoritmo de recomendación
    
    Returns:
        Estado de la API y componentes
    """
    try:
        # Verificar conexión con Neo4j
        driver = Neo4jDriver()
        connection_test = driver.execute_read("RETURN 1 as test")
        
        # Verificar algoritmo
        algoritmo = AlgoritmoRecomendacion()
        
        return create_response(
            data={
                "database": "conectada" if connection_test else "desconectada",
                "algoritmo": "operativo",
                "timestamp": "datetime().isoString()",
                "componentes": {
                    "neo4j_driver": "ok",
                    "algoritmo_recomendacion": "ok",
                    "algoritmo_estudiante": "ok",
                    "algoritmo_profesor": "ok"
                }
            },
            message="API funcionando correctamente"
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Error de conexión: {str(e)}")

@router.get("/compatibilidad/{nombre_estudiante}")
async def obtener_matriz_compatibilidad(
    nombre_estudiante: str,
    incluir_todos: Optional[bool] = Query(False, description="Incluir todos los profesores aunque no tengan cursos")
):
    """
    Obtiene una matriz de compatibilidad completa para un estudiante
    Útil para análisis y visualizaciones en el frontend
    
    Args:
        nombre_estudiante: Nombre del estudiante
        incluir_todos: Si incluir todos los profesores
        
    Returns:
        Matriz de compatibilidad organizada
    """
    try:
        algoritmo = AlgoritmoRecomendacion()
        recomendaciones = algoritmo.recomendar_profesores(nombre_estudiante)
        
        if isinstance(recomendaciones, dict) and "error" in recomendaciones:
            raise HTTPException(status_code=404, detail=recomendaciones["error"])
        
        # Organizar por rangos de compatibilidad
        matriz = {
            "excelente": [],  # 90-100%
            "muy_bueno": [],  # 80-89%
            "bueno": [],      # 70-79%
            "regular": [],    # 60-69%
            "bajo": []        # < 60%
        }
        
        for rec in recomendaciones:
            porcentaje = rec["porcentaje_recomendacion"]
            if porcentaje >= 90:
                matriz["excelente"].append(rec)
            elif porcentaje >= 80:
                matriz["muy_bueno"].append(rec)
            elif porcentaje >= 70:
                matriz["bueno"].append(rec)
            elif porcentaje >= 60:
                matriz["regular"].append(rec)
            else:
                matriz["bajo"].append(rec)
        
        return create_response(
            data={
                "matriz_compatibilidad": matriz,
                "resumen": {
                    "total_profesores": len(recomendaciones),
                    "excelente": len(matriz["excelente"]),
                    "muy_bueno": len(matriz["muy_bueno"]),
                    "bueno": len(matriz["bueno"]),
                    "regular": len(matriz["regular"]),
                    "bajo": len(matriz["bajo"])
                },
                "estudiante": nombre_estudiante
            },
            message=f"Matriz de compatibilidad generada para {nombre_estudiante}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar matriz: {str(e)}")