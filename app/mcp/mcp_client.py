import json
import asyncio
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam

from app.mcp.schemas import ChatResponse, ChatResponseGraphicOnly

import logging

SYSTEM_PROMPT = """
    TODAS LAS REPUESTAS DEBEN SER EN ESPAÑOL
    Eres un asistente inteligente que ayuda a los usuarios a hacer consultas sobre
    información de la base de datos MYSQL de una negocio ferretero llamado "Cerámica de Altura".
    La base de datos contiene datos de inventario del negocio.
    Solo puedes responder preguntas relacionadas al negocio.
    Si se te pide información sensible como contraseña de usuario, no brindar la
    información.

    Cuando necesites obtener información de la base de datos, utiliza las herramientas.

    Debes elegir el mejor tipo de gráfico que se adecúe a la información solicitada.

    Cuando se te solicite una respuesta en el formato gráfico, debes hacer lo siguiente:

    Tú como asistente debes decidir uno de lo siguientes gráficos: barras, líneas y pastel.

    Si los datos obtenidos del tool no son adecuados para generar gráficos o solo es un dato,
    no enviar ningún gráfico.

    Si la consulta es un gráfico, evita enviar enlaces o imágenes de respuesta. Solo
    responde con la recomendación de gráficos.
"""


class MCPClient:
    def __init__(self):
        self.session: ClientSession
        self.exit_stack = AsyncExitStack()
        self.client = OpenAI()
        self.messages: list[ChatCompletionMessageParam] = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
        ]


    async def connect_to_server(self, server_script_path: str):
        """Conectarse al servidor MCP

        Args:
            server_script_path: Dirección del script (.py o .js)
        """

        # Validar la extensión del archivo
        # Solo se permiten .py y .js (servidores MCP en Python o Node.js)
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        if not (is_python or is_js):
            logging.error("El script del servidor debe ser .py o .js")
            raise ValueError("El script del servidor debe ser .py o .js")

        # Definir el comando y los parámetros del servidor
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None
        )

        # Iniciar el transporte stdio y la sesión del cliente
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params)) # Comunicación stdio con el servidor
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write)) # Sesión MCP
        await self.session.initialize()

        # Listar herramientas disponibles 
        response = await self.session.list_tools()
        tools = response.tools
        logging.info(f"Conectado al servidor MCP en {server_script_path} con herramientas: {[tool.name for tool in tools]}")


    async def process_query_stream(self, query: str):
        """Procesar la consulta del usuario en modo stream

        Args:
            query: La consulta del usuario
        """
        
        # Preparar el mensaje inicial del chat
        self.messages.append(
            {
                "role": "user",
                "content": query
            }
        )

        # Obtener la lista de herramientas disponibles desde el servidor MCP
        response = await self.session.list_tools()
        available_tools: list[ChatCompletionToolParam] = [
            ChatCompletionToolParam(
                type="function",
                function={
                    "name": tool.name,
                    "description": str(tool.description),
                    "parameters": tool.inputSchema,
                }
            )
            for tool in response.tools
        ]

        # Enviar la consulta al modelo GPT-4o con las herramientas disponibles
        stream = self.client.chat.completions.create(
            model="gpt-4o",
            messages=self.messages,
            tools=available_tools,
            max_tokens=1000,
            stream=True
        )

        tool_dict = {}
        for event in stream:
            # print(event.to_json())
            content = event.choices[0].delta.content
            tool_calls = event.choices[0].delta.tool_calls
            if content:
                yield content

            if tool_calls:
                for tool_call in tool_calls:
                    index = str(tool_call.index)
                    args = tool_call.function.arguments # type: ignore[attr-defined]
                    name = tool_call.function.name # type: ignore[attr-defined]

                    # Almacenar las llamadas a herramientas en un diccionario
                    # Si la herramienta ya existe, concatenar los argumentos y nombres
                    # Si no, crear una nueva entrada
                    if index not in tool_dict:
                        tool_dict[index] = { "type": "function", "id": index, "function": {} }
                    if args:
                        tool_dict[index]["function"]["arguments"] = tool_dict[index]["function"].get("arguments", "") +  args
                    if name:
                        tool_dict[index]["function"]["name"] = tool_dict[index]["function"].get("name", "") + name

        if tool_dict:
            for key in tool_dict:
                tool_name = tool_dict[key]["function"]["name"] 
                tool_args = json.loads(tool_dict[key]["function"]["arguments"])

                # Llamar a la herramienta en el servidor MCP
                result = await self.session.call_tool(tool_name, tool_args)
                logging.info(f"Llamada a herramienta {tool_name} con los argumentos {tool_args}")

                # Actualizar el contexto del chat con la llamada a la herramienta y su resultado
                self.messages.append({
                    "role": "assistant",
                    "tool_calls": [tool_dict[key]], # type: ignore[attr-defined]
                })
                self.messages.append({
                    "role": "tool",
                    "content": result.content,
                    "tool_call_id": key  # type: ignore[attr-defined]
                })
                self.messages.append({
                    "role": "system",
                    "content": "Genera insights basados en los datos obtenidos. Response al usuario con esto."
                })

                stream = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=self.messages,
                    max_tokens=1000,
                    stream=True
                )

                for event in stream:
                    content = event.choices[0].delta.content
                    if content:
                        yield content


    async def get_graphic_recommendation(self) -> ChatResponseGraphicOnly:
        """Obtener recomendación de gráficos para la consulta del usuario

        Args:
            query: La consulta del usuario
        """

        self.messages.append(
            {
                "role": "system",
                "content": """
                Considera la última información obtenida del tool para hacer el gráfico.
                Según tu recomendación anterior de gráfico, definir "barras", "líneas"
                o "pastel".
                Si detectas que no es necesario gráfico, no colocar nada.
                """
            }
        )
        
        # Enviar la consulta al modelo GPT-4o
        response = self.client.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            response_format=ChatResponseGraphicOnly,
            messages=self.messages,
        )


        # Retornar la respuesta parseada
        if response.choices[0].message.parsed:
            # Guardar la respuesta del modelo
            self.messages.append(
                {
                    "role": "assistant",
                    "content": response.choices[0].message.parsed.model_dump_json()
                }
            )
            return response.choices[0].message.parsed
        else:
            print("No hay recomdnación de gráfico")
            self.messages.append(
                {
                    "role": "assistant",
                    "content": "No hubo recomendación de gráfico"
                }
            )
            return ChatResponseGraphicOnly(list_graphics=[]) 


    async def process_query(self, query: str) -> str | ChatResponse:
        """Procesar la consulta del usuario

        Args:
            query: La consulta del usuario
        """
        
        # Preparar el mensaje inicial del chat
        messages: list[ChatCompletionMessageParam] = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": query
            }
        ]

        # Obtener la lista de herramientas disponibles desde el servidor MCP
        response = await self.session.list_tools()
        available_tools: list[ChatCompletionToolParam] = [
            ChatCompletionToolParam(
                type="function",
                function={
                    "name": tool.name,
                    "description": str(tool.description),
                    "parameters": tool.inputSchema,
                }
            )
            for tool in response.tools
        ]

        # Enviar la consulta al modelo GPT-4o con las herramientas disponibles
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=available_tools,
            max_tokens=1000 # Limitar la respuesta a 1000 tokens
        )

        # Procesar la respuesta del modelo
        final_text = [] # Almacenar la respuesta final hacia el usuario
        assistant_message_content = [] # Almacenar toda la respuesta de la IA

        msg = response.choices[0].message

        # Si el mensaje contiene texto, agregarlo a la respuesta final
        if msg.content:
            final_text.append(msg.content)
            assistant_message_content.append(msg.content)

        # Si el mensaje contiene llamadas a herramientas, procesarlas
        if msg.tool_calls:
            for tool_call in msg.tool_calls:
                tool_name = tool_call.function.name # type: ignore[attr-defined]
                tool_args = json.loads(tool_call.function.arguments) # type: ignore[attr-defined]

                # Llamar a la herramienta en el servidor MCP
                result = await self.session.call_tool(tool_name, tool_args)
                logging.info(f"Llamada a herramienta {tool_name} con los argumentos {tool_args}")

                # Actualizar el contexto del chat con la llamada a la herramienta y su resultado
                messages.append({
                    "role": "assistant",
                    "tool_calls": msg.tool_calls, # type: ignore[attr-defined]
                })
                messages.append({
                    "role": "tool",
                    "content": result.content,
                    "tool_call_id": tool_call.id  # type: ignore[attr-defined]
                })

                # Volver a enviar la consulta al modelo con el contexto actualizado
                response = self.client.chat.completions.parse(
                    model="gpt-4o-2024-08-06",
                    response_format=ChatResponse,
                    messages=messages,
                )

                # Agregar la nueva respuesta del modelo a la respuesta final
                if response.choices[0].message.parsed:
                    return response.choices[0].message.parsed


        return "\n".join(final_text)


    async def chat_loop(self):
        """Bucle de chat para interactuar con el usuario

        Args: none
        """

        print("\nInicio de cliente MCP.")
        print("Para salir, escribe 'quit'.")

        while True:
            try:
                query = input("\nMensaje: ").strip()

                # Salir si el usuario escribe 'quit'
                if query.lower() == 'quit':
                    break

                response = await self.process_query(query)
                print("\n" + str(response))

            except Exception as e:
                logging.error(f"Error en el bucle de chat: {str(e)}")


    async def cleanup(self):
        """Limpiar los recursos utilizados por el cliente MCP

        Args: none
        """

        await self.exit_stack.aclose()


