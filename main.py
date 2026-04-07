import uvicorn

from src.config.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        "src.infrastructure.api.app:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.environment == "development",
    )
