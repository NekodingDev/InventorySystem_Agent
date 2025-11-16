from pydantic import BaseModel
from typing import List, Union
from enum import Enum

# Enum que permite definir los tipos de gráficos disponibles
class CharType(str, Enum):
    barras = "barras"
    lineas = "lineas"
    pastel = "pastel"


class Data(BaseModel):
    description: str
    value: Union[int, float, str]


class Graphic(BaseModel):
    type: CharType
    data: List[Data]


class ChatResponse(BaseModel):
    summary: str
    list_graphics: List[Graphic]


class ChatResponseGraphicOnly(BaseModel):
    list_graphics: List[Graphic] = []
