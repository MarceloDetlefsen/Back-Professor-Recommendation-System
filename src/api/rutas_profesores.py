from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional

from models.profesor import Profesor
from services.algoritmo_profesor import AlgoritmoProfesor
from database.neo4jdriver import Neo4jDriver
from utils.helpers import create_response, validate_learning_style, validate_class_style

router = APIRouter()

@router.post("/", status_code=201)
async def crear_profesor(profesor: Profesor):
    """
    Crea un nuevo profesor en la base de datos
    
    Args:
        profesor: Datos del profesor a crear
        
    Returns:
        Datos del profesor creado
    """
    try:
        # Validar estilos
        if not validate_learning_style(profesor.estilo_enseñanza):
            raise HTTPException(status_code=400, detail="Estilo de enseñanza no válido")
            
        if not validate_class_style(profesor.estilo_clase):
            raise HTTPException(status_code=400, detail="Estilo de clase no válido")
        
        # Calcular puntuación
        profesor.calcular_puntuacion()
        
        # Registrar en la base de datos
        algoritmo = AlgoritmoProfesor()
        nuevo_profesor = algoritmo.registrar_profesor(profesor)
        
        if not nuevo_profesor:
            raise HTTPException(status_code=500, detail="Error al crear el profesor")
            
        return create_response(
            data=nuevo_profesor,
            message="Profesor creado exitosamente"
        )
    except Exception as e:
        # Si es un error de validación de Pydantic, ya se maneja en FastAPI
        if not isinstance(e, HTTPException):
            raise HTTPException(status_code=500, detail=f"Error al crear profesor: {str(e)}")
        raise e

@router.get("/{nombre}")
async def obtener_profesor(nombre: str):
    """
    Obtiene un profesor por su nombre
    
    Args:
        nombre: Nombre del profesor a buscar
        
    Returns:
        Datos del profesor
    """
    try:
        algoritmo = AlgoritmoProfesor()
        profesor = algoritmo.obtener_profesor(nombre)
        
        if not profesor:
            raise HTTPException(status_code=404, detail=f"No se encontró al profesor con nombre {nombre}")
            
        return create_response(
            data=profesor,
            message=f"Profesor {nombre} encontrado"
        )
    except Exception as e:
        if not isinstance(e, HTTPException):
            raise HTTPException(status_code=500, detail=f"Error al obtener profesor: {str(e)}")
        raise e

@router.get("/")
async def listar_profesores(
    estilo_enseñanza: Optional[str] = None,
    estilo_clase: Optional[str] = None
):
    """
    Lista todos los profesores, opcionalmente filtrados por estilo
    
    Args:
        estilo_enseñanza: Filtrar por estilo de enseñanza
        estilo_clase: Filtrar por estilo de clase
        
    Returns:
        Lista de profesores
    """
    try:
        # Construir la consulta con filtros opcionales
        query = "MATCH (p:Profesor)"
        where_clauses = []
        params = {}
        
        if estilo_enseñanza:
            if not validate_learning_style(estilo_enseñanza):
                raise HTTPException(status_code=400, detail="Estilo de enseñanza no válido")
            where_clauses.append("p.estilo_enseñanza = $estilo_enseñanza")
            params["estilo_enseñanza"] = estilo_enseñanza.lower()
            
        if estilo_clase:
            if not validate_class_style(estilo_clase):
                raise HTTPException(status_code=400, detail="Estilo de clase no válido")
            where_clauses.append("p.estilo_clase = $estilo_clase")
            params["estilo_clase"] = estilo_clase.lower()
        
        # Añadir cláusula WHERE si hay filtros
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
            
        query += " RETURN p"
        
        # Ejecutar consulta
        driver = Neo4jDriver()
        result = driver.execute_read(query, **params)
        
        profesores = [record["p"] for record in result]
        
        return create_response(
            data=profesores,
            message=f"Se encontraron {len(profesores)} profesores"
        )
    except Exception as e:
        if not isinstance(e, HTTPException):
            raise HTTPException(status_code=500, detail=f"Error al listar profesores: {str(e)}")
        raise e

