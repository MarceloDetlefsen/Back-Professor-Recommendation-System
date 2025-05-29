"""
Script para inicializar la base de datos Neo4j con datos de prueba
para el sistema de recomendación de profesores
"""
import random
from faker import Faker
from datetime import datetime
import sys
from typing import List

from src.database.neo4jdriver import Neo4jDriver
from src.models.estudiante import Estudiante
from src.models.profesor import Profesor
from src.models.curso import Curso
import os

fake = Faker("es_ES")
random.seed(datetime.now().timestamp())

def limpiar_base_datos(driver: Neo4jDriver):
    """Elimina todos los nodos y relaciones de la base de datos"""
    driver.execute_write("MATCH (n) DETACH DELETE n")
    print("Base de datos limpiada correctamente")

def crear_restricciones(driver: Neo4jDriver):
    """Crea las restricciones de unicidad en la base de datos"""
    constraints = driver.execute_read("SHOW CONSTRAINTS")
    
    if not any("estudiante_nombre" in str(c).lower() for c in constraints):
        driver.execute_write("CREATE CONSTRAINT estudiante_nombre IF NOT EXISTS FOR (e:Estudiante) REQUIRE e.nombre IS UNIQUE")
    
    if not any("profesor_nombre" in str(c).lower() for c in constraints):
        driver.execute_write("CREATE CONSTRAINT profesor_nombre IF NOT EXISTS FOR (p:Profesor) REQUIRE p.nombre IS UNIQUE")
    
    if not any("curso_codigo" in str(c).lower() for c in constraints):
        driver.execute_write("CREATE CONSTRAINT curso_codigo IF NOT EXISTS FOR (c:Curso) REQUIRE c.codigo IS UNIQUE")
    
    print("Restricciones creadas correctamente")

"""Se crean los cursos a utilizarse en el sistema de recomendación según los datos recopilados"""
def crear_cursos(driver: Neo4jDriver) -> list:
    cursos_data=[
        Curso(
            nombre="Cálculo 1",
            codigo="MAT101",
            departamento="Matemáticas",
            creditos=4
        ),
        Curso(
            nombre="Algebra Lineal",
            codigo="MAT102",
            departamento="Matemáticas",
            creditos=3
        ),
        Curso(
            nombre="Ecuaciones Diferenciales",
            codigo="MAT201",
            departamento="Matemáticas",
            creditos=4
        ),
        Curso(
            nombre="Estadística 1",
            codigo="MAT103",
            departamento="Matemáticas",
            creditos=3
        ),
        Curso(
            nombre="Cálculo 2",
            codigo="MAT104",
            departamento="Matemáticas",
            creditos=4
        ),
        Curso(
            nombre="Matemática discreta",
            codigo="MAT202",
            departamento="Matemáticas",
            creditos=3
        ),
        Curso(
            nombre="Algebra y geometría analítica",	
            codigo="MAT203",
            departamento="Matemáticas",
            creditos=4
        ),
        Curso(
            nombre="Pensamiento cuantitativo",
            codigo="MAT301",
            departamento="Matemáticas",
            creditos=5
        ),
        Curso(
            nombre="Lógica matemática",
            codigo="MAT302",
            departamento="Matemáticas",
            creditos=3
        ),
        Curso(
            nombre="Estadística 2",
            codigo="MAT303",
            departamento="Matemáticas",
            creditos=4
        ),
        Curso(
            nombre="Geometría Euclidiana",
            codigo="MAT304",
            departamento="Matemáticas",
            creditos=3
        ),
        Curso(
            nombre="Teoría de Números",
            codigo="MAT305",
            departamento="Matemáticas",
            creditos=3
        )
    ]
    cursos_creados = []
    
    for curso in cursos_data:
        try:
            result = driver.execute_write(
                """
                CREATE (c:Curso {
                    nombre: $nombre,
                    codigo: $codigo,
                    departamento: $departamento,
                    creditos: $creditos
                })
                RETURN c.nombre AS nombre, c.codigo AS codigo
                """,
                nombre=curso.nombre,
                codigo=curso.codigo,
                departamento=curso.departamento,
                creditos=curso.creditos
            )
            
            if result:
                cursos_creados.append(curso)
                print(f"✅ Curso creado: {curso.codigo}")
            else:
                print(f"❌ Falló al crear curso: {curso.codigo}")
        except Exception as e:
            print(f"🔥 Error crítico al crear curso {curso.codigo}: {str(e)}")
    
    return cursos_creados

