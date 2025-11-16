from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.agent.route import router_agent_chat
from app.config import config

# Crear una instancia de la aplicación FastAPI 
app = FastAPI(
    title="Cerámica de Altura - Agent API",
    description="API para el agente de Cerámica de Altura utilizando FastMCP y MySQL.",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Solo para desarrollo
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

# Incluir el router del agente
app.include_router(router_agent_chat, prefix="/api/v1")

# Iniciar la aplicación
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=config.PORT, log_level="info")
