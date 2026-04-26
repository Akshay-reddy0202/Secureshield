import instructor
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from typing import Dict
import logging
from app.config import settings

# Setup layer logging
logger = logging.getLogger("SecureShield.ToxicityGuard")

class ToxicityReport(BaseModel):
    is_toxic: bool = Field(description="True if the content exceeds toxicity thresholds")
    score: float = Field(description="Overall toxicity score from 0.0 to 1.0")
    reason: str = Field(description="Brief explanation of the classification")
    categories: Dict[str, float] = Field(
        description="Dictionary of category scores (Hate, Harassment, Threat, Self-harm, Sexual)"
    )

class ToxicityEngine:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None:
            cls._client = instructor.from_openai(
                AsyncOpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=settings.OPENROUTER_API_KEY,
                    timeout=30.0 # Guard timeout
                ),
                mode=instructor.Mode.JSON,
            )
        return cls._client

async def check_toxicity(text: str) -> bool:
    """
    Analyzes text for toxicity using an LLM-as-a-Judge approach.
    Returns True if SAFE, False if BLOCKED.
    """
    client = ToxicityEngine.get_client()
    
    try:
        # Use a fast, context-aware model for content filtering
        result = await client.chat.completions.create(
            model=settings.GUARD_MODEL,
            response_model=ToxicityReport,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Content Safety Classifier for an Enterprise AI Gateway. "
                        "Analyze the user input for toxicity including Hate Speech, Harassment, "
                        "Threats, Self-harm, and Sexual content.\n\n"
                        "Classify the text and provide scores from 0.0 to 1.0 for each category. "
                        "If the overall score is > 0.7 or any category is > 0.8, mark is_toxic=true."
                    )
                },
                {"role": "user", "content": text}
            ],
        )
        
        if result.is_toxic:
            logger.warning(f"BLOCKED_TOXICITY: Score {result.score} - {result.reason}")
            return False
        
        return True

    except Exception as e:
        logger.error(f"Toxicity analysis CRITICAL ERROR: {str(e)}")
        # FAIL-SECURE: Block if we cannot verify safety
        return False

