"""Gradio entry point: python -m deep_research.app."""

import gradio as gr

from .errors import explain_error
from .research_manager import ResearchManager


async def run(query: str, send_email: bool, recipient: str = ""):
    # Clear the previous research result before starting a new run.
    yield "Starting...", "", []
    status, report, files = "Starting...", "", []
    try:
        async for update in ResearchManager().run(
            query, send_email=send_email, recipient=recipient
        ):
            status, report, files = update.status, update.report, update.files
            yield status, report, files
    except Exception as exc:
        # Raising gr.Error would replace useful partial outputs with red error panels.
        yield status + "\n" + explain_error(exc), report, files


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Deep Research — Orchestration via Tools") as ui:
        gr.Markdown(
            "# Deep Research — Orchestration via Tools\n"
            "Research Manager calls Planner, Search, Writer and Email agents as tools.\n\n"
            "Enter a research question to generate an English report. "
            "Choose your email delivery preferences below."
        )
        query = gr.Textbox(label="Research question", lines=3)
        with gr.Group():
            gr.Markdown("### Email settings")
            send_email = gr.Checkbox(label="Send report by email", value=False)
            recipient = gr.Textbox(
                label="Recipient email",
                placeholder="name@example.com",
                info="Required for delivery. Turn sending off to create a report and preview only.",
            )
        submit = gr.Button("Start research", variant="primary")
        status = gr.Textbox(label="Manager tool calls", lines=10, interactive=False)
        report = gr.Markdown()
        files = gr.File(label="Report, email preview and workflow record", file_count="multiple")
        submit.click(
            run, [query, send_email, recipient], [status, report, files], concurrency_limit=1
        )
        query.submit(
            run, [query, send_email, recipient], [status, report, files], concurrency_limit=1
        )
    return ui


if __name__ == "__main__":
    build_ui().queue().launch(server_name="127.0.0.1", share=False, footer_links=[])
