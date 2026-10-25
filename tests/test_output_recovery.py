import json

import pytest
from agents import ModelBehaviorError, RunConfig, Runner

from deep_research.config import Settings
from deep_research.research_manager import ResearchManager
from deep_research.state import ResearchState
from deep_research.structured_output import ResearchOutputSchema, StructuredOutputError
from deep_research.writer_agent import ReportData, build_writer

from .fake_model import ScriptedModel, message, tool_call
from .test_workflow import REPORT, script, use_model


def test_complete_json_fence_preserves_report_exactly():
    diagnostics = []
    schema = ResearchOutputSchema(ReportData, "Writer", diagnostics)
    result = schema.validate_json("```json\n" + REPORT.model_dump_json() + "\n```")
    assert result == REPORT
    assert "validated" in diagnostics[-1]


@pytest.mark.parametrize(
    "invalid",
    [
        '{"short_summary":"private-source-text", "markdown_report":"unfinished',
        '{"markdown_report":"missing other required fields"}',
        "Explanation before JSON\n" + REPORT.model_dump_json(),
    ],
)
def test_incomplete_output_is_not_filled_in_or_exposed(invalid):
    diagnostics = []
    schema = ResearchOutputSchema(ReportData, "Writer", diagnostics)
    with pytest.raises(StructuredOutputError) as caught:
        schema.validate_json(invalid)
    assert "private-source-text" not in str(caught.value)
    assert "private-source-text" not in " ".join(diagnostics)


@pytest.mark.parametrize("stage", ["Planner", "Writer"])
async def test_manager_recovers_from_one_format_failure(tmp_path, monkeypatch, stage):
    steps = script()
    role, tool = (
        ("research planner", "plan_research")
        if stage == "Planner"
        else ("senior researcher", "write_report")
    )
    position = next(i for i, step in enumerate(steps) if step[0] == role)
    steps[position:position] = [
        (role, [message('{"truncated":')]),
        ("Research Manager", [tool_call(tool, input="Regenerate complete valid JSON.")]),
    ]
    model = use_model(monkeypatch, steps)
    updates = [
        u
        async for u in ResearchManager(Settings(search_count=1, output_root=tmp_path)).run(
            "Original question"
        )
    ]
    assert not model.steps
    assert "Complete." in updates[-1].status
    assert updates[-1].report == REPORT.markdown_report
    assert updates[-1].status.count("Manager called: search_web") == 1
    manager_inputs = json.dumps([c[1] for c in model.calls if c[0] == "Research Manager"])
    assert "retry_required" in manager_inputs
    saved = json.loads(next(tmp_path.glob("*/evidence.json")).read_text(encoding="utf-8"))
    assert saved["query"] == "Original question"
    assert len(saved["search_summaries"]) == 1
    workflow = json.loads(next(tmp_path.glob("*/workflow.json")).read_text(encoding="utf-8"))
    assert any("format failure 1" in line for line in workflow["diagnostics"])


async def test_second_writer_failure_stops_with_downloadable_evidence(tmp_path, monkeypatch):
    steps = script()
    position = next(i for i, step in enumerate(steps) if step[0] == "senior researcher")
    steps = steps[:position] + [
        ("senior researcher", [message('{"unfinished":')]),
        ("Research Manager", [tool_call("write_report", input="Retry valid JSON.")]),
        ("senior researcher", [message('{"unfinished":')]),
    ]
    model = use_model(monkeypatch, steps)
    updates = []
    with pytest.raises(ModelBehaviorError):
        async for update in ResearchManager(Settings(search_count=1, output_root=tmp_path)).run(
            "Original question"
        ):
            updates.append(update)
    assert not model.steps
    assert not updates[-1].report
    assert "Complete." not in updates[-1].status
    assert any(p.endswith("evidence.json") for p in updates[-1].files)
    assert any(p.endswith("workflow.json") for p in updates[-1].files)
    assert not list(tmp_path.glob("*/email.eml"))


async def test_writer_receives_evidence_saved_after_agent_creation(tmp_path):
    state = ResearchState(tmp_path, query="Original question")
    agent = build_writer(Settings(), state)
    state.searches.append("Saved evidence: https://example.com/evidence")

    class InspectModel(ScriptedModel):
        async def get_response(self, *args, **kwargs):
            prompt = kwargs["system_instructions"]
            assert "Original question" in prompt
            assert state.searches[0] in prompt
            return await super().get_response(*args, **kwargs)

    await Runner.run(
        agent,
        "Write from saved evidence.",
        run_config=RunConfig(
            model=InspectModel([("senior researcher", [message(REPORT.model_dump_json())])]),
            tracing_disabled=True,
        ),
    )
