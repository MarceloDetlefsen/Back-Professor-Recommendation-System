from pydantic import BaseModel, Field, validator
from typing import Optional

class Estudiante(BaseModel):
    """Modelo de datos para un estudiante"""
    nombre: str
    carnet: str = Field(..., description="Carnet del estudiante")
    carrera: str
    pensum: int = Field(..., ge=2020, le=2030, description="Año del pensum")
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$', description="Email válido")
    password: str = Field(..., min_length=6, description="Contraseña mínimo 6 caracteres")
    estilo_aprendizaje: str
    estilo_clase: str
    promedio: float = Field(..., ge=0, le=100, description="Promedio académico")
    grado: str
    carga_maxima: int = Field(..., ge=1, le=7, description="Cursos máximos por ciclo")
    cursos_zona_minima: int = Field(..., ge=0, le=7, description="Cursos con zona mínima")
    
    # Campos opcionales para compatibilidad con el código existente
    asistencias: Optional[int] = Field(default=5, ge=0, le=5)
    veces_curso: Optional[int] = Field(default=1, ge=0, le=5)
    puntuacion_total: Optional[int] = None

    @validator('estilo_aprendizaje')
    def validate_estilo_aprendizaje(cls, v):
        # Mapeo de valores del frontend a valores internos
        mapeo_estilos = {
            "Mixto": "mixto",
            "Práctico": "pracitco", 
            "Teórico": "teorico"
        }
        
        if v in mapeo_estilos:
            return mapeo_estilos[v]
        
        # Si viene en minúsculas, aceptarlo directamente
        estilos_validos = ["mixto", "practico", "teorico"]
        if v.lower() in estilos_validos:
            return v.lower()
            
        raise ValueError(f"Estilo de aprendizaje debe ser uno de: {list(mapeo_estilos.keys())}")

    @validator('estilo_clase')
    def validate_estilo_clase(cls, v):
        # Mapeo de valores del frontend a valores internos
        mapeo_clase = {
            "Uso de herramientas tecnológicas": "con_tecnologia",
            "Sin uso de herramientas tecnológicas": "sin_tecnologia",
            "Mixto": "mixto"
        }
        
        if v in mapeo_clase:
            return mapeo_clase[v]
        
        # Si viene en minúsculas, aceptarlo directamente    
        estilos_validos = ["tecnologico", "no_tecnologico", "mixto"]
        if v.lower() in estilos_validos:
            return v.lower()
            
        raise ValueError(f"Estilo de clase debe ser uno de: {list(mapeo_clase.keys())}")

    @validator('grado')
    def validate_grado(cls, v):
        grados_validos = ["Primer año", "Segundo año", "Tercer año", "Cuarto año", "Quinto año", "Sexto año"]
        if v not in grados_validos:
            raise ValueError(f"Grado debe ser uno de: {grados_validos}")
        return v

    def calcular_puntuacion(self):
        """Calcula la puntuación total del estudiante basada en múltiples factores"""
        # Puntuación por promedio (0-10 puntos)
        puntuacion_promedio = min(10, int(self.promedio // 10))
        
        # Puntuación por carga académica (0-5 puntos)
        # Menos carga = más puntos (estudiante más disponible)
        puntuacion_carga = max(0, 5 - (self.carga_maxima // 2))
        
        # Puntuación por cursos con zona mínima (0-5 puntos) 
        # Menos cursos con zona mínima = más puntos (mejor rendimiento)
        puntuacion_zona = max(0, 5 - self.cursos_zona_minima)
        
        # Puntuación por asistencias (si está disponible)
        puntuacion_asistencias = min(5, self.asistencias) if self.asistencias else 3
        
        # Puntuación por veces que lleva curso (si está disponible)
        puntuacion_veces = max(0, 5 - self.veces_curso) if self.veces_curso else 4
        
        self.puntuacion_total = (
            puntuacion_promedio + 
            puntuacion_carga + 
            puntuacion_zona + 
            puntuacion_asistencias + 
            puntuacion_veces
        )
        
        return self.puntuacion_total