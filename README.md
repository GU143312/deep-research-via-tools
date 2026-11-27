# Deep Research Assignment

This assignment includes two implementations of a tool-orchestrated deep research agent. Both turn a research question into search tasks, collect evidence, and produce a Markdown report with source citations. Email delivery is optional in both implementations.

| Subgroup | Implementation | Project README |
| --- | --- | --- |
| 1 | An OpenAI Agents SDK manager calls specialist agents as tools. | [OpenAI Agents SDK README](subgroup1/README.md) |
| 2 | A LangGraph manager routes tools through a state graph. `ToolNode` can run Tavily searches concurrently. | [LangGraph README](subgroup2/README.md) |

## Subgroup 2 — LangGraph

The LangGraph implementation uses DeepSeek for planning and writing, Tavily for evidence retrieval, and Gradio to show progress and the final report. It supports optional report delivery through NetEase SMTP.

- [Setup, architecture, and tests](subgroup2/README.md)
- [File-level team contributions](subgroup2/README.md#team-contributions)

Run each implementation from its own directory and use its `.env.example` template to configure the services it needs.
