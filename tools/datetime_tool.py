import datetime
from google.genai import types as genai_types # SDK unificado

GET_CURRENT_DATETIME_DECLARATION = genai_types.FunctionDeclaration(
    name="get_current_datetime",
    description="Obtiene la fecha y hora actual del servidor. Retorna la fecha y hora en formato ISO (YYYY-MM-DDTHH:MM:SS.ffffff).",
    # Especificar explícitamente un esquema de tipo OBJECT sin propiedades
    parameters={
        "type": "object",  # Indicar que el tipo de esquema es un objeto
        "properties": {}   # Un objeto vacío para 'properties' ya que no hay parámetros
    }
)

def get_current_datetime() -> str:
    current_time = datetime.datetime.now()
    return current_time.isoformat()