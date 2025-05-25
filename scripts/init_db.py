"""
Script para inicializar la base de datos Neo4j con datos de prueba
para el sistema de recomendación de profesores
"""
import random
from faker import Faker
from datetime import datetime
import sys

from src.database.neo4jdriver import Neo4jDriver
from src.models.estudiante import Estudiante
from src.models.profesor import Profesor
from src.models.curso import Curso
import os

fake = Faker("es_ES")
random.seed(datetime.now().timestamp())

def limpiar_base_datos():
    """Elimina todos los nodos y relaciones de la base de datos"""
    driver = Neo4jDriver()
    driver.execute_write("MATCH (n) DETACH DELETE n")
    print("Base de datos limpiada correctamente")

def crear_restricciones():
    """Crea las restricciones de unicidad en la base de datos"""
    driver = Neo4jDriver()
    
    # Verificar si las restricciones ya existen
    constraints = driver.execute_read("SHOW CONSTRAINTS")
    
    if not any("estudiante_nombre" in str(c).lower() for c in constraints):
        driver.execute_write("CREATE CONSTRAINT estudiante_nombre IF NOT EXISTS FOR (e:Estudiante) REQUIRE e.nombre IS UNIQUE")
    
    if not any("profesor_nombre" in str(c).lower() for c in constraints):
        driver.execute_write("CREATE CONSTRAINT profesor_nombre IF NOT EXISTS FOR (p:Profesor) REQUIRE p.nombre IS UNIQUE")
    
    if not any("curso_codigo" in str(c).lower() for c in constraints):
        driver.execute_write("CREATE CONSTRAINT curso_codigo IF NOT EXISTS FOR (c:Curso) REQUIRE c.codigo IS UNIQUE")
    
    print("Restricciones creadas correctamente")

"""Se crean los cursos a utilizarse en el sistema de recomendación según los datos recopilados"""
def crear_cursos() -> list:
    return [
        Curso(
            nombre="Cálculo 1",
            codigo="MAT101",
            departamento="Matemáticas",
            creditos=4
        ),
        Curso(
            nombre="Álgebra Lineal",
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
            nombre="Estadística",
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
        )
    ]

"""Se crean los estudiantes a utilizarse en el sistema de recomendación según los datos recopilados"""
def crear_estudiantes() -> list:
    carreras = [
        "Ingeniería en Ciencias de la Computación y Tecnologías de la Información", "Ingeniería Mecatrónica", 
        "Matemática Aplicada", "Física", "Bioquímica y microbiología",
    ]
    
    carnet = 24000
    cantidad_estudiantes = 70
    estudiantes = []
    #Estudiante login
    estudiantes.append(Estudiante(
        nombre="estudiante_login",
        carnet="00000",
        carrera=random.choice(carreras),
        email="estudiante@uvg.edu.gt",
        password="password123",
        pensum=2023,
        estilo_aprendizaje="mixto",
        estilo_clase="Mixto",
        promedio=1,
        grado="Primer año",
        carga_maxima=1,
        cursos_zona_minima=1,
        asistencias=1,
        veces_curso=1,
        puntuacion_total=1,
        fecha_registro=datetime.now().date(),
    ))
    
    #Admin
    estudiantes.append(Estudiante(
        nombre="admin_login",
        carnet="00001",
        carrera="Administración del Sistema",
        email="admin@uvg.edu.gt",
        password="admin123",
        pensum=2023,
        estilo_aprendizaje="mixto",
        estilo_clase="Mixto",
        promedio=1,
        grado="Primer año",
        carga_maxima=1,
        cursos_zona_minima=1,
        asistencias=1,
        veces_curso=1,
        puntuacion_total=1,
        fecha_registro=datetime.now().date(),
    ))
    for i in range(1, cantidad_estudiantes + 1):
        estudiantes.append(Estudiante(
            nombre=f"Estudiante {i}",
            pensum=2023,
            carnet=f"{carnet + i}",
            carrera=random.choice(carreras),
            email=f"estudiante{i}@universidad.edu",
            password=f"pass{i*123}",
            estilo_aprendizaje=random.choice(["mixto", "practico", "teorico"]),
            estilo_clase=random.choice(["Uso de herramientas tecnológicas", "Sin uso de herramientas tecnológicas", "Mixto"]),
            promedio=random.randint(65, 95),
            grado=f"{random.choice(['Primer', 'Segundo', 'Tercer'])} año",
            carga_maxima=random.randint(4, 6),
            cursos_zona_minima=random.randint(0, 2),
            asistencias=random.randint(0, 5),
            veces_curso=random.randint(0, 4),
            puntuacion_total=random.randint(0, 100),
            fecha_registro=fake.date_between(start_date="-2y", end_date="today"),
        ))
    return estudiantes

