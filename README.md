# Sistema de Recomendación de Profesores

Este sistema utiliza un algoritmo basado en grafos para recomendar profesores a estudiantes, considerando estilos de aprendizaje, rendimiento académico y experiencias previas de estudiantes similares.

## Características

- API RESTful desarrollada con FastAPI
- Base de datos de grafos Neo4j para almacenar relaciones entre estudiantes, profesores y cursos
- Algoritmo de recomendación que considera múltiples factores:
  - Estilo de aprendizaje del estudiante y estilo de enseñanza del profesor
  - Preferencia por clases presenciales o virtuales
  - Experiencia del profesor
  - Evaluaciones de estudiantes anteriores
  - Resultados de estudiantes similares con el mismo profesor

## Requisitos

- Python 3.10+
- Neo4j (instancia local o en la nube)
- Dependencias listadas en requisitos.txt

## Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/back-professor-recommendation-system.git
cd back-professor-recommendation-system
```

2. Crear y activar un entorno virtual:
```bash
python -m venv venv
venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requisitos.txt
```

4. Configurar variables de entorno:
   - Editar el archivo `.env` en la raíz del proyecto con la siguiente información:
   ```
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=tu_contraseña //Modificar esto
   DEBUG=True
   ```

## Iniciar la aplicación

1. Se ponen de momento asi datos en la base datos.
```bash
poetry run python -m scripts.init_db
```

2. Se ejecuta el programa
```bash
poetry run python -m src.main
```

La API estará disponible en `http://localhost:8000`

## Documentación de la API

Luego de iniciar la aplicación, puedes acceder a la documentación interactiva:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

**Queda pendiente conectar el back con el front**

## Estructura del proyecto

```
Back-Professor-Recommendation-System/
├── scripts/
|   ├── __init__.py
|   ├── init_db.py
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── rutas.py
│   │   ├── rutas_cursos.py
│   │   ├── rutas_estudiantes.py
│   │   └── rutas_profesores.py
│   ├── database/
│   │   ├── __init__.py
│   │   └── neo4jdriver.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── curso.py
│   │   ├── estudiante.py
│   │   └── profesor.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── algoritmo_de_recomendacion.py
│   │   ├── algoritmo_estudiante.py
│   │   └── algoritmo_profesor.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── helpers.py
│   ├── __init__.py
│   ├── config.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   ├── algoritmo_recomendacion.py
│   └── base_datos.py
├── venv/
├── .env
├── pyproject.toml
├── README.md
└── requisitos.txt
```

# Modelos de datos

### Estudiante
- Nombre
- Estilo de aprendizaje (visual, práctico, teórico)
- Estilo de clase (presencial, virtual)
- Promedio académico
- Asistencias
- Veces que ha llevado el curso
- Puntuación total (calculada)

### Profesor
- Nombre
- Estilo de enseñanza (visual, práctico, teórico)
- Estilo de clase (presencial, virtual)
- Años de experiencia
- Evaluación docente
- Porcentaje de estudiantes aprobados
- Disponibilidad
- Puntuación total (calculada)

### Curso
- Nombre
- Código
- Departamento
- Créditos

## Algoritmo de recomendación

El algoritmo toma en cuenta:
1. La compatibilidad del estilo de aprendizaje del estudiante con el estilo de enseñanza del profesor
2. La modalidad de clase preferida (presencial o virtual)
3. La puntuación del estudiante basada en su rendimiento
4. La puntuación del profesor basada en su experiencia y evaluaciones
5. El éxito que han tenido estudiantes similares con cada profesor

El resultado es un índice de compatibilidad que determina qué profesores son más recomendables para cada estudiante específico.