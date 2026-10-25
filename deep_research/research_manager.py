"""Application runner: one Manager run, with event display and result persistence."""

import json
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from uuid import uuid4

from agents import RunConfig, Runner, gen_trace_id, trace
from agents.run_config import ToolExecutionConfig

from .config import Settings, validate_credentials
from .manager_agent import build_manager
from .providers import build_provider
from .recipients import validate_recipient
from .state import ResearchState, ResearchUpdate


class ResearchManager:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings.from_env()

    async def run(
        self, query: str, send_email: bool = False, recipient: str = ""
    ) -> AsyncIterator[ResearchUpdate]:
        query = query.strip()
        if not query:
            raise ValueError("Please enter a research question.")
        recipient = validate_recipient(recipient, required=send_email)
        validate_credentials(send_email, self.settings)
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ_") + uuid4().hex[:8]
        state = ResearchState(
            self.settings.output_root / run_id,
            send_email=send_email,
            recipient=recipient,
            query=query,
        )
        state.save_evidence()
        run_config = RunConfig(
            model_provider=build_provider(self.settings),
            tracing_disabled=not self.settings.tracing,
            trace_include_sensitive_data=False,
            # DeepSeek ignores parallel_tool_calls. Serialize execution in the SDK,
            # including nested function tools, instead of relying on that API flag.
            tool_execution=ToolExecutionConfig(max_function_tool_concurrency=1),
        )
        manager_agent = build_manager(self.settings, state, run_config)
        trace_id = gen_trace_id()
        log = [f"Starting Research Manager (agents as tools; provider={self.settings.provider})."]
        if self.settings.tracing:
            log.append(f"Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}")

        def snapshot() -> ResearchUpdate:
            files = sorted(str(path.resolve()) for path in state.output_dir.glob("*"))
            return ResearchUpdate(
                status="\n".join(log[:-1] + state.diagnostics + log[-1:]),
                report=state.report.markdown_report if state.report else "",
                files=files,
            )

        yield snapshot()
        with trace(
            "Deep Research via Tools", trace_id=trace_id, disabled=not self.settings.tracing
        ):
            failure = None
            try:
                # This is the ONLY top-level Runner call. The LLM chooses tool calls;
                # there is no Python planner -> searcher -> writer -> email sequence.
                result = Runner.run_streamed(
                    manager_agent,
                    input=f"Research question: {query}",
                    run_config=run_config,
                    max_turns=self.settings.search_count + 12,
                )
                async for event in result.stream_events():
                    if event.type != "run_item_stream_event":
                        continue
                    if event.name == "tool_called":
                        log.append(f"Manager called: {event.item.raw_item.name}")
                        yield snapshot()
                    elif event.name == "tool_output":
                        log.append("Tool returned control to Manager.")
                        yield snapshot()

                # Validate completion; this check does not execute missing stages.
                if not state.plan or len(state.searches) < len(state.plan.searches):
                    raise RuntimeError("Manager stopped before completing the planned searches.")
                if state.report is None or state.email_receipt is None:
                    raise RuntimeError("Manager stopped without a report or email receipt.")
                log.append(f"Complete. Email status: {state.email_receipt['status']}")
            except Exception as exc:
                # Do not log provider responses or credentials into local artifacts.
                log.append(f"Research failed ({type(exc).__name__}). Partial files were retained.")
                failure = exc
            finally:
                state.output_dir.mkdir(parents=True, exist_ok=True)
                (state.output_dir / "workflow.json").write_text(
                    json.dumps(
                        {"events": log, "diagnostics": state.diagnostics, "trace_id": trace_id},
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
        yield snapshot()
        if failure is not None:
            raise failure
