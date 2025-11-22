import asyncio
import json
from dotenv import load_dotenv
from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from app.agent.tools import execute_sql_query, graphic_recomendation, format_insight
from google.genai import types

load_dotenv() # Cargar variables de entorno

# Definir constantes sobre el modelo
MODEL_NAME = 'openai/gpt-4o'

# Definir constantes para indentificar la sesión
APP_NAME = 'Cerámica de Altura App'
USER_ID = 'user_1'
SESSION_ID = 'session_1'

# Función para manejar el agente de forma asíncrona
async def call_agent_async(query: str, runner: Runner, user_id, session_id):
  content = types.Content(role='user', parts=[types.Part(text=query)])

  final_response_text = "El agente no ha enviado ningún mensaje." # Mensaje por defecto

  async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
      print('El evento es: ', event.model_dump_json())
      if event.content and event.content.parts:
          for part in event.get_function_responses():
              print('EL PART ES: ', part.model_dump_json())
              if part.name == 'execute_sql_query':
                  print('Se usó este tool de sql')
                  yield '[[TOOL]]' + json.dumps(part.response, default=str)
                  await asyncio.sleep(0.1)
              elif part.name == 'graphic_recomendation':
                  print('Se usó este tool de graphics')
                  yield '[[TOOL-GRAPHIC]]' + json.dumps(part.response, default=str)
                  await asyncio.sleep(0.1)
              elif part.name == 'format_insight':
                  print('Se usó este tool para los insights')
                  yield '[[INSIGHT]]' + json.dumps(part.response, default=str) 
                  await asyncio.sleep(0.1)

      if event.is_final_response(): # Valida si es el mensaje final que tiene el texto final del modelo
          if event.content and event.content.parts:
             final_response_text = event.content.parts[0].text
          elif event.actions and event.actions.escalate: # Handle potential errors/escalations
             final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
          break

  if final_response_text:
      print(f"\nEl mensaje es: {final_response_text}\n")
      yield '[[MENSAJE]]' + final_response_text
      await asyncio.sleep(0.1)
  else:
      yield 'Error response'


# Función para iniciar el agente
async def init_agent():
    # Se define nuestro agente de Cerámica de Altura
    agent = Agent(
        name='agente_ceramica_de_altura',
        model=LiteLlm(model=MODEL_NAME),
        description='Extrae información de la bd de inventario de Cerámica de Altura',
        instruction="""
        Eres un asistente que ayuda a otorgar información de la base de datos.
        Puedes usar la herramientas execute_sql_query para las consultas de
        información de lo que respecta al inventario de Cerámica de Altura.
        SIEMPRE que se te pida un gráfico, usa la herramienta graphic_recomendation.
        No enviar imágenes en base64 del gráfic. Solo usar el tool.
        No enviar imágenes del gráfico. Solo usar el tool.
        No enviar archivos adjuntos.
        SIEMPRE que se pida un insight sobre la data obtenida partir de execute_sql_query,
        usar el tool format_insight.
        Las respuestas textuales deben ser del mismo tamaño todas las partes. No usar
        tamaños de letra grandes.
        """,
        tools=[execute_sql_query, graphic_recomendation, format_insight],
    )
    print(f"Se ha creado el agente {agent.name} usando el modelo {MODEL_NAME}")

    # Iniciar el session service para memoria no persistente
    session_service = InMemorySessionService()
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    print(f"Sesión credada {APP_NAME} {USER_ID} {SESSION_ID}")

    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service
    )
    print(f"Se creó el Runner {runner.agent.name}")
    
    return runner
