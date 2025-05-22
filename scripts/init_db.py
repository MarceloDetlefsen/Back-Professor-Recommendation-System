"""
Script para inicializar la base de datos Neo4j con datos de prueba
para el sistema de recomendación de profesores
"""

import sys
from src.database.neo4jdriver import Neo4jDriver
from src.models.estudiante import Estudiante
from src.models.profesor import Profesor
from src.models.curso import Curso
import os

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

def crear_cursos():
    """Crea cursos de ejemplo en la base de datos"""
    driver = Neo4jDriver()
    
    cursos = [
        Curso(nombre="Cálculo 1", codigo="MAT103", departamento="Matemáticas", creditos=4),
        Curso(nombre="Física General", codigo="FIS101", departamento="Física", creditos=5),
        Curso(nombre="Programación Básica", codigo="INF110", departamento="Informática", creditos=3),
        Curso(nombre="Estadística", codigo="EST201", departamento="Matemáticas", creditos=3),
        Curso(nombre="Bases de Datos", codigo="INF210", departamento="Informática", creditos=4)
    ]
    
    for curso in cursos:
        query = """
        MERGE (c:Curso {
            nombre: $nombre,
            codigo: $codigo,
            departamento: $departamento,
            creditos: $creditos
        })
        RETURN c
        """
        
        driver.execute_write(
            query,
            nombre=curso.nombre,
            codigo=curso.codigo,
            departamento=curso.departamento,
            creditos=curso.creditos
        )
    
    print(f"Se han creado {len(cursos)} cursos de ejemplo")

def crear_estudiantes():
    """Crea estudiantes de ejemplo en la base de datos"""
    estudiantes = [
        Estudiante(nombre="Juan Pérez", estilo_aprendizaje="visual", estilo_clase="presencial", promedio=85, asistencias=4, veces_curso=1),
        Estudiante(nombre="María López", estilo_aprendizaje="teórico", estilo_clase="virtual", promedio=92, asistencias=5, veces_curso=1),
        Estudiante(nombre="Carlos Rodríguez", estilo_aprendizaje="práctico", estilo_clase="presencial", promedio=78, asistencias=3, veces_curso=2),
        Estudiante(nombre="Ana Martínez", estilo_aprendizaje="visual", estilo_clase="virtual", promedio=88, asistencias=4, veces_curso=1),
        Estudiante(nombre="Pedro Gómez", estilo_aprendizaje="teórico", estilo_clase="presencial", promedio=75, asistencias=2, veces_curso=3)
    ]
    
    for estudiante in estudiantes:
        estudiante.calcular_puntuacion()
        
        query = """
        MERGE (e:Estudiante {
            nombre: $nombre,
            estilo_aprendizaje: $estilo_aprendizaje,
            estilo_clase: $estilo_clase,
            promedio: $promedio,
            asistencias_curso_anterior: $asistencias,
            veces_que_llevo_curso: $veces_curso,
            puntuacion_total: $puntuacion_total
        })
        RETURN e
        """
        
        driver = Neo4jDriver()
        driver.execute_write(
            query,
            nombre=estudiante.nombre,
            estilo_aprendizaje=estudiante.estilo_aprendizaje,
            estilo_clase=estudiante.estilo_clase,
            promedio=estudiante.promedio,
            asistencias=estudiante.asistencias,
            veces_curso=estudiante.veces_curso,
            puntuacion_total=estudiante.puntuacion_total
        )
    
    print(f"Se han creado {len(estudiantes)} estudiantes de ejemplo")

