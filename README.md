# Sistema de Recomendación de Profesores

Este sistema utiliza un algoritmo basado en grafos para recomendar profesores a estudiantes, considerando estilos de aprendizaje, rendimiento académico y experiencias previas de estudiantes similares.

## 📊Características

- API RESTful desarrollada con FastAPI
- Base de datos de grafos en Neo4j para almacenar relaciones entre estudiantes, profesores y cursos
- Algoritmo de recomendación que considera múltiples factores:
  - Estilo de aprendizaje del estudiante y estilo de enseñanza del profesor
  - Preferencia por clases presenciales o virtuales
  - Experiencia del profesor
  - Evaluaciones de estudiantes anteriores
  - Resultados de estudiantes similares con el mismo profesor
  - Desempeño académico del estudiante

## ✅Requisitos

- Python 3.10+
- Neo4j (instancia local o en la nube)
- Poetry (para gestión de dependencias)
- Dependencias listadas en pyproject.toml

## 🛠️Instalación

### 1. Instalar Poetry

1. Descargar e instalar Poetry (recomendado):
```bash
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Linux/macOS
curl -sSL https://install.python-poetry.org | python3 -
```

2. Agregar Poetry al PATH (si no se agregó automáticamente):
```
# Windows
setx PATH "%PATH%;%APPDATA%\Python\Scripts"

# Linux/macOS
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

3. Verificar la instalación:
```
poetry --version
```

### ⚙️2. Modificaciones

1. Clonar el repositorio:
```bash
git clone https://github.com/tu-usuario/back-professor-recommendation-system.git
cd back-professor-recommendation-system
```

2. Crear y activar un entorno virtual:
```bash
poetry install  # Instala todas las dependencias
```

3. Configurar variables de entorno:

Editar el archivo `.env` en la raíz del proyecto con la siguiente información:
   ```
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=tu_contraseña //Modificar esto
   DEBUG=True
   ```

Editar el archivo `config.py`en el source del proyecto con la siguiente información:
   ```
  NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
  NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
  NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "tu_contraseña") //Modificar esto
  ```

## 🪄Iniciar la aplicación

1. Se ponen de momento asi datos en la base datos.
```bash
///Se recomiendan los siguientes comandos:
poetry run python -m scripts.init_db 
poetry run python scripts/init_db.py
```

2. Se ejecuta el programa
```bash
///Se recomiendan los siguientes comandos:
poetry run python -m src.main
poetry run python src/main.py
```

La API estará disponible en `http://localhost:8000`

## 📄Documentación de la API

Luego de iniciar la aplicación, puedes acceder a la documentación interactiva:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🗂️Estructura del proyecto

```
Back-Professor-Recommendation-System/
├── scripts/
│   ├── __init__.py
│   ├── init_db.py
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
├── .gitignore
├── poetry.lock
├── pyproject.toml
├── README.md
```

# 🗃️Modelos de datos

### 🧑‍🎓Estudiante
- Nombre
- Carnet
- Carrera
- Año de pensum
- Email
- Contraseña
- Estilo de aprendizaje (visual, práctico, teórico)
- Estilo de clase (presencial, virtual)
- Promedio académico
- Grado (año cursando)
- Carga máxima de cursos por ciclo
- Cursos aprobados con más de la zona mínima
- Asistencia
- Veces que ha llevado el curso
- Puntuación total (calculada a partir del resto de información)

### 🧑‍🏫Profesor
- Nombre
- Estilo de enseñanza (visual, práctico, teórico)
- Estilo de clase (presencial, virtual)
- Años de experiencia
- Puntuación en la evaluación docente
- Porcentaje de estudiantes aprobados
- Nivel de disponibilidad
- Puntuación total (calculada a partir del resto de información)

### 📒Curso
- Nombre
- Código
- Departamento
- Créditos

## 🧠🔁Algoritmo de recomendación

El algoritmo toma en cuenta:
1. La compatibilidad del estilo de aprendizaje del estudiante con el estilo de enseñanza del profesor
2. La modalidad de clase preferida (presencial o virtual)
3. La puntuación del estudiante basada en su rendimiento
4. La puntuación del profesor basada en su experiencia y evaluaciones
5. El éxito que han tenido estudiantes similares con cada profesor

El resultado es un índice de compatibilidad estudiante-profesor que determina qué profesores son más recomendables para cada estudiante específico.
