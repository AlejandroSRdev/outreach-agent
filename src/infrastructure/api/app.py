from contextlib import asynccontextmanager
import asyncio
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI

from src.config.settings import settings
from src.infrastructure.ai.config import GENERATION_CONFIG, REFINEMENT_CONFIG
from src.infrastructure.ai.client import OpenAIClient
from src.infrastructure.research.provider import DBResearchProvider
from src.application.services.pipeline import OutreachPipeline
from src.application.services.orchestrator import BatchOrchestrator
from src.infrastructure.api.routers.health import router as health_router
from src.infrastructure.api.routers.leads import router as leads_router
from src.infrastructure.db.connection import verify_database_connection
from src.infrastructure.db.campaigns import PGCampaignRepository
from src.infrastructure.db.executions import PGExecutionRepository
from src.application.use_cases.create_campaign import CreateCampaignUseCase
from src.application.use_cases.start_execution import StartExecutionUseCase
from src.infrastructure.api.routers.campaigns import router as campaigns_router


# Defined before outreach_router is imported to resolve the circular import:
# outreach.py imports get_orchestrator from this module at load time.
def get_orchestrator(request: Request) -> BatchOrchestrator:
    return request.app.state.orchestrator


from src.infrastructure.api.routers.outreach import router as outreach_router  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    from src.infrastructure.logging.setup import configure_logging
    configure_logging(settings.log_level)
    await verify_database_connection()
    openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
    research = DBResearchProvider()
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
    orchestrator = BatchOrchestrator(pipeline=pipeline, semaphore=semaphore)
    app.state.orchestrator = orchestrator
    campaign_repo = PGCampaignRepository()
    execution_repo = PGExecutionRepository()
    create_campaign_uc = CreateCampaignUseCase(campaign_repo)
    start_execution_uc = StartExecutionUseCase(campaign_repo, execution_repo, orchestrator)
    app.state.create_campaign_use_case = create_campaign_uc
    app.state.start_execution_use_case = start_execution_uc
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
app.include_router(leads_router)
app.include_router(campaigns_router, prefix="/campaigns")
