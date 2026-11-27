"""Per-run results; never shared between users or research requests."""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .planner_agent import WebSearchPlan
from .writer_agent import ReportData


@dataclass
class SearchEvidence:
    plan_id: int | None
    query: str
    reason: str
    summary: str


@dataclass
class ResearchState:
    output_dir: Path
    send_email: bool = False
    recipient: str = ""
    plan: WebSearchPlan | None = None
    searches: list[SearchEvidence] = field(default_factory=list)
    report: ReportData | None = None
    email_receipt: dict | None = None
    email_attempted: bool = False
    query: str = ""
    diagnostics: list[str] = field(default_factory=list)
    format_failures: dict[str, int] = field(default_factory=dict)

    def missing_plan_ids(self) -> list[int]:
        if self.plan is None:
            return []
        completed = {search.plan_id for search in self.searches}
        return [i for i in range(1, len(self.plan.searches) + 1) if i not in completed]

    def remaining_extra_searches(self) -> int:
        return 2 - sum(search.plan_id is None for search in self.searches)

    def numbered_plan(self) -> dict | None:
        if self.plan is None:
            return None
        return {
            "searches": [
                {"plan_id": i, **item.model_dump()} for i, item in enumerate(self.plan.searches, 1)
            ]
        }

    def save_evidence(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "evidence.json").write_text(
            json.dumps(
                {
                    "query": self.query,
                    "plan": self.numbered_plan(),
                    "searches": [asdict(search) for search in self.searches],
                    "search_summaries": [search.summary for search in self.searches],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


@dataclass
class ResearchUpdate:
    status: str
    report: str = ""
    files: list[str] = field(default_factory=list)
