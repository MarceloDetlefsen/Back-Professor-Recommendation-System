from pydantic import BaseModel, Field, validator

class Estudiante(BaseModel):
    """Modelo de datos para un estudiante"""
    nombre: str
    estilo_aprendizaje: str
    estilo_clase: str
    promedio: int = Field(..., ge=0, le=100)
    asistencias: int = Field(..., ge=0, le=5)
    veces_curso: int = Field(..., ge=0, le=5)
    puntuacion_total: int = None

    @validator('estilo_aprendizaje')
    def validate_estilo_aprendizaje(cls, v):
        estilos_validos = ["visual", "práctico", "teórico"]
        if v.lower() not in estilos_validos:
            raise ValueError(f"Estilo de aprendizaje debe ser uno de: {estilos_validos}")
        return v.lower()

    @validator('estilo_clase')
    def validate_estilo_clase(cls, v):
        estilos_validos = ["presencial", "virtual"]
        if v.lower() not in estilos_validos:
            raise ValueError(f"Estilo de clase debe ser uno de: {estilos_validos}")
        return v.lower()

    def calcular_puntuacion(self):
        """Calcula la puntuación total del estudiante"""
        puntuacion_promedio = min(10, self.promedio // 10)  # 1 punto por cada 10 pts en la clase
        puntuacion_asistencias = min(5, self.asistencias)   # 1 punto por asistencia
        puntuacion_veces = max(0, 5 - self.veces_curso)     # 5 si es primera vez, 0 si lo lleva por 5ta vez
        
        self.puntuacion_total = puntuacion_promedio + puntuacion_asistencias + puntuacion_veces
        return self.puntuacion_total