"""Genera los profesores a utilizarse en el sistema de recomendación según los datos recopilados
Estos profesores se crean manualmente ya que se utilizan datos reales obtenidos
por parte de consultas a distintos estudiantes del departamento de matemáticas
Todos los nombres de los catedráticos a quienes se realizaron las consultas fueron reemplazados por nombres ficticios
para proteger la privacidad de los mismos"""

def crear_profesores(driver: Neo4jDriver) -> list:
    profesores_data = [
        {
            "nombre": "Carlos Martínez",
            "estilo_enseñanza": "mixto",
            "estilo_clase": "con_tecnologia",
            "años_experiencia": 15,
            "evaluacion_docente": 4.8,
            "porcentaje_aprobados": 85,
            "disponibilidad": 4
        },
        {
            "nombre": "Ana Rodríguez",
            "estilo_enseñanza": "practico",
            "estilo_clase": "mixto",
            "años_experiencia": 10,
            "evaluacion_docente": 4.5,
            "porcentaje_aprobados": 80,
            "disponibilidad": 3
        },
        {
            "nombre": "Luis García",
            "estilo_enseñanza": "teorico",
            "estilo_clase": "sin_tecnologia",
            "años_experiencia": 8,
            "evaluacion_docente": 4.2,
            "porcentaje_aprobados": 75,
            "disponibilidad": 5
        },
        {
            "nombre": "Sofía Hernández",
            "estilo_enseñanza": "mixto",
            "estilo_clase": "con_tecnologia",
            "años_experiencia": 20,
            "evaluacion_docente": 4.9,
            "porcentaje_aprobados": 90,
            "disponibilidad": 3
        },
        {
            "nombre": "Jorge Pérez",
            "estilo_enseñanza": "practico",
            "estilo_clase": "mixto",
            "años_experiencia": 12,
            "evaluacion_docente": 4.6,
            "porcentaje_aprobados": 82,
            "disponibilidad": 4
        },
        {
            "nombre": "Patricia López",
            "estilo_enseñanza": "teorico",
            "estilo_clase": "sin_tecnologia",
            "años_experiencia": 6,
            "evaluacion_docente": 4.0,
            "porcentaje_aprobados": 78,
            "disponibilidad": 5
        },
        {
            "nombre": "Ricardo Sánchez",
            "estilo_enseñanza": "mixto",
            "estilo_clase": "con_tecnologia",
            "años_experiencia": 18,
            "evaluacion_docente": 4.7,
            "porcentaje_aprobados": 88,
            "disponibilidad": 2
        },
        {
            "nombre": "Elena Ramírez",
            "estilo_enseñanza": "practico",
            "estilo_clase": "mixto",
            "años_experiencia": 9,
            "evaluacion_docente": 4.3,
            "porcentaje_aprobados": 79,
            "disponibilidad": 4
        },
        {
            "nombre": "Javier Torres",
            "estilo_enseñanza": "teorico",
            "estilo_clase": "sin_tecnologia",
            "años_experiencia": 7,
            "evaluacion_docente": 4.1,
            "porcentaje_aprobados": 76,
            "disponibilidad": 5
        },
        {
            "nombre": "Carmen Castro",
            "estilo_enseñanza": "mixto",
            "estilo_clase": "con_tecnologia",
            "años_experiencia": 14,
            "evaluacion_docente": 4.7,
            "porcentaje_aprobados": 86,
            "disponibilidad": 3
        },
        {
            "nombre": "Fernando Díaz",
            "estilo_enseñanza": "practico",
            "estilo_clase": "mixto",
            "años_experiencia": 11,
            "evaluacion_docente": 4.4,
            "porcentaje_aprobados": 81,
            "disponibilidad": 4
        },
        {
            "nombre": "Adriana Morales",
            "estilo_enseñanza": "teorico",
            "estilo_clase": "sin_tecnologia",
            "años_experiencia": 5,
            "evaluacion_docente": 3.9,
            "porcentaje_aprobados": 74,
            "disponibilidad": 5
        },
        {
            "nombre": "Renato Sagastume",
            "estilo_enseñanza": "teorico",
            "estilo_clase": "con_tecnologia",
            "años_experiencia": 9,
            "evaluacion_docente": 3.8,
            "porcentaje_aprobados": 65,
            "disponibilidad": 3
        },
        {
            "nombre": "Eusebio Francesco",
            "estilo_enseñanza": "mixto",
            "estilo_clase": "sin_tecnologia",
            "años_experiencia": 4,
            "evaluacion_docente": 4.3,
            "porcentaje_aprobados": 87,
            "disponibilidad": 4
        },
        {
            "nombre": "Alfredo Bustamante",
            "estilo_enseñanza": "practico",
            "estilo_clase": "con_tecnologia",
            "años_experiencia": 4,
            "evaluacion_docente": 3.8,
            "porcentaje_aprobados": 86,
            "disponibilidad": 2
        },
        {
            "nombre": "Matteo Joronen",
            "estilo_enseñanza": "mixto",
            "estilo_clase": "sin_tecnologia",
            "años_experiencia": 7,
            "evaluacion_docente": 4.4,
            "porcentaje_aprobados": 81,
            "disponibilidad": 4
        },
        {
            "nombre": "Francesco Zampano",
            "estilo_enseñanza": "practico",
            "estilo_clase": "sin_tecnologia",
            "años_experiencia": 9,
            "evaluacion_docente": 4.7,
            "porcentaje_aprobados": 91,
            "disponibilidad": 5
        },
        {
            "nombre": "Marcos Alonso",
            "estilo_enseñanza": "teorico",
            "estilo_clase": "sin_tecnologia",
            "años_experiencia": 2,
            "evaluacion_docente": 3.6,
            "porcentaje_aprobados": 70,
            "disponibilidad": 2
        },
        {
            "nombre": "Henry Martin",
            "estilo_enseñanza": "mixto",
            "estilo_clase": "con_tecnologia",
            "años_experiencia": 13,
            "evaluacion_docente": 4.0,
            "porcentaje_aprobados": 92,
            "disponibilidad": 2
        },
        {
            "nombre": "Oliver Giroud",
            "estilo_enseñanza": "teorico",
            "estilo_clase": "sin_tecnologia",
            "años_experiencia": 6,
            "evaluacion_docente": 4.1,
            "porcentaje_aprobados": 84,
            "disponibilidad": 4
        }
    ]
    profesores_creados = []
    for profesor_data in profesores_data:
        try:
            profesor = Profesor(**profesor_data)
            puntuacion = profesor.calcular_puntuacion()
            result = driver.execute_write(
                """
                CREATE (p:Profesor {
                    nombre: $nombre,
                    estilo_enseñanza: $estilo_enseñanza,
                    estilo_clase: $estilo_clase,
                    años_experiencia: $años_experiencia,
                    evaluacion_docente: $evaluacion_docente,
                    porcentaje_aprobados: $porcentaje_aprobados,
                    disponibilidad: $disponibilidad,
                    puntuacion_total: $puntuacion_total
                })
                RETURN p.nombre AS nombre
                """,
                nombre=profesor.nombre,
                estilo_enseñanza=profesor.estilo_enseñanza,
                estilo_clase=profesor.estilo_clase,
                años_experiencia=profesor.años_experiencia,
                evaluacion_docente=profesor.evaluacion_docente,
                porcentaje_aprobados=profesor.porcentaje_aprobados,
                disponibilidad=profesor.disponibilidad,
                puntuacion_total=puntuacion
            )
            if result:
                profesores_creados.append(profesor)
                print(f"✅ Profesor creado: {profesor.nombre}")
            else:
                print(f"❌ Falló al crear profesor: {profesor.nombre}")
        except Exception as e:
            print(f"🔥 Error al crear profesor {profesor_data.get('nombre', '')}: {str(e)}")
    
    return profesores_creados
        