@router.put("/{nombre}")
async def actualizar_profesor(
    nombre: str,
    datos_actualizados: dict = Body(...)
):
    """
    Actualiza los datos de un profesor existente
    
    Args:
        nombre: Nombre del profesor a actualizar
        datos_actualizados: Datos a actualizar
        
    Returns:
        Datos del profesor actualizado
    """
    try:
        algoritmo = AlgoritmoProfesor()
        
        # Verificar que el profesor existe
        profesor_existente = algoritmo.obtener_profesor(nombre)
        if not profesor_existente:
            raise HTTPException(status_code=404, detail=f"No se encontró al profesor con nombre {nombre}")
        
        # Validar estilos si se van a actualizar
        if "estilo_enseñanza" in datos_actualizados and not validate_learning_style(datos_actualizados["estilo_enseñanza"]):
            raise HTTPException(status_code=400, detail="Estilo de enseñanza no válido")
            
        if "estilo_clase" in datos_actualizados and not validate_class_style(datos_actualizados["estilo_clase"]):
            raise HTTPException(status_code=400, detail="Estilo de clase no válido")
        
        # Construir la consulta para actualizar sólo los campos proporcionados
        update_fields = []
        params = {"nombre": nombre}
        
        for key, value in datos_actualizados.items():
            if key != "nombre":  # No permitir cambiar el nombre (clave primaria)
                update_fields.append(f"p.{key} = ${key}")
                params[key] = value
        
        if not update_fields:
            return create_response(
                data=profesor_existente,
                message="No se proporcionaron campos para actualizar"
            )
        
        # Ejecutar la actualización
        query = f"""
        MATCH (p:Profesor {{nombre: $nombre}})
        SET {', '.join(update_fields)}
        RETURN p
        """
        
        driver = Neo4jDriver()
        result = driver.execute_write(query, **params)
        
        if not result:
            raise HTTPException(status_code=500, detail="Error al actualizar el profesor")
            
        # Recalcular puntuación si se actualizaron campos relevantes
        relevant_fields = {"años_experiencia", "evaluacion_docente", "porcentaje_aprobados", "disponibilidad"}
        if any(field in datos_actualizados for field in relevant_fields):
            # Obtener el profesor actualizado
            updated_data = result[0]["p"]
            
            # Crear un objeto Profesor para recalcular puntuación
            profesor = Profesor(
                nombre=updated_data["nombre"],
                estilo_enseñanza=updated_data["estilo_enseñanza"],
                estilo_clase=updated_data["estilo_clase"],
                años_experiencia=updated_data["años_experiencia"],
                evaluacion_docente=updated_data["evaluacion_docente"],
                porcentaje_aprobados=updated_data["porcentaje_aprobados"],
                disponibilidad=updated_data["disponibilidad"]
            )
            
            # Recalcular puntuación
            puntuacion = profesor.calcular_puntuacion()
            
            # Actualizar puntuación en base de datos
            driver.execute_write(
                """
                MATCH (p:Profesor {nombre: $nombre})
                SET p.puntuacion_total = $puntuacion
                """,
                nombre=nombre,
                puntuacion=puntuacion
            )
            
            # Obtener el profesor con la puntuación actualizada
            updated_profesor = algoritmo.obtener_profesor(nombre)
            
            return create_response(
                data=updated_profesor,
                message=f"Profesor {nombre} actualizado con puntuación recalculada"
            )
        
        return create_response(
            data=result[0]["p"],
            message=f"Profesor {nombre} actualizado exitosamente"
        )
    except Exception as e:
        if not isinstance(e, HTTPException):
            raise HTTPException(status_code=500, detail=f"Error al actualizar profesor: {str(e)}")
        raise e

@router.post("/{nombre_profesor}/cursos/{codigo_curso}")
async def registrar_curso_impartido(nombre_profesor: str, codigo_curso: str):
    """
    Registra que un profesor imparte un curso específico
    
    Args:
        nombre_profesor: Nombre del profesor
        codigo_curso: Código del curso
        
    Returns:
        Confirmación del registro
    """
    try:
        algoritmo = AlgoritmoProfesor()
        
        # Verificar que el profesor existe
        profesor = algoritmo.obtener_profesor(nombre_profesor)
        if not profesor:
            raise HTTPException(status_code=404, detail=f"No se encontró al profesor con nombre {nombre_profesor}")
        
        # Verificar que el curso existe
        driver = Neo4jDriver()
        curso = driver.execute_read(
            "MATCH (c:Curso {codigo: $codigo}) RETURN c", 
            codigo=codigo_curso
        )
        
        if not curso:
            raise HTTPException(status_code=404, detail=f"No se encontró el curso con código {codigo_curso}")
        
        # Registrar relación
        resultado = algoritmo.registrar_curso_impartido(nombre_profesor, codigo_curso)
        
        if resultado:
            return create_response(
                message=f"Se registró que {nombre_profesor} imparte el curso {codigo_curso}"
            )
        else:
            raise HTTPException(status_code=500, detail="No se pudo registrar la relación")
    except Exception as e:
        if not isinstance(e, HTTPException):
            raise HTTPException(status_code=500, detail=f"Error al registrar curso impartido: {str(e)}")
        raise e