from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
from app.mcp.mcp_client import MCPClient, procesar_mensaje, procesar_mensaje_stream
from fastapi import HTTPException, status
from app.api.v1.agent.schemas import ChatAgentRequest, ChatAgentResponse
from app.logger import logger

load_dotenv()

class AgetController:
    def __init__(self):
        self.client_mcp = MCPClient()

    async def chat_agent_controller(self, consulta: ChatAgentRequest) -> ChatAgentResponse:
        """Controlador para manejar la consulta del Chat Agent

        Args:
            consulta: Consulta del usuario
        """

        client = MCPClient()

        try:
            logger.info(f"Procesando consulta del Chat Agent... {consulta.mensaje}")
            respuesta = await procesar_mensaje(client, consulta.mensaje, './app/mcp/servers/mcp_server_sql.py')
            return ChatAgentResponse(
                respuesta=respuesta
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al procesar la consulta: {str(e)}"
            )

    async def chat_agent_stream_controller(self, consulta: ChatAgentRequest):
        """Controlador para manejar la consulta del Chat Agent en forma stream

        Args:
            consulta: Consulta del usuario
        """

        # client = MCPClient()

        try:
            logger.info(f"Procesando consulta del Chat Agent en forma stream... {consulta.mensaje}")
            return StreamingResponse(procesar_mensaje_stream(self.client_mcp, consulta.mensaje, './app/mcp/servers/mcp_server_sql.py'), media_type="text/plain")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al procesar la consulta en forma stream: {str(e)}"
            )