"""Prueba para debug, intentar escribir en la base de datos"""
def comprobar_conexion(driver: Neo4jDriver):
    try:
        result = driver.execute_write("CREATE (t:Test) RETURN t")
        driver.execute_write("MATCH (t:Test) DELETE t")
        if result:
            print("Conexión a Neo4j con permisos de escritura exitosa! ✅")
            return True
        else:
            print("Error: No se pudo escribir en Neo4j")
            return False
    except Exception as e:
        print(f"Error de conexión a Neo4j: {e}")
        return False


"""Se crean los estudiantes a utilizarse en el sistema de recomendación según los datos recopilados
Se consideró crer estudiantes de forma al azar pero con valores lógicos ya que dentro de una institución educativa existen
estudiantes de todo tipo, de esta manear no utilizamos datos idóneos para el sistema de recomendación"""
def crear_estudiantes(driver=None) -> list:
    """Genera los estudiantes en el sistema sin fecha_registro"""
    carreras = ["Ingeniería en Ciencias de la Computación", "Matemática Aplicada", "Física", "Ingeniería Mecánica", "Ingeniería Industrial",
                "Ingeniería civil arquitectónica", "Ingeniería química", "Ingeniería biomédica", "Bioquímica y microbiología", "Química", "Química Farmacéutica",
                "Arquitectura", "Ingeniería electrónica"]
    estudiantes = []
    for i in range(1, 99):
        estudiantes.append({
            "nombre": fake.name(),
            "carnet": f"25{str(i).zfill(3)}",
            "carrera": random.choice(carreras),
            "pensum": 2025,
            "email": f"estudiante{i}@uvg.edu.gt",
            "password": f"pass{i*123}",
            "estilo_aprendizaje": random.choice(["mixto", "practico", "teorico"]),
            "estilo_clase": random.choice(["con_tecnologia", "sin_tecnologia", "mixto"]),
            "promedio": random.randint(45, 95),
            "grado": f"{random.choice(['Primer', 'Segundo', 'Tercer', 'Cuarto', 'Quinto', 'Sexto'])} año",
            "carga_maxima": random.randint(4, 6),
            "cursos_zona_minima": random.randint(0, 3),
            "asistencias": random.randint(0, 5),
            "veces_curso": random.randint(0, 5),
            "role": "estudiante"
        })

    estudiantes.extend([
        {
            "nombre": "Usuario de Prueba",
            "carnet": "00001",
            "carrera": random.choice(carreras),
            "pensum": 2025,
            "email": "estudiante@uvg.edu.gt",
            "password": "password123",
            "estilo_aprendizaje": "mixto",
            "estilo_clase": "con_tecnologia",
            "promedio": 73,
            "grado": "Segundo año",
            "carga_maxima": 6,
            "cursos_zona_minima": 5,
            "asistencias": 4,
            "veces_curso": 1,
            "role": "estudiante"
        },
        {
            "nombre": "ADMINISTRADOR UVG",
            "carnet": "77777",
            "carrera": "Administración del Sistema",
            "pensum": 2023,
            "email": "admin@uvg.edu.gt",
            "password": "admin123",
            "estilo_aprendizaje": "mixto",
            "estilo_clase": "mixto",
            "promedio": 1,
            "grado": "Primer año",
            "carga_maxima": 5,
            "cursos_zona_minima": 2,
            "asistencias": 2,
            "veces_curso": 3,
            "role": "admin"
        }
    ])
    
    estudiantes_creados = []
    for e_data in estudiantes:
        try:
            estudiante = Estudiante(**e_data)
            puntuacion = estudiante.calcular_puntuacion()
            
            result = driver.execute_write(
                """
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
                    role: $role
                })
                RETURN e
                """,
                **estudiante.dict(exclude={"puntuacion_total"}),
                puntuacion_total=puntuacion
            )
            
            if result:
                estudiantes_creados.append(estudiante)
                print(f"✅ Estudiante creado: {estudiante.carnet}")
            else:
                print(f"❌ Falló al crear estudiante: {estudiante.carnet}")
        except Exception as e:
            print(f"🔥 Error al crear estudiante {e_data.get('carnet', '')}: {str(e)}")
    
    return estudiantes_creados

