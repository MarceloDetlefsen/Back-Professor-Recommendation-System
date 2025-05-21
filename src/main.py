from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

from api.rutas_estudiantes import router as estudiantes_router
from api.rutas_profesores import router as profesores_router
from api.rutas import router as rutas_generales
from database.neo4jdriver import Neo4jDriver
from config import API_PREFIX, DEBUG

# Manejador de contexto para inicializar y cerrar recursos
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializar la conexión con Neo4j
    try:
        driver = Neo4jDriver()
        print("Conexión a Neo4j inicializada en el lifespan de la aplicación")
        yield
    finally:
        # Cerrar la conexión cuando la aplicación se cierra
        driver.close()
        print("Conexión a Neo4j cerrada correctamente")

# Crear la aplicación FastAPI
app = FastAPI(
    title="Sistema de Recomendación de Profesores",
    description="API para recomendar profesores a estudiantes basado en sus características",
    version="0.1.0",
    lifespan=lifespan,
    debug=DEBUG
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todas las origins en desarrollo
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos
    allow_headers=["*"],  # Permite todos los headers
)

# Incluir los routers
app.include_router(estudiantes_router, prefix=f"{API_PREFIX}/estudiantes", tags=["Estudiantes"])
app.include_router(profesores_router, prefix=f"{API_PREFIX}/profesores", tags=["Profesores"])
app.include_router(rutas_generales, prefix=API_PREFIX, tags=["General"])

# Ruta raíz
@app.get("/", tags=["Root"])
async def root():
    return {
        "mensaje": "Sistema de Recomendación de Profesores API",
        "estado": "en línea",
        "documentación": "/docs"
    }

# Código para ejecutar la aplicación directamente
if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=DEBUG)