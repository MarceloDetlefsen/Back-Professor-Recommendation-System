from pydantic import BaseModel, Field, validator

class Profesor(BaseModel):
    """Modelo de datos para un profesor"""
    nombre: str
    estilo_enseñanza: str
    estilo_clase: str
    años_experiencia: int = Field(..., ge=0)
    evaluacion_docente: float = Field(..., ge=0, le=5)
    porcentaje_aprobados: float = Field(..., ge=0, le=100)
    disponibilidad: int = Field(..., ge=0, le=5)
    puntuacion_total: int = None

    @validator('estilo_enseñanza')
    def validate_estilo_ensenanza(cls, v):
        estilos_validos = ["visual", "práctico", "teórico"]
        if v.lower() not in estilos_validos:
            raise ValueError(f"Estilo de enseñanza debe ser uno de: {estilos_validos}")
        return v.lower()

    @validator('estilo_clase')
    def validate_estilo_clase(cls, v):
        estilos_validos = ["presencial", "virtual"]
        if v.lower() not in estilos_validos:
            raise ValueError(f"Estilo de clase debe ser uno de: {estilos_validos}")
        return v.lower()

    def calcular_puntuacion(self):
        """Calcula la puntuación total del profesor"""
        experiencia = min(5, self.años_experiencia // 5)  # 1 punto por cada 5 años de experiencia
        evaluacion = min(5, int(self.evaluacion_docente))  # 1 punto por cada estrella en evaluación
        aprobados = min(5, int((self.porcentaje_aprobados / 100) * 5))  # 1 punto por cada 20% de aprobados
        disponibilidad = min(5, self.disponibilidad)  # 1 punto por cada nivel de disponibilidad
        
        self.puntuacion_total = experiencia + evaluacion + aprobados + disponibilidad
        return self.puntuacion_total
