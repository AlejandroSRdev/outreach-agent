from contextlib import asynccontextmanager
import asyncio
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI

from src.config.settings import settings
from src.infrastructure.ai.config import RESEARCH_CONFIG, GENERATION_CONFIG, REFINEMENT_CONFIG
from src.infrastructure.ai.client import OpenAIClient
from src.infrastructure.research.provider import LLMResearchProvider
from src.application.services.pipeline import OutreachPipeline
from src.application.services.orchestrator import BatchOrchestrator
from src.infrastructure.api.routers.health import router as health_router


# Defined before outreach_router is imported to resolve the circular import:
# outreach.py imports get_orchestrator from this module at load time.
def get_orchestrator(request: Request) -> BatchOrchestrator:
    return request.app.state.orchestrator


from src.infrastructure.api.routers.outreach import router as outreach_router  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    research = LLMResearchProvider(client=openai_client, config=RESEARCH_CONFIG)
    ai = OpenAIClient(
        client=openai_client,
        generation_config=GENERATION_CONFIG,
        refinement_config=REFINEMENT_CONFIG,
    )
    pipeline = OutreachPipeline(
        research=research,
        ai=ai,
        research_timeout_s=settings.research_timeout_s,
        generation_timeout_s=settings.generation_timeout_s,
        refinement_timeout_s=settings.refinement_timeout_s,
    )
    semaphore = asyncio.Semaphore(settings.max_concurrent_pipelines)
    app.state.orchestrator = BatchOrchestrator(pipeline=pipeline, semaphore=semaphore)
    yield


app = FastAPI(title="Outreach Agent", version="0.1.0", lifespan=lifespan)

frontend_url = os.getenv("FRONTEND_URL")
origins = [frontend_url] if frontend_url else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(outreach_router, prefix="/outreach")
