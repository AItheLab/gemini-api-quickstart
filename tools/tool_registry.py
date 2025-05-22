from google.genai import types as genai_types # SDK unificado
from . import datetime_tool

# GenerateContentConfig espera una lista de google.genai.types.Tool
_available_tools_sdk_format = [
    genai_types.Tool(
        function_declarations=[
            datetime_tool.GET_CURRENT_DATETIME_DECLARATION,
        ]
    )
]

_tool_implementations_map = {
    datetime_tool.GET_CURRENT_DATETIME_DECLARATION.name: datetime_tool.get_current_datetime,
}

def get_available_tools_for_sdk() -> list[genai_types.Tool]:
    return _available_tools_sdk_format

def get_tool_implementation(tool_name: str):
    return _tool_implementations_map.get(tool_name)