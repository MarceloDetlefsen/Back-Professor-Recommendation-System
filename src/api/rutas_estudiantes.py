from database.neo4jdriver import Neo4jDriver
from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional

from models.estudiante import Estudiante
from services.algoritmo_estudiante import AlgoritmoEstudiante
from utils.helpers import create_response, validate_learning_style, validate_class_style

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
        # Calcular puntuación
        estudiante.calcular_puntuacion()
        
        # Verificar si el estudiante ya existe por carnet
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Verificar carnet
            query_existe = """
            MATCH (e:Estudiante {carnet: $carnet})
            RETURN e
            """
            result_carnet = session.run(query_existe, carnet=estudiante.carnet)
            if result_carnet.single():
                raise HTTPException(status_code=400, detail="El carnet ya está registrado")
            
            # Verificar email
            query_email = """
            MATCH (e:Estudiante {email: $email})
            RETURN e
            """
            result_email = session.run(query_email, email=estudiante.email)
            if result_email.single():
                raise HTTPException(status_code=400, detail="El email ya está registrado")
            
            # Crear el estudiante
            query_crear = """
            CREATE (e:Estudiante {
                nombre: $nombre,
                carnet: $carnet,
                carrera: $carrera,
                pensum: $pensum,
                email: $email,
                password: $password,
                estilo_aprendizaje: $estilo_aprendizaje,
                estilo_clase: $estilo_clase,
                promedio: $promedio,
                grado: $grado,
                carga_maxima: $carga_maxima,
                cursos_zona_minima: $cursos_zona_minima,
                asistencias: $asistencias,
                veces_curso: $veces_curso,
                puntuacion_total: $puntuacion_total,
                fecha_registro: datetime()
            })
            RETURN e
            """
            
            # Convertir el modelo a diccionario
            datos_estudiante = estudiante.dict()
            
            result = session.run(query_crear, **datos_estudiante)
            nuevo_estudiante = result.single()
            
            if not nuevo_estudiante:
                raise HTTPException(status_code=500, detail="Error al crear el estudiante")
            
            # Preparar respuesta sin incluir la contraseña
            datos_respuesta = dict(nuevo_estudiante["e"])
            datos_respuesta.pop("password", None)  # Remover password de la respuesta
            
            return {
                "success": True,
                "message": "Estudiante registrado exitosamente",
                "data": datos_respuesta
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error detallado: {str(e)}")  # Para debugging
        raise HTTPException(status_code=500, detail=f"Error al crear estudiante: {str(e)}")

@router.get("/")
async def listar_estudiantes():
    """
    Lista todos los estudiantes
    
    Returns:
        Lista de todos los estudiantes
    """
    try:
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            query = """
            MATCH (e:Estudiante)
            RETURN e
            ORDER BY e.nombre
            """
            result = session.run(query)
            estudiantes = []
            
            for record in result:
                estudiante_data = dict(record["e"])
                estudiante_data.pop("password", None)  # No incluir password
                estudiantes.append(estudiante_data)
            
            return {
                "success": True,
                "message": f"Se encontraron {len(estudiantes)} estudiantes",
                "data": estudiantes
            }
        finally:
            session.close()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estudiantes: {str(e)}")

@router.get("/{carnet}")
async def obtener_estudiante_por_carnet(carnet: str):
    """
    Obtiene un estudiante por su carnet
    
    Args:
        carnet: Carnet del estudiante a buscar
        
    Returns:
        Datos del estudiante
    """
    try:
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            query = """
            MATCH (e:Estudiante {carnet: $carnet})
            RETURN e
            """
            result = session.run(query, carnet=carnet)
            record = result.single()
            
            if not record:
                raise HTTPException(status_code=404, detail=f"No se encontró al estudiante con carnet {carnet}")
            
            estudiante_data = dict(record["e"])
            estudiante_data.pop("password", None)  # No incluir password
            
            return {
                "success": True,
                "message": f"Estudiante con carnet {carnet} encontrado",
                "data": estudiante_data
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estudiante: {str(e)}")

@router.get("/nombre/{nombre}")
async def obtener_estudiante_por_nombre(nombre: str):
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estudiante: {str(e)}")

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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al buscar estudiantes similares: {str(e)}")

@router.put("/{carnet}")
async def actualizar_estudiante(
    carnet: str,
    datos_actualizados: dict = Body(...)
):
    """
    Actualiza los datos de un estudiante existente
    
    Args:
        carnet: Carnet del estudiante a actualizar
        datos_actualizados: Datos a actualizar
        
    Returns:
        Datos del estudiante actualizado
    """
    try:
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Verificar que el estudiante existe
            query_existe = """
            MATCH (e:Estudiante {carnet: $carnet})
            RETURN e
            """
            result = session.run(query_existe, carnet=carnet)
            estudiante_existente = result.single()
            
            if not estudiante_existente:
                raise HTTPException(status_code=404, detail=f"No se encontró al estudiante con carnet {carnet}")
            
            # Validar estilos si se van a actualizar
            if "estilo_aprendizaje" in datos_actualizados:
                if not validate_learning_style(datos_actualizados["estilo_aprendizaje"]):
                    raise HTTPException(status_code=400, detail="Estilo de aprendizaje no válido")
                
            if "estilo_clase" in datos_actualizados:
                if not validate_class_style(datos_actualizados["estilo_clase"]):
                    raise HTTPException(status_code=400, detail="Estilo de clase no válido")
            
            # Construir la consulta para actualizar sólo los campos proporcionados
            update_fields = []
            params = {"carnet": carnet}
            
            for key, value in datos_actualizados.items():
                if key not in ["carnet"]:  # No permitir cambiar el carnet
                    update_fields.append(f"e.{key} = ${key}")
                    params[key] = value
            
            if not update_fields:
                estudiante_data = dict(estudiante_existente["e"])
                estudiante_data.pop("password", None)
                return {
                    "success": True,
                    "message": "No se proporcionaron campos para actualizar",
                    "data": estudiante_data
                }
            
            # Ejecutar la actualización
            query_update = f"""
            MATCH (e:Estudiante {{carnet: $carnet}})
            SET {', '.join(update_fields)}
            RETURN e
            """
            
            result_update = session.run(query_update, **params)
            updated_record = result_update.single()
            
            if not updated_record:
                raise HTTPException(status_code=500, detail="Error al actualizar el estudiante")
            
            # Preparar respuesta
            estudiante_data = dict(updated_record["e"])
            estudiante_data.pop("password", None)
            
            return {
                "success": True,
                "message": f"Estudiante con carnet {carnet} actualizado exitosamente",
                "data": estudiante_data
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar estudiante: {str(e)}")

@router.delete("/{carnet}")
async def eliminar_estudiante(carnet: str):
    """
    Elimina un estudiante por su carnet
    
    Args:
        carnet: Carnet del estudiante a eliminar
        
    Returns:
        Confirmación de eliminación
    """
    try:
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Verificar que el estudiante existe
            query_existe = """
            MATCH (e:Estudiante {carnet: $carnet})
            RETURN e
            """
            result = session.run(query_existe, carnet=carnet)
            if not result.single():
                raise HTTPException(status_code=404, detail=f"No se encontró al estudiante con carnet {carnet}")
            
            # Eliminar el estudiante
            query_delete = """
            MATCH (e:Estudiante {carnet: $carnet})
            DELETE e
            RETURN COUNT(e) as deleted_count
            """
            result_delete = session.run(query_delete, carnet=carnet)
            deleted = result_delete.single()
            
            if deleted["deleted_count"] == 0:
                raise HTTPException(status_code=500, detail="Error al eliminar el estudiante")
            
            return {
                "success": True,
                "message": f"Estudiante con carnet {carnet} eliminado exitosamente"
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar estudiante: {str(e)}")

@router.post("/login")
async def login_estudiante(credenciales: dict = Body(...)):
    """
    Autentica un estudiante
    
    Args:
        credenciales: Dict con carnet/email y password
        
    Returns:
        Datos del estudiante autenticado
    """
    try:
        if "carnet" not in credenciales and "email" not in credenciales:
            raise HTTPException(status_code=400, detail="Se requiere carnet o email")
        
        if "password" not in credenciales:
            raise HTTPException(status_code=400, detail="Se requiere password")
        
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Buscar por carnet o email
            if "carnet" in credenciales:
                query = """
                MATCH (e:Estudiante {carnet: $identifier, password: $password})
                RETURN e
                """
                identifier = credenciales["carnet"]
            else:
                query = """
                MATCH (e:Estudiante {email: $identifier, password: $password})
                RETURN e
                """
                identifier = credenciales["email"]
            
            result = session.run(query, identifier=identifier, password=credenciales["password"])
            record = result.single()
            
            if not record:
                raise HTTPException(status_code=401, detail="Credenciales inválidas")
            
            estudiante_data = dict(record["e"])
            estudiante_data.pop("password", None)  # No incluir password en respuesta
            
            return {
                "success": True,
                "message": "Login exitoso",
                "data": estudiante_data
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en login: {str(e)}")