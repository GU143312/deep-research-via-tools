# Deep Research Assignment

This assignment includes two implementations of a tool-orchestrated deep research agent. Both turn a research question into search tasks, collect evidence, and produce a Markdown report with source citations. Email delivery is optional in both implementations.

## Team contributions

Our team completed the same assignment in two subgroups. Each subgroup developed its own implementation and recorded contributions within that implementation, so each subgroup's percentages total 100%. The three members of the LangGraph subgroup contributed equally. If a single breakdown is required for the whole assignment, we propose giving each implementation 50% weight. The final column uses that convention.

| Subgroup | Team member | Contribution | Within subgroup | Overall (50/50 split) |
| --- | --- | --- | ---: | ---: |
| 1 · OpenAI Agents SDK | Gu Lantian | Led SDK development and integrated the four specialist agents, model providers, and web and command-line interfaces. | 50% | 25% |
| 1 · OpenAI Agents SDK | Liu Chang | Tested the workflow, model and search requests, error recovery, recipient selection, and SMTP delivery. | 20% | 10% |
| 1 · OpenAI Agents SDK | Sun Haojun | Developed an alternative implementation and compared approaches. Added search coverage checks, retry handling, report and email safeguards, and regression tests. | 30% | 15% |
| 2 · LangGraph | Wang Jianyu | Built the LangGraph workflow, research tools, and data schemas, and streamed progress and reports to the interface. | 1/3 (33⅓%) | 1/6 (16⅔%) |
| 2 · LangGraph | Tu Jiaen | Integrated Tavily search and NetEase SMTP, managed configuration and dependencies, and tested both clients and their settings. | 1/3 (33⅓%) | 1/6 (16⅔%) |
| 2 · LangGraph | Li Tangzishun | Built the Gradio interface, tested the full workflow and model output formats, and documented setup and testing. | 1/3 (33⅓%) | 1/6 (16⅔%) |
| **Team total** | | | | **100%** |

## Implementations

| Subgroup | Implementation | Project README |
| --- | --- | --- |
| 1 · OpenAI Agents SDK | An OpenAI Agents SDK manager calls specialist agents as tools. | [OpenAI Agents SDK README](subgroup1-openai-agents-sdk/README.md) |
| 2 · LangGraph | A LangGraph manager routes tools through a state graph. `ToolNode` can run Tavily searches concurrently. | [LangGraph README](subgroup2-langgraph/README.md) |

## Subgroup 1 — OpenAI Agents SDK

A manager agent calls specialist agents for planning, web search, report writing, and email. It tracks search coverage against the research plan before writing and supports email previews and optional SMTP delivery.

- [Setup, architecture, and tests](subgroup1-openai-agents-sdk/README.md)

## Subgroup 2 — LangGraph

The LangGraph implementation uses DeepSeek for planning and writing, Tavily for evidence retrieval, and Gradio to show progress and the final report. It supports optional report delivery through NetEase SMTP.

- [Setup, architecture, and tests](subgroup2-langgraph/README.md)

Run each implementation from its own directory and use its `.env.example` template to configure the services it needs.
