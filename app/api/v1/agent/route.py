from fastapi import APIRouter
from app.api.v1.agent.schemas import ChatAgentResponse, ChatAgentStreamResponse
from app.api.v1.agent.controller import AgetController

# Crear una instancia del router de FastAPI 
router_agent_chat = APIRouter()

# Crear una instancia del controlador
agent_controller = AgetController()

# Definir la ruta para el Chat Agent
router_agent_chat.post("/chat-agent", response_model=ChatAgentResponse)(agent_controller.chat_agent_controller)
router_agent_chat.post("/chat-agent-stream", response_model=ChatAgentStreamResponse)(agent_controller.chat_agent_stream_controller)
