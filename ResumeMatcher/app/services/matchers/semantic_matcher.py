"""
Semantic matching using OpenAI text-embedding-3-small
"""

import os
import structlog
from openai import AsyncOpenAI

logger = structlog.get_logger()


def _cosine_similarity(a: list, b: list) -> float:
    """Compute cosine similarity without numpy dependency."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class SemanticMatcher:
    """Semantic matching using OpenAI text-embedding-3-small"""

    def __init__(self):
        self.client = None
        self.initialized = False

    async def initialize(self):
        """Initialize the OpenAI async client."""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY is not set in environment")
            self.client = AsyncOpenAI(api_key=api_key)
            self.initialized = True
            logger.info("Semantic matcher initialized with OpenAI embeddings")
        except Exception as e:
            logger.error("Failed to initialize semantic matcher", error=str(e))
            raise

    async def match(self, resume_text: str, job_description: str) -> float:
        """
        Compute semantic similarity between resume and JD using embeddings.

        Returns a score in [0, 1] where 1 = perfect semantic match.
        """
        try:
            if not self.initialized:
                await self.initialize()

            # Truncate inputs to avoid hitting token limits (~8000 chars ≈ 2000 tokens)
            resume_input = resume_text[:8000]
            jd_input = job_description[:8000]

            response = await self.client.embeddings.create(
                model="text-embedding-3-small",
                input=[resume_input, jd_input],
            )

            resume_vec = response.data[0].embedding
            jd_vec = response.data[1].embedding

            # Raw cosine similarity is in [-1, 1]; normalize to [0, 1]
            raw = _cosine_similarity(resume_vec, jd_vec)
            score = (raw + 1) / 2

            logger.debug("Semantic match completed", score=round(score, 4))
            return float(score)

        except Exception as e:
            logger.error("Semantic matching failed", error=str(e))
            return 0.0

    async def cleanup(self):
        """Release client resources."""
        self.client = None
        self.initialized = False
        logger.info("Semantic matcher cleaned up")
