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
    limite: Optional[int] = Query(None, description="Número máximo de recomendaciones a devolver")
):
    """
    Obtiene recomendaciones de profesores para un estudiante específico
    
    Args:
        nombre_estudiante: Nombre del estudiante
        limite: Número máximo de recomendaciones a devolver
        
    Returns:
        Lista de recomendaciones de profesores ordenadas por compatibilidad
    """
    try:
        algoritmo = AlgoritmoRecomendacion()
        recomendaciones = algoritmo.recomendar_profesores(nombre_estudiante, codigo_curso=curso)
        
        if isinstance(recomendaciones, dict) and "error" in recomendaciones:
            raise HTTPException(status_code=404, detail=recomendaciones["error"])
            
        if limite is not None and limite > 0:
            recomendaciones = recomendaciones[:limite]
            
        return create_response(
            data=recomendaciones,
            message=f"Se encontraron {len(recomendaciones)} recomendaciones para {nombre_estudiante}" + (f" en el curso {curso}" if curso else "")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener recomendaciones: {str(e)}")

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
                message=f"Se registró correctamente que {nombre_estudiante} aprobó el curso {codigo_curso} con {nombre_profesor}"
            )
        else:
            raise HTTPException(status_code=400, detail="No se pudo registrar la aprobación")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al registrar aprobación: {str(e)}")

@router.get("/health")
async def health_check():
    """
    Verifica el estado de la API
    
    Returns:
        Estado de la API
    """
    try:
        # Verificar conexión con Neo4j
        driver = Neo4jDriver()
        driver.execute_read("RETURN 1 as test")
        
        return create_response(
            data={"database": "conectada"},
            message="API funcionando correctamente"
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Error de conexión a la base de datos: {str(e)}")