def crear_relaciones(driver: Neo4jDriver, cursos: List[Curso],profesores: List[Profesor], estudiantes: List[Estudiante]):
    """Crea todas las relaciones entre nodos en la base de datos"""
    asignaciones_profesor_curso = [
        ("Carlos Martínez", "MAT101"), ("Carlos Martínez", "MAT104"),
        ("Ana Rodríguez", "MAT102"), ("Ana Rodríguez", "MAT202"),
        ("Luis García", "MAT103"), ("Luis García", "MAT201"),
        ("Sofía Hernández", "MAT201"), ("Sofía Hernández", "MAT104"),
        ("Jorge Pérez", "MAT203"), ("Jorge Pérez", "MAT301"),
        ("Patricia López", "MAT301"), ("Patricia López", "MAT202"),
        ("Ricardo Sánchez", "MAT101"), ("Ricardo Sánchez", "MAT102"),
        ("Elena Ramírez", "MAT103"), ("Elena Ramírez", "MAT201"),
        ("Javier Torres", "MAT202"), ("Javier Torres", "MAT203"),
        ("Carmen Castro", "MAT301"), ("Carmen Castro", "MAT104"),
        ("Fernando Díaz", "MAT101"), ("Fernando Díaz", "MAT102"),
        ("Adriana Morales", "MAT103"), ("Adriana Morales", "MAT201"),
        ("Carlos Martínez", "MAT302"),("Patricia López", "MAT302"),
        ("Javier Torres", "MAT302"), ("Renato Sagastume", "MAT303"),
        ("Eusebio Francesco", "MAT304"),("Alfredo Bustamante", "MAT305"),
        ("Matteo Joronen", "MAT303"),("Francesco Zampano", "MAT304"),
        ("Marcos Alonso", "MAT305"),("Henry Martin", "MAT303"),
        ("Oliver Giroud", "MAT304")
        ]
    
    print("\nCreando relaciones PROFESOR-IMPARTE-CURSO...")
    for profesor_nombre, curso_codigo in asignaciones_profesor_curso:
        try:
            result = driver.execute_write(
                """
                MATCH (p:Profesor {nombre: $profesor_nombre})
                MATCH (c:Curso {codigo: $curso_codigo})
                MERGE (p)-[r:IMPARTE]->(c)
                RETURN r
                """,
                profesor_nombre=profesor_nombre,
                curso_codigo=curso_codigo
            )
            print(f"Relación IMPARTE creada: {profesor_nombre} -> {curso_codigo}: {'Éxito' if result else 'Falló'}")
        except Exception as e:
            print(f"Error al crear relación IMPARTE {profesor_nombre} -> {curso_codigo}: {str(e)}")
    
    print("\nCreando relaciones ESTUDIANTE-APROBÓ_CON-CURSO y RECOMENDACIONES...")
    for estudiante in estudiantes:
        try:
            cursos_aprobados = random.sample(cursos, random.randint(3, 5))
            
            for curso in cursos_aprobados:

                profesor_result = driver.execute_read(
                    """
                    MATCH (p:Profesor)-[:IMPARTE]->(c:Curso {codigo: $codigo_curso})
                    RETURN p.nombre as profesor_nombre LIMIT 1
                    """,
                    codigo_curso=curso.codigo
                )
                
                if profesor_result:
                    profesor_nombre = profesor_result[0]["profesor_nombre"]
                    nota = random.randint(70, 95) if random.random() < 0.8 else random.randint(60, 69)
                    
                    # Crear relación APROBÓ_CON
                    driver.execute_write(
                        """
                        MATCH (e:Estudiante {carnet: $carnet})
                        MATCH (c:Curso {codigo: $codigo_curso})
                        MERGE (e)-[r:APROBÓ_CON {nota: $nota}]->(c)
                        RETURN r
                        """,
                        carnet=estudiante.carnet,
                        codigo_curso=curso.codigo,
                        nota=nota
                    )
                    
                    # Crear relación RECOMENDACION
                    driver.execute_write(
                        """
                        MATCH (e:Estudiante {carnet: $carnet})
                        MATCH (p:Profesor {nombre: $profesor_nombre})
                        MERGE (e)-[r:RECOMENDACION]->(p)
                        RETURN r
                        """,
                        carnet=estudiante.carnet,
                        profesor_nombre=profesor_nombre
                    )
                    print(f"Relaciones creadas para {estudiante.carnet} con curso {curso.codigo}")
                else:
                    print(f"⚠️ No se encontró profesor para el curso {curso.codigo}")
        except Exception as e:
            print(f"🔥 Error al procesar estudiante {getattr(estudiante, 'carnet', '')}: {str(e)}")

    """Comprueba la conexión con Neo4j"""
