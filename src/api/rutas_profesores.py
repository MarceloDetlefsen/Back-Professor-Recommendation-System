from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional

from models.profesor import Profesor
from database.neo4jdriver import Neo4jDriver
from utils.helpers import create_response

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
        # Calcular puntuación
        profesor.calcular_puntuacion()
        
        # Verificar si el profesor ya existe por nombre
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Verificar nombre
            query_existe = """
            MATCH (p:Profesor {nombre: $nombre})
            RETURN p
            """
            result_nombre = session.run(query_existe, nombre=profesor.nombre)
            if result_nombre.single():
                raise HTTPException(status_code=400, detail="Ya existe un profesor con ese nombre")
            
            # Crear el profesor
            query_crear = """
            CREATE (p:Profesor {
                nombre: $nombre,
                estilo_enseñanza: $estilo_enseñanza,
                estilo_clase: $estilo_clase,
                años_experiencia: $años_experiencia,
                evaluacion_docente: $evaluacion_docente,
                porcentaje_aprobados: $porcentaje_aprobados,
                disponibilidad: $disponibilidad,
                puntuacion_total: $puntuacion_total,
                fecha_registro: datetime()
            })
            RETURN p
            """
            
            # Convertir el modelo a diccionario
            datos_profesor = profesor.dict()
            
            result = session.run(query_crear, **datos_profesor)
            nuevo_profesor = result.single()
            
            if not nuevo_profesor:
                raise HTTPException(status_code=500, detail="Error al crear el profesor")
            
            # Preparar respuesta
            datos_respuesta = dict(nuevo_profesor["p"])
            
            return {
                "success": True,
                "message": "Profesor registrado exitosamente",
                "data": datos_respuesta
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error detallado: {str(e)}")  # Para debugging
        raise HTTPException(status_code=500, detail=f"Error al crear profesor: {str(e)}")

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
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Construir la consulta con filtros opcionales
            query = "MATCH (p:Profesor)"
            where_clauses = []
            params = {}
            
            if estilo_enseñanza:
                where_clauses.append("p.estilo_enseñanza = $estilo_enseñanza")
                params["estilo_enseñanza"] = estilo_enseñanza.lower()
                
            if estilo_clase:
                where_clauses.append("p.estilo_clase = $estilo_clase")
                params["estilo_clase"] = estilo_clase.lower()
            
            # Añadir cláusula WHERE si hay filtros
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
                
            query += " RETURN p ORDER BY p.nombre"
            
            result = session.run(query, **params)
            profesores = []
            
            for record in result:
                profesor_data = dict(record["p"])
                profesores.append(profesor_data)
            
            return {
                "success": True,
                "message": f"Se encontraron {len(profesores)} profesores",
                "data": profesores
            }
        finally:
            session.close()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener profesores: {str(e)}")

@router.get("/{nombre}")
async def obtener_profesor_por_nombre(nombre: str):
    """
    Obtiene un profesor por su nombre
    
    Args:
        nombre: Nombre del profesor a buscar
        
    Returns:
        Datos del profesor
    """
    try:
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            query = """
            MATCH (p:Profesor {nombre: $nombre})
            RETURN p
            """
            result = session.run(query, nombre=nombre)
            record = result.single()
            
            if not record:
                raise HTTPException(status_code=404, detail=f"No se encontró al profesor con nombre {nombre}")
            
            profesor_data = dict(record["p"])
            
            return {
                "success": True,
                "message": f"Profesor {nombre} encontrado",
                "data": profesor_data
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener profesor: {str(e)}")

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
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Verificar que el profesor existe
            query_existe = """
            MATCH (p:Profesor {nombre: $nombre})
            RETURN p
            """
            result = session.run(query_existe, nombre=nombre)
            profesor_existente = result.single()
            
            if not profesor_existente:
                raise HTTPException(status_code=404, detail=f"No se encontró al profesor con nombre {nombre}")
            
            # Construir la consulta para actualizar sólo los campos proporcionados
            update_fields = []
            params = {"nombre": nombre}
            
            for key, value in datos_actualizados.items():
                if key not in ["nombre"]:  # No permitir cambiar el nombre
                    update_fields.append(f"p.{key} = ${key}")
                    params[key] = value
            
            if not update_fields:
                profesor_data = dict(profesor_existente["p"])
                return {
                    "success": True,
                    "message": "No se proporcionaron campos para actualizar",
                    "data": profesor_data
                }
            
            # Ejecutar la actualización
            query_update = f"""
            MATCH (p:Profesor {{nombre: $nombre}})
            SET {', '.join(update_fields)}
            RETURN p
            """
            
            result_update = session.run(query_update, **params)
            updated_record = result_update.single()
            
            if not updated_record:
                raise HTTPException(status_code=500, detail="Error al actualizar el profesor")
            
            # Recalcular puntuación si se actualizaron campos relevantes
            relevant_fields = {"años_experiencia", "evaluacion_docente", "porcentaje_aprobados", "disponibilidad"}
            if any(field in datos_actualizados for field in relevant_fields):
                updated_data = dict(updated_record["p"])
                
                # Crear un objeto Profesor para recalcular puntuación
                profesor_temp = Profesor(
                    nombre=updated_data["nombre"],
                    estilo_enseñanza=updated_data["estilo_enseñanza"],
                    estilo_clase=updated_data["estilo_clase"],
                    años_experiencia=updated_data["años_experiencia"],
                    evaluacion_docente=updated_data["evaluacion_docente"],
                    porcentaje_aprobados=updated_data["porcentaje_aprobados"],
                    disponibilidad=updated_data["disponibilidad"]
                )
                
                # Recalcular puntuación
                nueva_puntuacion = profesor_temp.calcular_puntuacion()
                
                # Actualizar puntuación en base de datos
                query_puntuacion = """
                MATCH (p:Profesor {nombre: $nombre})
                SET p.puntuacion_total = $puntuacion_total
                RETURN p
                """
                
                result_puntuacion = session.run(query_puntuacion, 
                                               nombre=nombre, 
                                               puntuacion_total=nueva_puntuacion)
                final_record = result_puntuacion.single()
                profesor_data = dict(final_record["p"])
            else:
                profesor_data = dict(updated_record["p"])
            
            return {
                "success": True,
                "message": f"Profesor {nombre} actualizado exitosamente",
                "data": profesor_data
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar profesor: {str(e)}")

@router.delete("/{nombre}")
async def eliminar_profesor(nombre: str):
    """
    Elimina un profesor por su nombre (solo si no tiene relaciones)
    
    Args:
        nombre: Nombre del profesor a eliminar
        
    Returns:
        Confirmación de eliminación
    """
    try:
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Verificar que el profesor existe
            query_existe = """
            MATCH (p:Profesor {nombre: $nombre})
            RETURN p
            """
            result = session.run(query_existe, nombre=nombre)
            if not result.single():
                raise HTTPException(status_code=404, detail=f"No se encontró al profesor con nombre {nombre}")
            
            # Verificar que no tiene relaciones
            query_relaciones = """
            MATCH (p:Profesor {nombre: $nombre})
            MATCH (p)-[r]-()
            RETURN count(r) as num_relaciones
            """
            result_relaciones = session.run(query_relaciones, nombre=nombre)
            relaciones = result_relaciones.single()
            
            if relaciones and relaciones["num_relaciones"] > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"No se puede eliminar al profesor {nombre} porque tiene relaciones con cursos"
                )
            
            # Eliminar el profesor
            query_delete = """
            MATCH (p:Profesor {nombre: $nombre})
            DELETE p
            RETURN COUNT(p) as deleted_count
            """
            result_delete = session.run(query_delete, nombre=nombre)
            deleted = result_delete.single()
            
            if deleted["deleted_count"] == 0:
                raise HTTPException(status_code=500, detail="Error al eliminar el profesor")
            
            return {
                "success": True,
                "message": f"Profesor {nombre} eliminado exitosamente"
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar profesor: {str(e)}")

@router.post("/{nombre_profesor}/cursos/{codigo_curso}")
async def asignar_curso_a_profesor(nombre_profesor: str, codigo_curso: str):
    """
    Asigna un curso a un profesor (crea relación IMPARTE)
    
    Args:
        nombre_profesor: Nombre del profesor
        codigo_curso: Código del curso
        
    Returns:
        Confirmación de la asignación
    """
    try:
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Verificar que el profesor existe
            query_profesor = """
            MATCH (p:Profesor {nombre: $nombre})
            RETURN p
            """
            result_profesor = session.run(query_profesor, nombre=nombre_profesor)
            if not result_profesor.single():
                raise HTTPException(status_code=404, detail=f"No se encontró al profesor {nombre_profesor}")
            
            # Verificar que el curso existe
            query_curso = """
            MATCH (c:Curso {codigo: $codigo})
            RETURN c
            """
            result_curso = session.run(query_curso, codigo=codigo_curso)
            if not result_curso.single():
                raise HTTPException(status_code=404, detail=f"No se encontró el curso {codigo_curso}")
            
            # Verificar si ya existe la relación
            query_relacion = """
            MATCH (p:Profesor {nombre: $nombre_profesor})-[r:IMPARTE]->(c:Curso {codigo: $codigo_curso})
            RETURN r
            """
            result_relacion = session.run(query_relacion, 
                                        nombre_profesor=nombre_profesor, 
                                        codigo_curso=codigo_curso)
            if result_relacion.single():
                raise HTTPException(status_code=400, detail=f"El profesor {nombre_profesor} ya imparte el curso {codigo_curso}")
            
            # Crear la relación sin fecha_asignacion
            query_crear_relacion = """
            MATCH (p:Profesor {nombre: $nombre_profesor})
            MATCH (c:Curso {codigo: $codigo_curso})
            CREATE (p)-[r:IMPARTE]->(c)
            RETURN r
            """
            
            result = session.run(query_crear_relacion, 
                               nombre_profesor=nombre_profesor, 
                               codigo_curso=codigo_curso)
            
            if not result.single():
                raise HTTPException(status_code=500, detail="Error al crear la relación")
            
            return {
                "success": True,
                "message": f"Se asignó el curso {codigo_curso} al profesor {nombre_profesor}"
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al asignar curso: {str(e)}")

@router.delete("/{nombre_profesor}/cursos/{codigo_curso}")
async def desasignar_curso_de_profesor(nombre_profesor: str, codigo_curso: str):
    """
    Desasigna un curso de un profesor (elimina relación IMPARTE)
    
    Args:
        nombre_profesor: Nombre del profesor
        codigo_curso: Código del curso
        
    Returns:
        Confirmación de la desasignación
    """
    try:
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Verificar que existe la relación
            query_relacion = """
            MATCH (p:Profesor {nombre: $nombre_profesor})-[r:IMPARTE]->(c:Curso {codigo: $codigo_curso})
            RETURN r
            """
            result_relacion = session.run(query_relacion, 
                                        nombre_profesor=nombre_profesor, 
                                        codigo_curso=codigo_curso)
            if not result_relacion.single():
                raise HTTPException(status_code=404, detail=f"No existe relación entre {nombre_profesor} y {codigo_curso}")
            
            # Eliminar la relación
            query_eliminar = """
            MATCH (p:Profesor {nombre: $nombre_profesor})-[r:IMPARTE]->(c:Curso {codigo: $codigo_curso})
            DELETE r
            RETURN COUNT(r) as deleted_count
            """
            
            result = session.run(query_eliminar, 
                               nombre_profesor=nombre_profesor, 
                               codigo_curso=codigo_curso)
            deleted = result.single()
            
            if deleted["deleted_count"] == 0:
                raise HTTPException(status_code=500, detail="Error al eliminar la relación")
            
            return {
                "success": True,
                "message": f"Se desasignó el curso {codigo_curso} del profesor {nombre_profesor}"
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al desasignar curso: {str(e)}")

@router.get("/{nombre_profesor}/cursos")
async def obtener_cursos_profesor(nombre_profesor: str):
    """
    Obtiene todos los cursos que imparte un profesor
    
    Args:
        nombre_profesor: Nombre del profesor
        
    Returns:
        Lista de cursos del profesor
    """
    try:
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Verificar que el profesor existe
            query_profesor = """
            MATCH (p:Profesor {nombre: $nombre})
            RETURN p
            """
            result_profesor = session.run(query_profesor, nombre=nombre_profesor)
            if not result_profesor.single():
                raise HTTPException(status_code=404, detail=f"No se encontró al profesor {nombre_profesor}")
            
            # Obtener cursos del profesor (sin fecha_asignacion)
            query_cursos = """
            MATCH (p:Profesor {nombre: $nombre_profesor})-[:IMPARTE]->(c:Curso)
            RETURN c
            ORDER BY c.nombre
            """
            
            result = session.run(query_cursos, nombre_profesor=nombre_profesor)
            cursos = []
            
            for record in result:
                curso_data = dict(record["c"])
                cursos.append(curso_data)
            
            return {
                "success": True,
                "message": f"Se encontraron {len(cursos)} cursos para el profesor {nombre_profesor}",
                "data": cursos
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener cursos del profesor: {str(e)}")