def crear_profesores():
    """Crea profesores de ejemplo en la base de datos"""
    profesores = [
        Profesor(nombre="Dr. Martínez", estilo_enseñanza="visual", estilo_clase="presencial", años_experiencia=10, evaluacion_docente=4.5, porcentaje_aprobados=85, disponibilidad=4),
        Profesor(nombre="Dra. González", estilo_enseñanza="teórico", estilo_clase="virtual", años_experiencia=15, evaluacion_docente=4.8, porcentaje_aprobados=90, disponibilidad=3),
        Profesor(nombre="Prof. Sánchez", estilo_enseñanza="práctico", estilo_clase="presencial", años_experiencia=8, evaluacion_docente=4.2, porcentaje_aprobados=78, disponibilidad=5),
        Profesor(nombre="Dra. Ramírez", estilo_enseñanza="visual", estilo_clase="virtual", años_experiencia=12, evaluacion_docente=4.6, porcentaje_aprobados=88, disponibilidad=4),
        Profesor(nombre="Dr. Torres", estilo_enseñanza="teórico", estilo_clase="presencial", años_experiencia=20, evaluacion_docente=4.9, porcentaje_aprobados=92, disponibilidad=2)
    ]
    
    for profesor in profesores:
        profesor.calcular_puntuacion()
        
        query = """
        MERGE (p:Profesor {
            nombre: $nombre,
            estilo_enseñanza: $estilo_enseñanza,
            estilo_clase: $estilo_clase,
            años_experiencia: $años_experiencia,
            evaluacion_docente: $evaluacion_docente,
            porcentaje_aprobados: $porcentaje_aprobados,
            disponibilidad: $disponibilidad,
            puntuacion_total: $puntuacion_total
        })
        RETURN p
        """
        
        driver = Neo4jDriver()
        driver.execute_write(
            query,
            nombre=profesor.nombre,
            estilo_enseñanza=profesor.estilo_enseñanza,
            estilo_clase=profesor.estilo_clase,
            años_experiencia=profesor.años_experiencia,
            evaluacion_docente=profesor.evaluacion_docente,
            porcentaje_aprobados=profesor.porcentaje_aprobados,
            disponibilidad=profesor.disponibilidad,
            puntuacion_total=profesor.puntuacion_total
        )
    
    print(f"Se han creado {len(profesores)} profesores de ejemplo")

def crear_relaciones():
    """Crea relaciones entre estudiantes, profesores y cursos"""
    driver = Neo4jDriver()
    
    # Relaciones entre profesores y cursos
    relaciones_profesor_curso = [
        ("Dr. Martínez", "MAT103"),
        ("Dra. González", "FIS101"),
        ("Prof. Sánchez", "INF110"),
        ("Dra. Ramírez", "EST201"),
        ("Dr. Torres", "INF210"),
        ("Dr. Martínez", "EST201"),
        ("Dra. González", "MAT103")
    ]
    
    for profesor, curso in relaciones_profesor_curso:
        driver.execute_write(
            """
            MATCH (p:Profesor {nombre: $nombre_profesor})
            MATCH (c:Curso {codigo: $codigo_curso})
            MERGE (p)-[r:IMPARTE]->(c)
            RETURN p, r, c
            """,
            nombre_profesor=profesor,
            codigo_curso=curso
        )
    
    # Relaciones de aprobación entre estudiantes y cursos
    aprobaciones = [
        ("Juan Pérez", "MAT103", "Dr. Martínez"),
        ("María López", "FIS101", "Dra. González"),
        ("Carlos Rodríguez", "INF110", "Prof. Sánchez"),
        ("Ana Martínez", "EST201", "Dra. Ramírez"),
        ("Pedro Gómez", "INF210", "Dr. Torres"),
        ("Juan Pérez", "EST201", "Dr. Martínez"),
        ("María López", "MAT103", "Dra. González")
    ]
    
    for estudiante, curso, profesor in aprobaciones:
        driver.execute_write(
            """
            MATCH (e:Estudiante {nombre: $nombre_estudiante})
            MATCH (p:Profesor {nombre: $nombre_profesor})
            MATCH (c:Curso {codigo: $codigo_curso})
            MERGE (e)-[r:APROBÓ_CON]->(c)
            RETURN e, r, c
            """,
            nombre_estudiante=estudiante,
            nombre_profesor=profesor,
            codigo_curso=curso
        )
    
    print(f"Se han creado {len(relaciones_profesor_curso)} relaciones entre profesores y cursos")
    print(f"Se han creado {len(aprobaciones)} relaciones de aprobación")

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
    
    # Crear restricciones (para garantizar unicidad)
    crear_restricciones()
    
    # Inicializar datos
    crear_cursos()
    crear_estudiantes()
    crear_profesores()
    crear_relaciones()
    
    print("\nBase de datos inicializada correctamente! 🎉")
    print("\nPuedes ejecutar el API con el comando:")
    print("python src/main.py")
    print("\nLa documentación estará disponible en http://localhost:8000/docs")

if __name__ == "__main__":
    main()