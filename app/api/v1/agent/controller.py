from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
from app.mcp_custom.mcp_client import MCPClient, procesar_mensaje, procesar_mensaje_stream
from fastapi import HTTPException, status
from app.api.v1.agent.schemas import ChatAgentRequest, ChatAgentResponse
from app.logger import logger
from app.agent.agent import init_agent, call_agent_async, USER_ID, SESSION_ID

load_dotenv()

class AgetController:
    def __init__(self):
        self.client_mcp = MCPClient()
        self.runner = None

    async def get_runner(self):
        if self.runner is None:
            self.runner = await init_agent()
        return self.runner

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

        try:
            logger.info(f"Procesando consulta del Chat Agent en forma stream... {consulta.mensaje}")
            return StreamingResponse(procesar_mensaje_stream(self.client_mcp, consulta.mensaje, './app/mcp/servers/mcp_server_sql.py'), media_type="text/plain")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al procesar la consulta en forma stream: {str(e)}"
            )

    async def chat_agent_controller_v2(self, consulta: ChatAgentRequest):
        """Controlador para manejar la consulta del Chat Agent en forma stream

        Args:
            consulta: Consulta del usuario
        """

        try:
            logger.info(f"Procesando consulta del Chat Agent ADK... {consulta.mensaje}")

            runner = await self.get_runner() 

            return StreamingResponse(call_agent_async(consulta.mensaje, runner=runner, user_id=USER_ID, session_id=SESSION_ID), media_type="text/plain")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al procesar la consulta: {str(e)}"
            )
