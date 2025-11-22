from pydantic import BaseModel
from typing import List
from enum import Enum

class CharType(str, Enum):
    barras = "barras"
    lineas = "lineas"
    pastel = "pastel"


class Data(BaseModel):
    description: str
    value: str


class Graphic(BaseModel):
    type: CharType
    data: List[Data]


class ChatResponseGraphicOnly(BaseModel):
    list_graphics: List[Graphic] = []