"""Genera los profesores a utilizarse en el sistema de recomendación según los datos recopilados"""
def crear_profesores() -> list:
    profesores = [
        {
            "nombre": "Dr. Carlos Martínez",
            "estilo": "teórico",
            "clase": "presencial",
            "exp": 15,
            "eval": 4.8,
            "aprob": 85,
            "disp": 4
        },
        {
            "nombre": "Dra. Ana Rodríguez",
            "estilo": "visual",
            "clase": "virtual",
            "exp": 10,
            "eval": 4.5,
            "aprob": 80,
            "disp": 3
        },
        {
            "nombre": "Prof. Luis García",
            "estilo": "práctico",
            "clase": "presencial",
            "exp": 8,
            "eval": 4.2,
            "aprob": 75,
            "disp": 5
        },
        {
            "nombre": "Dra. Sofía Hernández",
            "estilo": "teórico",
            "clase": "virtual",
            "exp": 20,
            "eval": 4.9,
            "aprob": 90,
            "disp": 3
        },
        {
            "nombre": "Dr. Jorge Pérez",
            "estilo": "visual",
            "clase": "presencial",
            "exp": 12,
            "eval": 4.6,
            "aprob": 82,
            "disp": 4
        },
        {
            "nombre": "MSc. Patricia López",
            "estilo": "práctico",
            "clase": "virtual",
            "exp": 6,
            "eval": 4.0,
            "aprob": 78,
            "disp": 5
        },
        {
            "nombre": "Dr. Ricardo Sánchez",
            "estilo": "teórico",
            "clase": "presencial",
            "exp": 18,
            "eval": 4.7,
            "aprob": 88,
            "disp": 2
        },
        {
            "nombre": "Dra. Elena Ramírez",
            "estilo": "visual",
            "clase": "virtual",
            "exp": 9,
            "eval": 4.3,
            "aprob": 79,
            "disp": 4
        },
        {
            "nombre": "Prof. Javier Torres",
            "estilo": "práctico",
            "clase": "presencial",
            "exp": 7,
            "eval": 4.1,
            "aprob": 76,
            "disp": 5
        },
        {
            "nombre": "Dra. Carmen Castro",
            "estilo": "teórico",
            "clase": "virtual",
            "exp": 14,
            "eval": 4.7,
            "aprob": 86,
            "disp": 3
        },
        {
            "nombre": "Dr. Fernando Díaz",
            "estilo": "visual",
            "clase": "presencial",
            "exp": 11,
            "eval": 4.4,
            "aprob": 81,
            "disp": 4
        },
        {
            "nombre": "MSc. Adriana Morales",
            "estilo": "práctico",
            "clase": "virtual",
            "exp": 5,
            "eval": 3.9,
            "aprob": 74,
            "disp": 5
        }
    ]
    
    return [Profesor(
        nombre=p["nombre"],
        estilo_enseñanza=p["estilo"],
        estilo_clase=p["clase"],
        años_experiencia=p["exp"],
        evaluacion_docente=p["eval"],
        porcentaje_aprobados=p["aprob"],
        disponibilidad=p["disp"]
    ) for p in profesores]


