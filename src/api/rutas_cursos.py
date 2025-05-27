from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional
from pydantic import BaseModel

from models.curso import Curso
from database.neo4jdriver import Neo4jDriver
from utils.helpers import create_response

router = APIRouter()

# Modelo para actualizaciones parciales
class CursoUpdate(BaseModel):
    nombre: Optional[str] = None
    departamento: Optional[str] = None
    creditos: Optional[int] = None

@router.post("/", status_code=201)
async def crear_curso(curso: Curso):
    """
    Crea un nuevo curso en la base de datos
    
    Args:
        curso: Datos del curso a crear
        
    Returns:
        Datos del curso creado
    """
    try:
        # Verificar si el curso ya existe
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Verificar código
            query_existe = """
            MATCH (c:Curso {codigo: $codigo})
            RETURN c
            """
            result_codigo = session.run(query_existe, codigo=curso.codigo)
            if result_codigo.single():
                raise HTTPException(status_code=400, detail=f"Ya existe un curso con el código {curso.codigo}")
            
            # Crear el curso
            query_crear = """
            CREATE (c:Curso {
                nombre: $nombre,
                codigo: $codigo,
                departamento: $departamento,
                creditos: $creditos,
                fecha_registro: datetime()
            })
            RETURN c
            """
            
            # Convertir el modelo a diccionario
            datos_curso = curso.dict()
            
            result = session.run(query_crear, **datos_curso)
            nuevo_curso = result.single()
            
            if not nuevo_curso:
                raise HTTPException(status_code=500, detail="Error al crear el curso")
            
            # Preparar respuesta
            datos_respuesta = dict(nuevo_curso["c"])
            
            return {
                "success": True,
                "message": "Curso creado exitosamente",
                "data": datos_respuesta
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error detallado: {str(e)}")  # Para debugging
        raise HTTPException(status_code=500, detail=f"Error al crear curso: {str(e)}")

@router.get("/")
async def listar_cursos(departamento: Optional[str] = None):
    """
    Lista todos los cursos, opcionalmente filtrados por departamento
    
    Args:
        departamento: Filtrar por departamento
        
    Returns:
        Lista de cursos
    """
    try:
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Construir la consulta con filtros opcionales
            query = "MATCH (c:Curso)"
            params = {}
            
            if departamento:
                query += " WHERE c.departamento = $departamento"
                params["departamento"] = departamento
                
            query += " RETURN c ORDER BY c.nombre"
            
            result = session.run(query, **params)
            cursos = []
            
            for record in result:
                curso_data = dict(record["c"])
                cursos.append(curso_data)
            
            return {
                "success": True,
                "message": f"Se encontraron {len(cursos)} cursos",
                "data": cursos
            }
        finally:
            session.close()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar cursos: {str(e)}")

@router.get("/{codigo}")
async def obtener_curso(codigo: str):
    """
    Obtiene un curso por su código
    
    Args:
        codigo: Código del curso a buscar
        
    Returns:
        Datos del curso
    """
    try:
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            query = """
            MATCH (c:Curso {codigo: $codigo})
            RETURN c
            """
            result = session.run(query, codigo=codigo)
            record = result.single()
            
            if not record:
                raise HTTPException(status_code=404, detail=f"No se encontró el curso con código {codigo}")
            
            curso_data = dict(record["c"])
            
            return {
                "success": True,
                "message": f"Curso {codigo} encontrado",
                "data": curso_data
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener curso: {str(e)}")

@router.put("/{codigo}")
async def actualizar_curso(
    codigo: str,
    datos_actualizados: CursoUpdate = Body(...)  # Usar el modelo de actualización parcial
):
    """
    Actualiza los datos de un curso existente
    
    Args:
        codigo: Código del curso a actualizar
        datos_actualizados: Datos a actualizar (solo campos proporcionados)
        
    Returns:
        Datos del curso actualizado
    """
    try:
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Verificar que el curso existe
            query_existe = """
            MATCH (c:Curso {codigo: $codigo})
            RETURN c
            """
            result = session.run(query_existe, codigo=codigo)
            curso_existente = result.single()
            
            if not curso_existente:
                raise HTTPException(status_code=404, detail=f"No se encontró el curso con código {codigo}")
            
            # Convertir a diccionario y filtrar campos None
            update_data = datos_actualizados.dict(exclude_none=True)
            
            # Construir la consulta para actualizar solo los campos proporcionados
            if not update_data:
                curso_data = dict(curso_existente["c"])
                return {
                    "success": True,
                    "message": "No se proporcionaron campos para actualizar",
                    "data": curso_data
                }
            
            update_fields = []
            params = {"codigo": codigo}
            
            for key, value in update_data.items():
                update_fields.append(f"c.{key} = ${key}")
                params[key] = value
            
            # Ejecutar la actualización
            query_update = f"""
            MATCH (c:Curso {{codigo: $codigo}})
            SET {', '.join(update_fields)}
            RETURN c
            """
            
            print(f"Query de actualización: {query_update}")  # Debug
            print(f"Parámetros: {params}")  # Debug
            
            result_update = session.run(query_update, **params)
            updated_record = result_update.single()
            
            if not updated_record:
                raise HTTPException(status_code=500, detail="Error al actualizar el curso")
            
            # Preparar respuesta
            curso_data = dict(updated_record["c"])
            
            return {
                "success": True,
                "message": f"Curso {codigo} actualizado exitosamente",
                "data": curso_data
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en actualizar_curso: {str(e)}")  # Debug
        raise HTTPException(status_code=500, detail=f"Error al actualizar curso: {str(e)}")

@router.delete("/{codigo}")
async def eliminar_curso(codigo: str):
    """
    Elimina un curso de la base de datos (solo si no tiene relaciones)
    
    Args:
        codigo: Código del curso a eliminar
        
    Returns:
        Confirmación de eliminación
    """
    try:
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Verificar que el curso existe
            query_existe = """
            MATCH (c:Curso {codigo: $codigo})
            RETURN c
            """
            result = session.run(query_existe, codigo=codigo)
            if not result.single():
                raise HTTPException(status_code=404, detail=f"No se encontró el curso con código {codigo}")
            
            # Verificar que no tiene relaciones
            query_relaciones = """
            MATCH (c:Curso {codigo: $codigo})
            MATCH (c)-[r]-()
            RETURN count(r) as num_relaciones
            """
            result_relaciones = session.run(query_relaciones, codigo=codigo)
            relaciones = result_relaciones.single()
            
            if relaciones and relaciones["num_relaciones"] > 0:
                raise HTTPException(
                    status_code=400, 
                    detail=f"No se puede eliminar el curso {codigo} porque tiene relaciones con estudiantes o profesores"
                )
            
            # Eliminar el curso
            query_delete = """
            MATCH (c:Curso {codigo: $codigo})
            DELETE c
            RETURN COUNT(c) as deleted_count
            """
            result_delete = session.run(query_delete, codigo=codigo)
            deleted = result_delete.single()
            
            if deleted["deleted_count"] == 0:
                raise HTTPException(status_code=500, detail="Error al eliminar el curso")
            
            return {
                "success": True,
                "message": f"Curso {codigo} eliminado exitosamente"
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar curso: {str(e)}")

@router.get("/{codigo}/profesores")
async def obtener_profesores_curso(codigo: str):
    """
    Obtiene todos los profesores que imparten un curso
    
    Args:
        codigo: Código del curso
        
    Returns:
        Lista de profesores del curso
    """
    try:
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Verificar que el curso existe
            query_curso = """
            MATCH (c:Curso {codigo: $codigo})
            RETURN c
            """
            result_curso = session.run(query_curso, codigo=codigo)
            if not result_curso.single():
                raise HTTPException(status_code=404, detail=f"No se encontró el curso {codigo}")
            
            # Obtener profesores del curso (sin fecha_asignacion)
            query_profesores = """
            MATCH (p:Profesor)-[:IMPARTE]->(c:Curso {codigo: $codigo})
            RETURN p
            ORDER BY p.nombre
            """
            
            result = session.run(query_profesores, codigo=codigo)
            profesores = []
            
            for record in result:
                profesor_data = dict(record["p"])
                profesores.append(profesor_data)
            
            return {
                "success": True,
                "message": f"Se encontraron {len(profesores)} profesores para el curso {codigo}",
                "data": profesores
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener profesores del curso: {str(e)}")

@router.get("/{codigo}/estudiantes")
async def obtener_estudiantes_curso(codigo: str):
    """
    Obtiene todos los estudiantes inscritos en un curso
    
    Args:
        codigo: Código del curso
        
    Returns:
        Lista de estudiantes del curso
    """
    try:
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Verificar que el curso existe
            query_curso = """
            MATCH (c:Curso {codigo: $codigo})
            RETURN c
            """
            result_curso = session.run(query_curso, codigo=codigo)
            if not result_curso.single():
                raise HTTPException(status_code=404, detail=f"No se encontró el curso {codigo}")
            
            # Obtener estudiantes del curso
            query_estudiantes = """
            MATCH (e:Estudiante)-[r:INSCRITO]->(c:Curso {codigo: $codigo})
            RETURN e, r.fecha_inscripcion as fecha_inscripcion, r.nota_final as nota_final, r.aprobado as aprobado
            ORDER BY e.nombre
            """
            
            result = session.run(query_estudiantes, codigo=codigo)
            estudiantes = []
            
            for record in result:
                estudiante_data = dict(record["e"])
                estudiante_data.pop("password", None)  # No incluir password
                estudiante_data["fecha_inscripcion"] = record["fecha_inscripcion"]
                estudiante_data["nota_final"] = record["nota_final"]
                estudiante_data["aprobado"] = record["aprobado"]
                estudiantes.append(estudiante_data)
            
            return {
                "success": True,
                "message": f"Se encontraron {len(estudiantes)} estudiantes para el curso {codigo}",
                "data": estudiantes
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estudiantes del curso: {str(e)}")

@router.post("/{codigo}/estudiantes/{carnet}")
async def inscribir_estudiante_curso(codigo: str, carnet: str):
    """
    Inscribe un estudiante a un curso (crea relación INSCRITO)
    
    Args:
        codigo: Código del curso
        carnet: Carnet del estudiante
        
    Returns:
        Confirmación de la inscripción
    """
    try:
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Verificar que el curso existe
            query_curso = """
            MATCH (c:Curso {codigo: $codigo})
            RETURN c
            """
            result_curso = session.run(query_curso, codigo=codigo)
            if not result_curso.single():
                raise HTTPException(status_code=404, detail=f"No se encontró el curso {codigo}")
            
            # Verificar que el estudiante existe
            query_estudiante = """
            MATCH (e:Estudiante {carnet: $carnet})
            RETURN e
            """
            result_estudiante = session.run(query_estudiante, carnet=carnet)
            if not result_estudiante.single():
                raise HTTPException(status_code=404, detail=f"No se encontró al estudiante con carnet {carnet}")
            
            # Verificar si ya existe la relación
            query_relacion = """
            MATCH (e:Estudiante {carnet: $carnet})-[r:INSCRITO]->(c:Curso {codigo: $codigo})
            RETURN r
            """
            result_relacion = session.run(query_relacion, carnet=carnet, codigo=codigo)
            if result_relacion.single():
                raise HTTPException(status_code=400, detail=f"El estudiante {carnet} ya está inscrito en el curso {codigo}")
            
            # Crear la relación
            query_crear_relacion = """
            MATCH (e:Estudiante {carnet: $carnet})
            MATCH (c:Curso {codigo: $codigo})
            CREATE (e)-[r:INSCRITO {fecha_inscripcion: datetime(), nota_final: null, aprobado: null}]->(c)
            RETURN r
            """
            
            result = session.run(query_crear_relacion, carnet=carnet, codigo=codigo)
            
            if not result.single():
                raise HTTPException(status_code=500, detail="Error al crear la inscripción")
            
            return {
                "success": True,
                "message": f"Se inscribió al estudiante {carnet} en el curso {codigo}"
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al inscribir estudiante: {str(e)}")

@router.delete("/{codigo}/estudiantes/{carnet}")
async def desinscribir_estudiante_curso(codigo: str, carnet: str):
    """
    Desinscribe un estudiante de un curso (elimina relación INSCRITO)
    
    Args:
        codigo: Código del curso
        carnet: Carnet del estudiante
        
    Returns:
        Confirmación de la desinscripción
    """
    try:
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Verificar que existe la relación
            query_relacion = """
            MATCH (e:Estudiante {carnet: $carnet})-[r:INSCRITO]->(c:Curso {codigo: $codigo})
            RETURN r
            """
            result_relacion = session.run(query_relacion, carnet=carnet, codigo=codigo)
            if not result_relacion.single():
                raise HTTPException(status_code=404, detail=f"No existe inscripción entre estudiante {carnet} y curso {codigo}")
            
            # Eliminar la relación
            query_eliminar = """
            MATCH (e:Estudiante {carnet: $carnet})-[r:INSCRITO]->(c:Curso {codigo: $codigo})
            DELETE r
            RETURN COUNT(r) as deleted_count
            """
            
            result = session.run(query_eliminar, carnet=carnet, codigo=codigo)
            deleted = result.single()
            
            if deleted["deleted_count"] == 0:
                raise HTTPException(status_code=500, detail="Error al eliminar la inscripción")
            
            return {
                "success": True,
                "message": f"Se desinscribió al estudiante {carnet} del curso {codigo}"
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al desinscribir estudiante: {str(e)}")

@router.put("/{codigo}/estudiantes/{carnet}/nota")
async def actualizar_nota_estudiante(
    codigo: str, 
    carnet: str, 
    datos_nota: dict = Body(...)
):
    """
    Actualiza la nota de un estudiante en un curso específico
    
    Args:
        codigo: Código del curso
        carnet: Carnet del estudiante
        datos_nota: Dict con nota_final y opcionalmente aprobado
        
    Returns:
        Confirmación de la actualización
    """
    try:
        if "nota_final" not in datos_nota:
            raise HTTPException(status_code=400, detail="Se requiere nota_final")
        
        nota_final = datos_nota["nota_final"]
        if not isinstance(nota_final, (int, float)) or nota_final < 0 or nota_final > 100:
            raise HTTPException(status_code=400, detail="La nota debe ser un número entre 0 y 100")
        
        # Calcular automáticamente si aprobó (nota >= 61)
        aprobado = nota_final >= 61
        
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Verificar que existe la relación
            query_relacion = """
            MATCH (e:Estudiante {carnet: $carnet})-[r:INSCRITO]->(c:Curso {codigo: $codigo})
            RETURN r
            """
            result_relacion = session.run(query_relacion, carnet=carnet, codigo=codigo)
            if not result_relacion.single():
                raise HTTPException(status_code=404, detail=f"No existe inscripción entre estudiante {carnet} y curso {codigo}")
            
            # Actualizar la nota
            query_actualizar = """
            MATCH (e:Estudiante {carnet: $carnet})-[r:INSCRITO]->(c:Curso {codigo: $codigo})
            SET r.nota_final = $nota_final, r.aprobado = $aprobado
            RETURN r
            """
            
            result = session.run(query_actualizar, 
                               carnet=carnet, 
                               codigo=codigo, 
                               nota_final=nota_final, 
                               aprobado=aprobado)
            
            if not result.single():
                raise HTTPException(status_code=500, detail="Error al actualizar la nota")
            
            return {
                "success": True,
                "message": f"Se actualizó la nota del estudiante {carnet} en el curso {codigo}",
                "data": {
                    "nota_final": nota_final,
                    "aprobado": aprobado
                }
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar nota: {str(e)}")