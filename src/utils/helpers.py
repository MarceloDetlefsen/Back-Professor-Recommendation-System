def normalize_string(text):
    """
    Normaliza un string eliminando acentos y convirtiendo a minúsculas
    
    Args:
        text: Texto a normalizar
        
    Returns:
        str: Texto normalizado
    """
    import unicodedata
    
    if not text:
        return ""
        
    # Normalizar NFD y eliminar diacríticos
    normalized = unicodedata.normalize('NFD', text)
    normalized = ''.join([c for c in normalized if not unicodedata.combining(c)])
    
    # Convertir a minúsculas
    return normalized.lower()

def validate_learning_style(style):
    """
    Valida si un estilo de aprendizaje/enseñanza es válido
    
    Args:
        style: Estilo a validar
        
    Returns:
        bool: True si es válido, False si no
    """
    valid_styles = ["practico", "teorico", "mixto"]
    normalized_style = normalize_string(style)
    
    return normalized_style in [normalize_string(s) for s in valid_styles]

def validate_class_style(style):
    """
    Valida si un estilo de clase es válido
    
    Args:
        style: Estilo a validar
        
    Returns:
        bool: True si es válido, False si no
    """
    valid_styles = ["con_tecnologia", "sin_tecnologia", "mixto"]
    normalized_style = normalize_string(style)
    
    return normalized_style in [normalize_string(s) for s in valid_styles]

def format_compatibility_index(index):
    """
    Formatea un índice de compatibilidad para mostrarlo como porcentaje
    
    Args:
        index: Índice de compatibilidad (0-1)
        
    Returns:
        str: Porcentaje formateado
    """
    return f"{index * 100:.2f}%"

def create_response(data=None, message="", success=True):
    """
    Crea una estructura de respuesta consistente para las API
    
    Args:
        data: Datos de la respuesta
        message: Mensaje descriptivo
        success: Indicador de éxito
        
    Returns:
        dict: Estructura de respuesta
    """
    return {
        "success": success,
        "message": message,
        "data": data
    }