def crear_relaciones(driver: Neo4jDriver, cursos: list, profesores: list, estudiantes: list):
    
    asignaciones_profesor_curso = [
        ("Dr. Carlos Martínez", "MAT101"),  # Cálculo 1
        ("Dr. Carlos Martínez", "MAT104"),  # Cálculo 2

        ("Dra. Ana Rodríguez", "MAT102"),  # Álgebra Lineal
        ("Dra. Ana Rodríguez", "MAT202"),  # Matemática discreta
        
        ("Prof. Luis García", "MAT103"),   # Estadística
        ("Prof. Luis García", "MAT201"),   # Ecuaciones Diferenciales
        
        ("Dra. Sofía Hernández", "MAT201"),  # Ecuaciones Diferenciales
        ("Dra. Sofía Hernández", "MAT104"),  # Cálculo 2
        
        ("Dr. Jorge Pérez", "MAT203"),  # Algebra y geometría analítica
        ("Dr. Jorge Pérez", "MAT301"),  # Pensamiento cuantitativo

        ("MSc. Patricia López", "MAT301"),  # Pensamiento cuantitativo
        ("MSc. Patricia López", "MAT202"),  # Matemática discreta

        ("Dr. Ricardo Sánchez", "MAT101"),  # Cálculo 1
        ("Dr. Ricardo Sánchez", "MAT102"),  # Álgebra Lineal
        
        ("Dra. Elena Ramírez", "MAT103"),  # Estadística
        ("Dra. Elena Ramírez", "MAT201"),  # Ecuaciones Diferenciales
        
        ("Prof. Javier Torres", "MAT202"),  # Matemática discreta
        ("Prof. Javier Torres", "MAT203"),  # Algebra y geometría analítica
        
        ("Dra. Carmen Castro", "MAT301"),   # Pensamiento cuantitativo
        ("Dra. Carmen Castro", "MAT104"),  # Cálculo 2
        
        ("Dr. Fernando Díaz", "MAT101"),  # Cálculo 1
        ("Dr. Fernando Díaz", "MAT102"),  # Álgebra Lineal
        
        ("MSc. Adriana Morales", "MAT103"),  # Estadística
        ("MSc. Adriana Morales", "MAT201")   # Ecuaciones Diferenciales
    ]
    
    for profesor_nombre, curso_codigo in asignaciones_profesor_curso:
        driver.execute_write(
            """
            MATCH (p:Profesor {nombre: $profesor_nombre})
            MATCH (c:Curso {codigo: $curso_codigo})
            MERGE (p)-[:IMPARTE]->(c)
            """,
            profesor_nombre=profesor_nombre,
            curso_codigo=curso_codigo
        )
    
    for estudiante in estudiantes:
        cursos_aprobados = random.sample(cursos, random.randint(3, 5))
        
        for curso in cursos_aprobados:
            resultado = driver.execute_read(
                """
                MATCH (p)-[:IMPARTE]->(c:Curso {codigo: $codigo_curso})
                RETURN p.nombre as profesor_nombre
                """,
                codigo_curso=curso.codigo
            )
            
            if resultado:
                profesor_nombre = resultado[0]["profesor_nombre"]
                nota = random.randint(70, 95) if random.random() < 0.8 else random.randint(60, 69)

                driver.execute_write(
                    """
                    MATCH (e:Estudiante {nombre: $estudiante_nombre})
                    MATCH (c:Curso {codigo: $curso_codigo})
                    MERGE (e)-[:APROBÓ_CON {
                        nota: $nota,
                        fecha: date($fecha_aprobacion)
                    }]->(c)
                    """,
                    estudiante_nombre=estudiante.nombre,
                    curso_codigo=curso.codigo,
                    nota=nota,
                    fecha_aprobacion=fake.date_between(
                        start_date=estudiante.fecha_registro, 
                        end_date="today"
                    ).isoformat()
                )
                
                driver.execute_write(
                    """
                    MATCH (e:Estudiante {nombre: $estudiante_nombre})
                    MATCH (p:Profesor {nombre: $profesor_nombre})
                    MERGE (e)-[:RECOMENDACION]->(p)
                    """,
                    estudiante_nombre=estudiante.nombre,
                    profesor_nombre=profesor_nombre
                )

def comprobar_conexion():
    """Comprueba la conexión con Neo4j"""
    try:
        driver = Neo4jDriver()
        result = driver.execute_read("RETURN 1 AS test")
        if result and result[0]["test"] == 1:
            print("Conexión a Neo4j exitosa! ✅")
            return True
        else:
            print("Error de conexión a Neo4j: respuesta inesperada")
            return False
    except Exception as e:
        print(f"Error de conexión a Neo4j: {e}")
        return False

def verificar_insercion(driver: Neo4jDriver):
    """Verificación detallada de datos insertados"""
    print("\n🔍 Verificando datos insertados...")
    
    # 1. Verificar conteo de nodos
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
    
    # 2. Verificar propiedades de los nodos
    print("\n📋 Propiedades de los nodos Estudiante:")
    props = driver.execute_read("""
        MATCH (e:Estudiante)
        WITH e LIMIT 1
        RETURN keys(e) AS propiedades
    """)
    print("Propiedades encontradas:", props[0]["propiedades"] if props else "Ningún estudiante encontrado")
def main():
    """Función principal para inicializar la base de datos"""
    print("Iniciando proceso de inicialización de base de datos...")
    
    # Comprobar conexión
    if not comprobar_conexion():
        print("🛑 No se puede continuar sin conexión a Neo4j. Revisa la configuración en .env")
        sys.exit(1)
    
    # Verificar si el usuario quiere limpiar la base de datos
    respuesta = input("¿Deseas limpiar la base de datos antes de inicializarla? (s/n): ")
    if respuesta.lower() == 's':
        limpiar_base_datos()
    
    crear_restricciones()
    
    # Inicializar datos
    cursos = crear_cursos()
    estudiantes = crear_estudiantes()
    profesores = crear_profesores()
    driver = Neo4jDriver()
    crear_relaciones(driver, cursos, profesores, estudiantes)
    verificar_insercion(driver)
    
    print("\nBase de datos inicializada correctamente! 🎉")
    print("\nPuedes ejecutar el API con el comando:")
    print("python src/main.py")
    print("\nLa documentación estará disponible en http://localhost:8000/docs")

if __name__ == "__main__":
    main()