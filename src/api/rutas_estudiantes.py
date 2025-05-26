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
                role: $role,
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

# Asignar estudiante a un curso con un profesor específico
@router.post("/{carnet}/asignar-curso")
async def asignar_estudiante_a_curso(
    carnet: str,
    datos_asignacion: dict = Body(...)
):
    """
    Asigna un estudiante a un curso específico impartido por un profesor específico
    RESTRICCIÓN: Un estudiante solo puede estar inscrito con UN profesor por curso
    
    Args:
        carnet: Carnet del estudiante
        datos_asignacion: Dict con codigo_curso y nombre_profesor
        
    Returns:
        Confirmación de asignación
    """
    try:
        # Validar datos requeridos
        if "codigo_curso" not in datos_asignacion:
            raise HTTPException(status_code=400, detail="Se requiere el código del curso")
        
        if "nombre_profesor" not in datos_asignacion:
            raise HTTPException(status_code=400, detail="Se requiere el nombre del profesor")
        
        codigo_curso = datos_asignacion["codigo_curso"]
        nombre_profesor = datos_asignacion["nombre_profesor"]
        
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Verificar que el estudiante existe
            query_estudiante = """
            MATCH (e:Estudiante {carnet: $carnet})
            RETURN e
            """
            result_estudiante = session.run(query_estudiante, carnet=carnet)
            estudiante = result_estudiante.single()
            
            if not estudiante:
                raise HTTPException(status_code=404, detail=f"No se encontró al estudiante con carnet {carnet}")
            
            # Verificar que el curso existe
            query_curso = """
            MATCH (c:Curso {codigo: $codigo_curso})
            RETURN c
            """
            result_curso = session.run(query_curso, codigo_curso=codigo_curso)
            curso = result_curso.single()
            
            if not curso:
                raise HTTPException(status_code=404, detail=f"No se encontró el curso con código {codigo_curso}")
            
            # Verificar que el profesor existe
            query_profesor = """
            MATCH (p:Profesor {nombre: $nombre_profesor})
            RETURN p
            """
            result_profesor = session.run(query_profesor, nombre_profesor=nombre_profesor)
            profesor = result_profesor.single()
            
            if not profesor:
                raise HTTPException(status_code=404, detail=f"No se encontró al profesor {nombre_profesor}")
            
            # Verificar que el profesor imparte el curso
            query_imparte = """
            MATCH (p:Profesor {nombre: $nombre_profesor})-[:IMPARTE]->(c:Curso {codigo: $codigo_curso})
            RETURN p, c
            """
            result_imparte = session.run(query_imparte, nombre_profesor=nombre_profesor, codigo_curso=codigo_curso)
            imparte = result_imparte.single()
            
            if not imparte:
                raise HTTPException(status_code=400, detail=f"El profesor {nombre_profesor} no imparte el curso {codigo_curso}")
            
            # NUEVA VALIDACIÓN: Verificar si el estudiante ya está inscrito en el curso (con cualquier profesor)
            query_ya_inscrito = """
            MATCH (e:Estudiante {carnet: $carnet})-[r:INSCRITO_EN]->(c:Curso {codigo: $codigo_curso})
            RETURN r.profesor as profesor_actual, r.fecha_inscripcion as fecha_inscripcion
            """
            result_ya_inscrito = session.run(query_ya_inscrito, carnet=carnet, codigo_curso=codigo_curso)
            inscripcion_existente = result_ya_inscrito.single()
            
            if inscripcion_existente:
                profesor_actual = inscripcion_existente["profesor_actual"]
                raise HTTPException(
                    status_code=400, 
                    detail=f"El estudiante ya está inscrito en el curso {codigo_curso} con el profesor {profesor_actual}. No se puede cambiar de profesor una vez inscrito."
                )
            
            # Si llegamos aquí, el estudiante NO está inscrito en el curso, proceder con la inscripción
            query_inscribir = """
            MATCH (e:Estudiante {carnet: $carnet})
            MATCH (c:Curso {codigo: $codigo_curso})
            MATCH (p:Profesor {nombre: $nombre_profesor})
            CREATE (e)-[:INSCRITO_EN {
                fecha_inscripcion: datetime(),
                profesor: $nombre_profesor,
                estado: 'activo'
            }]->(c)
            RETURN e, c, p
            """
            
            result_inscribir = session.run(
                query_inscribir, 
                carnet=carnet, 
                codigo_curso=codigo_curso, 
                nombre_profesor=nombre_profesor
            )
            inscripcion = result_inscribir.single()
            
            if not inscripcion:
                raise HTTPException(status_code=500, detail="Error al inscribir al estudiante en el curso")
            
            return {
                "success": True,
                "message": f"Estudiante {carnet} inscrito exitosamente en el curso {codigo_curso} con el profesor {nombre_profesor}",
                "data": {
                    "carnet_estudiante": carnet,
                    "codigo_curso": codigo_curso,
                    "nombre_profesor": nombre_profesor,
                    "fecha_inscripcion": "datetime()",
                    "estado": "activo"
                }
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al asignar estudiante a curso: {str(e)}")


# Verificar inscripción actual en un curso
@router.get("/{carnet}/curso/{codigo_curso}/inscripcion")
async def verificar_inscripcion_curso(carnet: str, codigo_curso: str):
    """
    Verifica si un estudiante está inscrito en un curso específico y con qué profesor
    
    Args:
        carnet: Carnet del estudiante
        codigo_curso: Código del curso
        
    Returns:
        Información de la inscripción si existe, o null si no está inscrito
    """
    try:
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Verificar inscripción
            query = """
            MATCH (e:Estudiante {carnet: $carnet})-[r:INSCRITO_EN]->(c:Curso {codigo: $codigo_curso})
            RETURN e.nombre as nombre_estudiante, 
                   c.nombre as nombre_curso, 
                   r.profesor as profesor,
                   r.fecha_inscripcion as fecha_inscripcion,
                   r.estado as estado
            """
            result = session.run(query, carnet=carnet, codigo_curso=codigo_curso)
            inscripcion = result.single()
            
            if not inscripcion:
                return {
                    "success": True,
                    "message": f"El estudiante {carnet} no está inscrito en el curso {codigo_curso}",
                    "data": None,
                    "inscrito": False
                }
            
            return {
                "success": True,
                "message": f"El estudiante {carnet} está inscrito en el curso {codigo_curso}",
                "data": {
                    "carnet_estudiante": carnet,
                    "nombre_estudiante": inscripcion["nombre_estudiante"],
                    "codigo_curso": codigo_curso,
                    "nombre_curso": inscripcion["nombre_curso"],
                    "profesor": inscripcion["profesor"],
                    "fecha_inscripcion": str(inscripcion["fecha_inscripcion"]) if inscripcion["fecha_inscripcion"] else None,
                    "estado": inscripcion["estado"]
                },
                "inscrito": True
            }
        finally:
            session.close()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al verificar inscripción: {str(e)}")


# Obtener profesores disponibles para un curso (que no sean el actual del estudiante)
@router.get("/{carnet}/curso/{codigo_curso}/profesores-disponibles")
async def obtener_profesores_disponibles_para_curso(carnet: str, codigo_curso: str):
    """
    Obtiene la lista de profesores que imparten un curso específico.
    Si el estudiante ya está inscrito, muestra todos los profesores pero indica cuál es el actual.
    
    Args:
        carnet: Carnet del estudiante
        codigo_curso: Código del curso
        
    Returns:
        Lista de profesores que imparten el curso con información de disponibilidad
    """
    try:
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Verificar si el estudiante ya está inscrito en el curso
            query_inscripcion_actual = """
            MATCH (e:Estudiante {carnet: $carnet})-[r:INSCRITO_EN]->(c:Curso {codigo: $codigo_curso})
            RETURN r.profesor as profesor_actual
            """
            result_inscripcion = session.run(query_inscripcion_actual, carnet=carnet, codigo_curso=codigo_curso)
            inscripcion_record = result_inscripcion.single()
            profesor_actual = inscripcion_record["profesor_actual"] if inscripcion_record else None
            
            # Obtener todos los profesores que imparten el curso
            query_profesores = """
            MATCH (p:Profesor)-[:IMPARTE]->(c:Curso {codigo: $codigo_curso})
            RETURN p.nombre as nombre,
                   p.departamento as departamento,
                   p.email as email,
                   p.especializacion as especializacion
            ORDER BY p.nombre
            """
            result_profesores = session.run(query_profesores, codigo_curso=codigo_curso)
            profesores = []
            
            for record in result_profesores:
                profesor_info = {
                    "nombre": record["nombre"],
                    "departamento": record["departamento"],
                    "email": record["email"],
                    "especializacion": record["especializacion"],
                    "es_profesor_actual": record["nombre"] == profesor_actual,
                    "disponible_para_inscripcion": profesor_actual is None  # Solo disponible si no está inscrito
                }
                profesores.append(profesor_info)
            
            return {
                "success": True,
                "message": f"Se encontraron {len(profesores)} profesores para el curso {codigo_curso}",
                "data": {
                    "codigo_curso": codigo_curso,
                    "carnet_estudiante": carnet,
                    "ya_inscrito": profesor_actual is not None,
                    "profesor_actual": profesor_actual,
                    "profesores": profesores
                }
            }
        finally:
            session.close()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener profesores disponibles: {str(e)}")

@router.delete("/{carnet}/desasignar-curso/{codigo_curso}")
async def desasignar_estudiante_de_curso(carnet: str, codigo_curso: str):
    """
    Desasigna un estudiante de un curso específico
    
    Args:
        carnet: Carnet del estudiante
        codigo_curso: Código del curso
        
    Returns:
        Confirmación de desasignación
    """
    try:
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Verificar que existe la relación de inscripción
            query_existe = """
            MATCH (e:Estudiante {carnet: $carnet})-[r:INSCRITO_EN]->(c:Curso {codigo: $codigo_curso})
            RETURN e, r, c
            """
            result_existe = session.run(query_existe, carnet=carnet, codigo_curso=codigo_curso)
            inscripcion = result_existe.single()
            
            if not inscripcion:
                raise HTTPException(
                    status_code=404, 
                    detail=f"No se encontró inscripción del estudiante {carnet} en el curso {codigo_curso}"
                )
            
            # Eliminar la relación de inscripción
            query_eliminar = """
            MATCH (e:Estudiante {carnet: $carnet})-[r:INSCRITO_EN]->(c:Curso {codigo: $codigo_curso})
            DELETE r
            RETURN COUNT(r) as deleted_count
            """
            result_eliminar = session.run(query_eliminar, carnet=carnet, codigo_curso=codigo_curso)
            eliminado = result_eliminar.single()
            
            if eliminado["deleted_count"] == 0:
                raise HTTPException(status_code=500, detail="Error al desasignar estudiante del curso")
            
            return {
                "success": True,
                "message": f"Estudiante {carnet} desasignado exitosamente del curso {codigo_curso}"
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al desasignar estudiante de curso: {str(e)}")

@router.get("/{carnet}/cursos")
async def obtener_cursos_estudiante(carnet: str):
    """
    Obtiene todos los cursos en los que está inscrito un estudiante
    
    Args:
        carnet: Carnet del estudiante
        
    Returns:
        Lista de cursos del estudiante
    """
    try:
        driver = Neo4jDriver()
        session = driver.get_session()
        try:
            # Verificar que el estudiante existe
            query_estudiante = """
            MATCH (e:Estudiante {carnet: $carnet})
            RETURN e
            """
            result_estudiante = session.run(query_estudiante, carnet=carnet)
            estudiante = result_estudiante.single()
            
            if not estudiante:
                raise HTTPException(status_code=404, detail=f"No se encontró al estudiante con carnet {carnet}")
            
            # Obtener cursos del estudiante
            query_cursos = """
            MATCH (e:Estudiante {carnet: $carnet})-[r:INSCRITO_EN]->(c:Curso)
            RETURN c, r.profesor as profesor, r.fecha_inscripcion as fecha_inscripcion, r.estado as estado
            ORDER BY c.nombre
            """
            result_cursos = session.run(query_cursos, carnet=carnet)
            cursos = []
            
            for record in result_cursos:
                curso_data = dict(record["c"])
                curso_data["profesor"] = record["profesor"]
                curso_data["fecha_inscripcion"] = str(record["fecha_inscripcion"]) if record["fecha_inscripcion"] else None
                curso_data["estado"] = record["estado"]
                cursos.append(curso_data)
            
            return {
                "success": True,
                "message": f"Se encontraron {len(cursos)} cursos para el estudiante {carnet}",
                "data": cursos
            }
        finally:
            session.close()
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener cursos del estudiante: {str(e)}")