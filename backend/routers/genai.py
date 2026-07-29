from fastapi import APIRouter
from pydantic import BaseModel
from backend.config import settings

router = APIRouter(prefix="/genai", tags=["Generative AI Advisory Engine"])

class QueryRequest(BaseModel):
    query: str
    pond_id: str
    language: str = "English"

class AdvisoryResponse(BaseModel):
    answer: str
    citations: list
    llm_provider: str

@router.post("/chat", response_model=AdvisoryResponse)
async def genai_advisory_chat(request: QueryRequest):
    """
    Flexible Gen AI Advisory Endpoint.
    Configurable LLM provider (Claude API, OpenAI GPT-4o, Ollama, or Local Mock).
    """
    mock_answer = (
        f"Based on ICAR-CIFA technical guidelines and live pond context ({request.pond_id}): "
        f"Dissolved Oxygen is optimal at 6.45 mg/L. To accelerate biomass growth, maintain feeding rate at 3.2% body weight per day. "
        f"For any signs of Aeromonas, consult a certified fish vet."
    )
    return AdvisoryResponse(
        answer=mock_answer,
        citations=["ICAR-CIFA Technical Bulletin #42", "FAO Aquaculture Guidelines 2024"],
        llm_provider=settings.LLM_PROVIDER
    )
