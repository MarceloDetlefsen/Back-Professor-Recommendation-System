from pydantic import BaseModel, Field

class Curso(BaseModel):
    """Modelo de datos para un curso"""
    nombre: str
    codigo: str
    departamento: str
    creditos: int = Field(..., ge=0)
    
    class Config:
        schema_extra = {
            "example": {
                "nombre": "Cálculo 1",
                "codigo": "MAT103",
                "departamento": "Matemáticas",
                "creditos": 4
            }
        }

class CursoEstudiante(BaseModel):
    """Modelo para relación entre estudiante y curso"""
    estudiante_id: str
    curso_id: str
    nota_final: float = Field(..., ge=0, le=100)
    aprobado: bool = None
    
    def calcular_estado(self, nota_aprobacion=61):
        """Determina si el estudiante aprobó el curso"""
        self.aprobado = self.nota_final >= nota_aprobacion
        return self.aprobado
