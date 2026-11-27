"""Adapted from ed-donner/agents, 2_openai/deep_research/planner_agent.py."""

from agents import Agent
from pydantic import BaseModel, Field

from .config import Settings
from .structured_output import ResearchOutputSchema


class WebSearchItem(BaseModel):
    reason: str = Field(description="Why this search helps answer the original question.")
    query: str = Field(description="The search term to use.", min_length=1, max_length=128)


class WebSearchPlan(BaseModel):
    searches: list[WebSearchItem] = Field(description="The planned web searches.", min_length=1)


def build_planner(settings: Settings, diagnostics=None) -> Agent:
    return Agent(
        name="Planner Agent",
        instructions=(
            "You are a research planner. Given a research question, produce exactly "
            f"{settings.search_count} complementary web searches and explain each one's purpose. "
            "Cover the important angles and prefer authoritative sources. "
            "Do not answer the research question yourself. Return only a JSON object "
            'with this structure: {"searches":[{"query":"search term","reason":"purpose"}]}. '
            "Use search terms no longer than 128 characters. Do not wrap JSON in code fences."
        ),
        model=settings.model,
        output_type=ResearchOutputSchema(WebSearchPlan, "Planner", diagnostics),
    )
