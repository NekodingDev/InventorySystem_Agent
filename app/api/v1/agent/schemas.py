from pydantic import BaseModel
from app.mcp.schemas import ChatResponse

class ChatAgentRequest(BaseModel):
    mensaje: str

class ChatAgentResponse(BaseModel):
    respuesta: str | ChatResponse

class ChatAgentStreamResponse(BaseModel):
    message: str
