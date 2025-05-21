from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional

from src.models.curso import Curso
from src.database.neo4jdriver import Neo4jDriver
from src.utils.helpers import create_response

router = APIRouter()

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
        existente = driver.execute_read(
            "MATCH (c:Curso {codigo: $codigo}) RETURN c",
            codigo=curso.codigo
        )
        
        if existente:
            raise HTTPException(status_code=400, detail=f"Ya existe un curso con el código {curso.codigo}")
        
        # Registrar curso en la base de datos
        result = driver.execute_write(
            """
            CREATE (c:Curso {
                nombre: $nombre,
                codigo: $codigo,
                departamento: $departamento,
                creditos: $creditos
            })
            RETURN c
            """,
            nombre=curso.nombre,
            codigo=curso.codigo,
            departamento=curso.departamento,
            creditos=curso.creditos
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Error al crear el curso")
            
        return create_response(
            data=result[0]["c"],
            message="Curso creado exitosamente"
        )
    except Exception as e:
        # Si es un error de validación de Pydantic, ya se maneja en FastAPI
        if not isinstance(e, HTTPException):
            raise HTTPException(status_code=500, detail=f"Error al crear curso: {str(e)}")
        raise e

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
        result = driver.execute_read(
            "MATCH (c:Curso {codigo: $codigo}) RETURN c",
            codigo=codigo
        )
        
        if not result:
            raise HTTPException(status_code=404, detail=f"No se encontró el curso con código {codigo}")
            
        return create_response(
            data=result[0]["c"],
            message=f"Curso {codigo} encontrado"
        )
    except Exception as e:
        if not isinstance(e, HTTPException):
            raise HTTPException(status_code=500, detail=f"Error al obtener curso: {str(e)}")
        raise e

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
        # Construir la consulta con filtros opcionales
        query = "MATCH (c:Curso)"
        params = {}
        
        if departamento:
            query += " WHERE c.departamento = $departamento"
            params["departamento"] = departamento
            
        query += " RETURN c"
        
        # Ejecutar consulta
        driver = Neo4jDriver()
        result = driver.execute_read(query, **params)
        
        cursos = [record["c"] for record in result]
        
        return create_response(
            data=cursos,
            message=f"Se encontraron {len(cursos)} cursos"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar cursos: {str(e)}")

@router.put("/{codigo}")
async def actualizar_curso(
    codigo: str,
    datos_actualizados: dict = Body(...)
):
    """
    Actualiza los datos de un curso existente
    
    Args:
        codigo: Código del curso a actualizar
        datos_actualizados: Datos a actualizar
        
    Returns:
        Datos del curso actualizado
    """
    try:
        driver = Neo4jDriver()
        
        # Verificar que el curso existe
        existente = driver.execute_read(
            "MATCH (c:Curso {codigo: $codigo}) RETURN c",
            codigo=codigo
        )
        
        if not existente:
            raise HTTPException(status_code=404, detail=f"No se encontró el curso con código {codigo}")
        
        # Construir la consulta para actualizar sólo los campos proporcionados
        update_fields = []
        params = {"codigo": codigo}
        
        for key, value in datos_actualizados.items():
            if key != "codigo":  # No permitir cambiar el código (clave primaria)
                update_fields.append(f"c.{key} = ${key}")
                params[key] = value
        
        if not update_fields:
            return create_response(
                data=existente[0]["c"],
                message="No se proporcionaron campos para actualizar"
            )
        
        # Ejecutar la actualización
        query = f"""
        MATCH (c:Curso {{codigo: $codigo}})
        SET {', '.join(update_fields)}
        RETURN c
        """
        
        result = driver.execute_write(query, **params)
        
        if not result:
            raise HTTPException(status_code=500, detail="Error al actualizar el curso")
        
        return create_response(
            data=result[0]["c"],
            message=f"Curso {codigo} actualizado exitosamente"
        )
    except Exception as e:
        if not isinstance(e, HTTPException):
            raise HTTPException(status_code=500, detail=f"Error al actualizar curso: {str(e)}")
        raise e

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
        
        # Verificar que el curso existe
        existente = driver.execute_read(
            "MATCH (c:Curso {codigo: $codigo}) RETURN c",
            codigo=codigo
        )
        
        if not existente:
            raise HTTPException(status_code=404, detail=f"No se encontró el curso con código {codigo}")
        
        # Verificar que no tiene relaciones
        relaciones = driver.execute_read(
            """
            MATCH (c:Curso {codigo: $codigo})
            MATCH (c)-[r]-()
            RETURN count(r) as num_relaciones
            """,
            codigo=codigo
        )
        
        if relaciones and relaciones[0]["num_relaciones"] > 0:
            raise HTTPException(
                status_code=400, 
                detail=f"No se puede eliminar el curso {codigo} porque tiene relaciones con estudiantes o profesores"
            )
        
        # Eliminar el curso
        result = driver.execute_write(
            "MATCH (c:Curso {codigo: $codigo}) DELETE c",
            codigo=codigo
        )
        
        return create_response(
            message=f"Curso {codigo} eliminado exitosamente"
        )
    except Exception as e:
        if not isinstance(e, HTTPException):
            raise HTTPException(status_code=500, detail=f"Error al eliminar curso: {str(e)}")
        raise e