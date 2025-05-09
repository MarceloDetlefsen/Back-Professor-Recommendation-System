// Descripción: Datos iniciales para la prueba del algoritmo de recomendación de profesores
// Generado el: 08-05-2025
// Contiene: 3 tipos de nodos y 3 relaciones
":begin
CREATE CONSTRAINT UNIQUE_IMPORT_NAME FOR (node:`UNIQUE IMPORT LABEL`) REQUIRE (node.`UNIQUE IMPORT ID`) IS UNIQUE;
:commit
CALL db.awaitIndexes(300);
:begin
UNWIND [{_id:1, properties:{estilo_clase:"presencial", disponibilidad:4, porcentaje_aprobados:0.85, años_experiencia:10, puntuacion_total:19, nombre:"Dr. Rodríguez", estilo_enseñanza:"visual", evaluacion_docente:4.5}}, {_id:2, properties:{estilo_clase:"presencial", disponibilidad:3, porcentaje_aprobados:0.75, años_experiencia:5, puntuacion_total:16, nombre:"Dra. Pérez", estilo_enseñanza:"práctico", evaluacion_docente:4.0}}, {_id:3, properties:{estilo_clase:"virtual", disponibilidad:5, porcentaje_aprobados:0.9, años_experiencia:3, puntuacion_total:18, nombre:"Mg. Gómez", estilo_enseñanza:"teórico", evaluacion_docente:4.8}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:Profesor;
UNWIND [{_id:0, properties:{estilo_clase:"presencial", promedio:80, puntuacion_total:18, estilo_aprendizaje:"visual", nombre:"Julian", veces_que_llevo_curso:0, asistencias_curso_anterior:5}}, {_id:8, properties:{estilo_clase:"presencial", promedio:85, puntuacion_total:18, estilo_aprendizaje:"visual", nombre:"Ana López", veces_que_llevo_curso:0, asistencias_curso_anterior:4}}, {_id:9, properties:{estilo_clase:"presencial", promedio:80, puntuacion_total:15, estilo_aprendizaje:"visual", nombre:"Carlos Méndez", veces_que_llevo_curso:1, asistencias_curso_anterior:3}}, {_id:10, properties:{estilo_clase:"virtual", promedio:90, puntuacion_total:20, estilo_aprendizaje:"teórico", nombre:"Luisa García", veces_que_llevo_curso:0, asistencias_curso_anterior:5}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:Estudiante;
UNWIND [{_id:4, properties:{nombre:"Matemáticas Básicas"}}, {_id:5, properties:{nombre:"Cálculo I"}}, {_id:7, properties:{nombre:"Álgebra Lineal"}}] AS row
CREATE (n:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row._id}) SET n += row.properties SET n:Curso;
:commit
:begin
UNWIND [{start: {_id:0}, end: {_id:1}, properties:{indice_compatibilidad:0.955, fecha_recomendacion:datetime('2025-05-08T17:51:30.477Z')}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:RECOMENDADO]->(end) SET r += row.properties;
UNWIND [{start: {_id:8}, end: {_id:4}, properties:{profesor:"Dr. Rodríguez"}}, {start: {_id:9}, end: {_id:4}, properties:{profesor:"Dr. Rodríguez"}}, {start: {_id:10}, end: {_id:7}, properties:{profesor:"Mg. Gómez"}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:APROBÓ_CON]->(end) SET r += row.properties;
UNWIND [{start: {_id:1}, end: {_id:4}, properties:{}}, {start: {_id:2}, end: {_id:5}, properties:{}}, {start: {_id:3}, end: {_id:7}, properties:{}}] AS row
MATCH (start:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.start._id})
MATCH (end:`UNIQUE IMPORT LABEL`{`UNIQUE IMPORT ID`: row.end._id})
CREATE (start)-[r:IMPARTE]->(end) SET r += row.properties;
:commit
:begin
MATCH (n:`UNIQUE IMPORT LABEL`)  WITH n LIMIT 20000 REMOVE n:`UNIQUE IMPORT LABEL` REMOVE n.`UNIQUE IMPORT ID`;
:commit
:begin
DROP CONSTRAINT UNIQUE_IMPORT_NAME;
:commit
"