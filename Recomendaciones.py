from neo4j import GraphDatabase
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "9vK@U$]73i{$")

try:
    driver = GraphDatabase.driver(URI, auth=AUTH)
    driver.verify_connectivity()
    print("Conexión exitosa a la base de datos")
except Exception as e:
    print(f"Error de conexión: {e}")
    exit()

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

def recomendar_profesores(tx, nombre_estudiante):
    query_validaciones = """
    MATCH (e:Estudiante {nombre: $nombre_estudiante})
    MATCH (p:Profesor)
    WHERE p.estilo_enseñanza = e.estilo_aprendizaje 
        AND p.estilo_clase = e.estilo_clase
    RETURN p, e.puntuacion_total AS puntuacion_estudiante
    """
    profesores_validos = tx.run(query_validaciones, nombre_estudiante=nombre_estudiante).data()

    if not profesores_validos:
        return []

    recomendaciones = []
    for record in profesores_validos:
        profesor = record["p"]
        puntuacion_estudiante = record["puntuacion_estudiante"]

        query_afinidad = """
        MATCH (e:Estudiante {nombre: $nombre_estudiante})
        OPTIONAL MATCH (similar:Estudiante)
        WHERE similar.estilo_aprendizaje = e.estilo_aprendizaje
            AND similar.estilo_clase = e.estilo_clase
            AND abs(similar.veces_que_llevo_curso - e.veces_que_llevo_curso) <= 1
            AND abs(similar.promedio - e.promedio) <= 5
        OPTIONAL MATCH (similar)-[:APROBÓ_CON]->(c:Curso)<-[:IMPARTE]-(p:Profesor {nombre: $nombre_profesor})
        WITH count(DISTINCT similar) AS total_similares,
             count(DISTINCT CASE WHEN similar IS NOT NULL THEN similar ELSE NULL END) AS similares_que_aprobaron
        RETURN similares_que_aprobaron, total_similares
        """
        afinidad_data = tx.run(query_afinidad, 
                               nombre_estudiante=nombre_estudiante,
                               nombre_profesor=profesor["nombre"]).single()

        afinidad = (afinidad_data["similares_que_aprobaron"] / afinidad_data["total_similares"]) * 100 if afinidad_data and afinidad_data["total_similares"] > 0 else 0

        if afinidad_data and afinidad_data["total_similares"] > 0:
            indice = (0.3 * (puntuacion_estudiante / 20)) + (0.3 * (profesor["puntuacion_total"] / 20)) + (0.4 * (afinidad / 100))
        else:
            indice = (0.5 * (puntuacion_estudiante / 20)) + (0.5 * (profesor["puntuacion_total"] / 20))

        tx.run("""
        MATCH (e:Estudiante {nombre: $nombre_estudiante})
        MATCH (p:Profesor {nombre: $nombre_profesor})
        MERGE (e)-[r:RECOMENDADO]->(p)
        SET r.indice_compatibilidad = $indice,
            r.fecha_recomendacion = datetime()
        """, nombre_estudiante=nombre_estudiante,
             nombre_profesor=profesor["nombre"],
             indice=indice)

        recomendaciones.append({
            "profesor": profesor["nombre"],
            "indice_compatibilidad": indice * 100,
            "puntuacion_estudiante": puntuacion_estudiante,
            "puntuacion_profesor": profesor["puntuacion_total"],
            "afinidad": afinidad
        })

    return sorted(recomendaciones, key=lambda x: x["indice_compatibilidad"], reverse=True)

def puntuacion_profesor(tx, nombre_profesor):
    query = """
    MATCH (p:Profesor {nombre: $nombre_profesor})
    RETURN p.años_experiencia AS experiencia,
           p.evaluacion_docente AS evaluacion,
           p.porcentaje_aprobados AS aprobados,
           p.disponibilidad AS disponibilidad
    """
    result = tx.run(query, nombre_profesor=nombre_profesor).single()
    
    if result:
        experiencia = min(5, result["experiencia"] // 5)  # 1 punto por cada 5 años de experiencia
        evaluacion = min(5, result["evaluacion_docente"])  # 1 punto por cada estrella en la evaluación docente
        aprobados = min(5, (result["porcentaje_aprobados"]/100) * 5)  # 1 punto por cada 20% de aprobados
        disponibilidad = min(5, result["disponibilidad"])  # 1 punto por cada nivel de disponibilidad
        
        puntuacion_total_profesor = experiencia + evaluacion + aprobados + disponibilidad
        return puntuacion_total_profesor
    else:
        return 0

def main():
    print("=== Sistema de Recomendación UVG ===")
    nombre = input("Nombre del estudiante: ")
    estilo_aprendizaje = input("Estilo de aprendizaje (visual/práctico/teórico): ")
    estilo_clase = input("Modalidad (presencial/virtual): ")
    promedio = int(input("Promedio académico (0-100): "))
    asistencias = int(input("Asistencias en curso anterior (0-5): "))
    veces_curso = int(input("Veces que ha llevado el curso (0-5): "))

    with driver.session() as session:
        session.execute_write(registrar_estudiante, nombre, estilo_aprendizaje, estilo_clase, promedio, asistencias, veces_curso)
        print("\n¡Registro exitoso! Calculando recomendaciones...\n")

        recomendaciones = session.execute_write(recomendar_profesores, nombre)

        if not recomendaciones:
            print("No hay profesores que cumplan tus requisitos exactos.")
        else:
            print("\nTop profesores recomendados:")
            for i, profe in enumerate(recomendaciones, 1):
                print(f"""
                {i}. {profe['profesor']}:
                  - Índice de compatibilidad: {profe['indice_compatibilidad']:.2f}%
                  - Puntuación estudiante: {profe['puntuacion_estudiante']}/20
                  - Puntuación profesor: {profe['puntuacion_profesor']}/20
                  - Afinidad con similares: {profe['afinidad']:.2f}%
                """)

if _name_ == "_main_":
    main()
    driver.close()
