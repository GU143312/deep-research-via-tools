from __future__ import annotations

import os

import gradio as gr
from dotenv import load_dotenv

from deep_research import ResearchService
from styles import CSS, EXAMPLES, HEADER_HTML

load_dotenv(override=True)


def allow_local_gradio_healthcheck() -> None:
    """Keep local Gradio startup checks out of an OS-level HTTP proxy."""
    required = {"127.0.0.1", "localhost"}
    configured = {
        item.strip() for item in os.getenv("NO_PROXY", "").split(",") if item.strip()
    }
    value = ",".join(sorted(configured | required))
    os.environ["NO_PROXY"] = value
    os.environ["no_proxy"] = value


allow_local_gradio_healthcheck()


async def run_research(query: str, send_email: bool):
    service = ResearchService()
    async for update in service.run(query, send_email=send_email):
        yield update


with gr.Blocks(title="LangGraph Deep Research") as demo:
    gr.HTML(HEADER_HTML)
    with gr.Row():
        query = gr.Textbox(
            placeholder="输入需要深入研究的问题…",
            show_label=False,
            lines=2,
            autofocus=True,
            elem_id="query",
            scale=5,
        )
        run_button = gr.Button("开始研究", variant="primary", elem_id="run", scale=1)
    email = gr.Checkbox(label="完成后通过网易邮箱发送报告", value=False)
    gr.Examples(examples=EXAMPLES, inputs=query, label="示例问题")
    report = gr.Markdown(elem_id="report")

    run_button.click(run_research, inputs=[query, email], outputs=report)
    query.submit(run_research, inputs=[query, email], outputs=report)


if __name__ == "__main__":
    demo.queue().launch(theme=gr.themes.Base(), css=CSS)