# Método para procesar una consulta externa desde API u otro módulo
async def procesar_mensaje(client: MCPClient, consulta: str, mcp_path: str) -> str | ChatResponse:
    """Procesar una consulta utilizando el cliente MCP

    Args:
        client: Instancia del cliente MCP
        consulta: Consulta del usuario
    """

    try:
        await client.connect_to_server(mcp_path)
        respuesta = await client.process_query(consulta)
        return respuesta
    finally:
        await client.cleanup()

# Método para procesar una consulta externa desde API u otro módulo
async def procesar_mensaje_stream(client: MCPClient, consulta: str, mcp_path: str):
    """Procesar una consulta en forma stream utilizando el cliente MCP

    Args:
        client: Instancia del cliente MCP
        consulta: Consulta del usuario
    """

    try:
        await client.connect_to_server(mcp_path)
        async for chunk in client.process_query_stream(consulta):
            yield chunk
            await asyncio.sleep(0)

        graphic_recommendation = await client.get_graphic_recommendation()
        yield "[[GRAPHIC]]" + graphic_recommendation.model_dump_json()

    finally:
        await client.cleanup()

# Método principal para ejecutar el cliente MCP de forma independiente
async def main():
    if len(sys.argv) < 2:
        print("Forma de uso: python main.py <path_al_script_del_servidor>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())
