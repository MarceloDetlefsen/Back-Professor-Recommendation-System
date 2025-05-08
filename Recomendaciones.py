from neo4j import GraphDatabase
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "9vK@U$]73i{$")
with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()
    print("Se ha conectado correctamente a tu base de datos.")

def registrar_estudiante(tx, nombre, estilo_aprendizaje, estilo_clase, promedio, asistencias, veces_curso):
    #Calculo de puntuaciones
    puntuacion_promedio = min(10, promedio // 10)  # 1 punto sumado por cada 10 pts en la clase
    puntuacion_asistencias = min(5, asistencias)   # 1 punto por asistencia
    puntuacion_veces = max(0, 5 - veces_curso)     # 5 si es primera vez tomando el curso, 0 si lo lleva por 5ta vez
    puntuacion_total = puntuacion_promedio + puntuacion_asistencias + puntuacion_veces

    #Query en CYPHER para la creación del nodo del estudiante correspondiente
    query = """
        CREATE (e:Estudiante {
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
    #Devuelve el nodo recién creado
    result = tx.run(query, 
                nombre=nombre,
                estilo_aprendizaje=estilo_aprendizaje,
                estilo_clase=estilo_clase,
                promedio=promedio,
                asistencias=asistencias,
                veces_curso=veces_curso,
                puntuacion_total=puntuacion_total)
    return result.single()

with driver.session() as session:
    result = session.execute_write(
        registrar_estudiante,
        "María González", "visual", "presencial", 88, 5, 0
    )
    print("Estudiante registrado:", result["e"]["nombre"])