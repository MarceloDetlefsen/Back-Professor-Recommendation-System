from src.database.neo4jdriver import Neo4jDriver
from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional

from src.models.estudiante import Estudiante
from src.services.algoritmo_estudiante import AlgoritmoEstudiante
from src.utils.helpers import create_response, validate_learning_style, validate_class_style

router = APIRouter()

@router.post("/", status_code=201)
async def crear_estudiante(estudiante: Estudiante):
    """
    Crea un nuevo estudiante en la base de datos
    
    Args:
        estudiante: Datos del estudiante a crear
        
    Returns:
        Datos del estudiante creado
    """
    try:
        # Validar estilos
        if not validate_learning_style(estudiante.estilo_aprendizaje):
            raise HTTPException(status_code=400, detail="Estilo de aprendizaje no válido")
            
        if not validate_class_style(estudiante.estilo_clase):
            raise HTTPException(status_code=400, detail="Estilo de clase no válido")
        
        # Calcular puntuación
        estudiante.calcular_puntuacion()
        
        # Registrar en la base de datos
        algoritmo = AlgoritmoEstudiante()
        nuevo_estudiante = algoritmo.registrar_estudiante(estudiante)
        
        if not nuevo_estudiante:
            raise HTTPException(status_code=500, detail="Error al crear el estudiante")
            
        return create_response(
            data=nuevo_estudiante,
            message="Estudiante creado exitosamente"
        )
    except Exception as e:
        # Si es un error de validación de Pydantic, ya se maneja en FastAPI
        if not isinstance(e, HTTPException):
            raise HTTPException(status_code=500, detail=f"Error al crear estudiante: {str(e)}")
        raise e

@router.get("/{nombre}")
async def obtener_estudiante(nombre: str):
    """
    Obtiene un estudiante por su nombre
    
    Args:
        nombre: Nombre del estudiante a buscar
        
    Returns:
        Datos del estudiante
    """
    try:
        algoritmo = AlgoritmoEstudiante()
        estudiante = algoritmo.obtener_estudiante(nombre)
        
        if not estudiante:
            raise HTTPException(status_code=404, detail=f"No se encontró al estudiante con nombre {nombre}")
            
        return create_response(
            data=estudiante,
            message=f"Estudiante {nombre} encontrado"
        )
    except Exception as e:
        if not isinstance(e, HTTPException):
            raise HTTPException(status_code=500, detail=f"Error al obtener estudiante: {str(e)}")
        raise e

@router.get("/{nombre}/similares")
async def obtener_estudiantes_similares(nombre: str):
    """
    Obtiene estudiantes similares a un estudiante específico
    
    Args:
        nombre: Nombre del estudiante de referencia
        
    Returns:
        Lista de estudiantes similares
    """
    try:
        algoritmo = AlgoritmoEstudiante()
        
        # Verificar que el estudiante existe
        estudiante = algoritmo.obtener_estudiante(nombre)
        if not estudiante:
            raise HTTPException(status_code=404, detail=f"No se encontró al estudiante con nombre {nombre}")
        
        # Obtener estudiantes similares
        similares = algoritmo.encontrar_estudiantes_similares(nombre)
        
        return create_response(
            data=similares,
            message=f"Se encontraron {len(similares)} estudiantes similares a {nombre}"
        )
    except Exception as e:
        if not isinstance(e, HTTPException):
            raise HTTPException(status_code=500, detail=f"Error al buscar estudiantes similares: {str(e)}")
        raise e

@router.put("/{nombre}")
async def actualizar_estudiante(
    nombre: str,
    datos_actualizados: dict = Body(...)
):
    """
    Actualiza los datos de un estudiante existente
    
    Args:
        nombre: Nombre del estudiante a actualizar
        datos_actualizados: Datos a actualizar
        
    Returns:
        Datos del estudiante actualizado
    """
    try:
        algoritmo = AlgoritmoEstudiante()
        
        # Verificar que el estudiante existe
        estudiante_existente = algoritmo.obtener_estudiante(nombre)
        if not estudiante_existente:
            raise HTTPException(status_code=404, detail=f"No se encontró al estudiante con nombre {nombre}")
        
        # Validar estilos si se van a actualizar
        if "estilo_aprendizaje" in datos_actualizados and not validate_learning_style(datos_actualizados["estilo_aprendizaje"]):
            raise HTTPException(status_code=400, detail="Estilo de aprendizaje no válido")
            
        if "estilo_clase" in datos_actualizados and not validate_class_style(datos_actualizados["estilo_clase"]):
            raise HTTPException(status_code=400, detail="Estilo de clase no válido")
        
        # Construir la consulta para actualizar sólo los campos proporcionados
        update_fields = []
        params = {"nombre": nombre}
        
        for key, value in datos_actualizados.items():
            if key != "nombre":  # No permitir cambiar el nombre (clave primaria)
                update_fields.append(f"e.{key} = ${key}")
                params[key] = value
        
        if not update_fields:
            return create_response(
                data=estudiante_existente,
                message="No se proporcionaron campos para actualizar"
            )
        
        # Ejecutar la actualización
        query = f"""
        MATCH (e:Estudiante {{nombre: $nombre}})
        SET {', '.join(update_fields)}
        RETURN e
        """
        
        driver = Neo4jDriver()
        result = driver.execute_write(query, **params)
        
        if not result:
            raise HTTPException(status_code=500, detail="Error al actualizar el estudiante")
            
        # Recalcular puntuación si se actualizaron campos relevantes
        relevant_fields = {"promedio", "asistencias_curso_anterior", "veces_que_llevo_curso"}
        if any(field in datos_actualizados for field in relevant_fields):
            # Obtener el estudiante actualizado
            updated_data = result[0]["e"]
            
            # Crear un objeto Estudiante para recalcular puntuación
            estudiante = Estudiante(
                nombre=updated_data["nombre"],
                estilo_aprendizaje=updated_data["estilo_aprendizaje"],
                estilo_clase=updated_data["estilo_clase"],
                promedio=updated_data["promedio"],
                asistencias=updated_data["asistencias_curso_anterior"],
                veces_curso=updated_data["veces_que_llevo_curso"]
            )
            
            # Recalcular puntuación
            puntuacion = estudiante.calcular_puntuacion()
            
            # Actualizar puntuación en base de datos
            driver.execute_write(
                """
                MATCH (e:Estudiante {nombre: $nombre})
                SET e.puntuacion_total = $puntuacion
                """,
                nombre=nombre,
                puntuacion=puntuacion
            )
            
            # Obtener el estudiante con la puntuación actualizada
            updated_estudiante = algoritmo.obtener_estudiante(nombre)
            
            return create_response(
                data=updated_estudiante,
                message=f"Estudiante {nombre} actualizado con puntuación recalculada"
            )
        
        return create_response(
            data=result[0]["e"],
            message=f"Estudiante {nombre} actualizado exitosamente"
        )
    except Exception as e:
        if not isinstance(e, HTTPException):
            raise HTTPException(status_code=500, detail=f"Error al actualizar estudiante: {str(e)}")
        raise e