def comprobar_conexion(driver:Neo4jDriver) -> bool:
    try:
        result = driver.execute_read("RETURN 1 AS test")
        driver.close()
        if result and result[0]["test"] == 1:
            print("Conexión a Neo4j exitosa! ✅")
            return True
        print("Error de conexión a Neo4j: respuesta inesperada")
        return False
    except Exception as e:
        print(f"Error de conexión a Neo4j: {e}")
        return False

"""Comprueba la inserción de datos"""
def verificar_insercion(driver:Neo4jDriver):
    """Verificación detallada de datos insertados"""
    print("\n🔍 Verificando datos insertados...")
    
    try:
        result = driver.execute_read("""
            MATCH (n)
            RETURN 
                count(n) AS total_nodos,
                sum(CASE WHEN 'Estudiante' IN labels(n) THEN 1 ELSE 0 END) AS estudiantes,
                sum(CASE WHEN 'Profesor' IN labels(n) THEN 1 ELSE 0 END) AS profesores,
                sum(CASE WHEN 'Curso' IN labels(n) THEN 1 ELSE 0 END) AS cursos
        """)
        
        if result:
            data = result[0]
            print(f"Total nodos: {data['total_nodos']}")
            print(f"- Estudiantes: {data['estudiantes']}")
            print(f"- Profesores: {data['profesores']}")
            print(f"- Cursos: {data['cursos']}")
            
            if data['profesores'] == 0 or data['estudiantes'] == 0:
                print("\n⚠️ Advertencia: No se encontraron profesores o estudiantes")
                print("Posibles causas:")
                print("1. Validación fallida de los datos")
                print("2. Restricciones de la base de datos")
                print("3. Errores silenciosos en las transacciones")
                
                print("\nMuestra de nodos creados:")
                sample = driver.execute_read("MATCH (n) RETURN labels(n) as tipo, n LIMIT 5")
                for item in sample:
                    print(f"Tipo: {item['tipo']}, Datos: {dict(item['n'])}")
    except Exception as e:
        print(f"Error durante verificación: {str(e)}")

"""Funcion principal para inicializar la base de datos"""
def main():
    driver = Neo4jDriver()
    print("Inicializando la base de datos...")
    if not comprobar_conexion(driver):
        sys.exit(1)
    try:
        if input("¿Deseas limpiar la base de datos? (s/n): ").lower() == 's':
            limpiar_base_datos(driver)
        
        crear_restricciones(driver)
        
        print("\n=== Creando Cursos ===")
        cursos = crear_cursos(driver)
        
        print("\n=== Creando Profesores ===")
        profesores = crear_profesores(driver)
        
        print("\n=== Creando Estudiantes ===")
        estudiantes = crear_estudiantes(driver)
        
        print("\n=== Creando Relaciones ===")
        crear_relaciones(driver, cursos, profesores, estudiantes)
        
        print("\n=== Verificación Final ===")
        verificar_insercion(driver)
        
        print("\n✅ Base de datos inicializada correctamente!")
    except Exception as e:
        print(f"🔥 Error crítico durante inicialización: {str(e)}")
    finally:
        driver.close()

if __name__ == "__main__":
    main()