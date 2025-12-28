from pydantic import BaseModel, field_validator
from typing import List
from enum import Enum
import json

class CharType(str, Enum):
    barras = "barras"
    lineas = "lineas"
    pastel = "pastel"


class Data(BaseModel):
    description: str
    value: str

    @field_validator('value', mode='before')
    @classmethod
    def convert_to_string(cls, v):
        # Convierte cualquier tipo a string
        return str(v)


class Graphic(BaseModel):
    type: CharType
    data: List[Data]

    @field_validator('data', mode='before')
    @classmethod
    def parse_data(cls, v):
        # Si es string, parsearlo
        if isinstance(v, str):
            return json.loads(v)
        # Si ya es lista, devolverla tal cual
        return v


class ChatResponseGraphicOnly(BaseModel):
    list_graphics: List[Graphic] = []
