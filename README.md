# Deep Research Assignment

This assignment includes two implementations of a tool-orchestrated deep research agent. Both turn a research question into search tasks, collect evidence, and produce a Markdown report with source citations. Email delivery is optional in both implementations.

## Team contributions

Our team completed the same assignment in two subgroups. Each subgroup developed its own implementation and recorded contributions within that implementation, so each subgroup's percentages total 100%. The three members of Subgroup 2 contributed equally. If a single breakdown is required for the whole assignment, we propose giving each implementation 50% weight. The final column uses that convention.

| Subgroup | Team member | Contribution | Within subgroup | Overall (50/50 split) |
| --- | --- | --- | ---: | ---: |
| 1 · OpenAI Agents SDK | Gu Lantian | Led SDK development and integrated the four specialist agents, model providers, and web and command-line interfaces. | 50% | 25% |
| 1 · OpenAI Agents SDK | Liu Chang | Tested the workflow, model and search requests, error recovery, recipient selection, and SMTP delivery. | 20% | 10% |
| 1 · OpenAI Agents SDK | Sun Haojun | Developed an alternative implementation and compared approaches. Added search coverage checks, retry handling, report and email safeguards, and regression tests. | 30% | 15% |
| 2 · LangGraph | Wang Jianyu | Built the LangGraph workflow, research tools, and data schemas, and streamed progress and reports to the interface. | 1/3 (33⅓%) | 1/6 (16⅔%) |
| 2 · LangGraph | Tu Jiaen | Integrated Tavily search and NetEase SMTP, managed configuration and dependencies, and tested both clients and their settings. | 1/3 (33⅓%) | 1/6 (16⅔%) |
| 2 · LangGraph | Li Tangzishun | Built the Gradio interface, tested the full workflow and model output formats, and documented setup and testing. | 1/3 (33⅓%) | 1/6 (16⅔%) |
| **Team total** | | | | **100%** |

### File-level responsibilities

Paths are relative to the subgroup folder shown in the first column.

| Subgroup | Team member | Files | Responsibility |
| --- | --- | --- | --- |
| 1 | Gu Lantian | `deep_research/manager_agent.py`, `deep_research/research_manager.py`, `deep_research/app.py`, `deep_research/__main__.py` | Integrated the four specialist tools with the Manager and connected the run loop and progress updates to the web and CLI entry points. |
| 1 | Gu Lantian | `deep_research/planner_agent.py`, `deep_research/search_agent.py`, `deep_research/writer_agent.py`, `deep_research/email_agent.py` | Led integration of the specialists for planning searches, collecting evidence, writing reports, and preparing or sending email. |
| 1 | Gu Lantian | `deep_research/providers.py`, `deep_research/config.py`, `deep_research/deepseek_search.py`, `deep_research/structured_output.py` | Integrated provider configuration, web search, and validation of structured plans and reports. |
| 1 | Liu Chang | `tests/test_workflow.py`, `tests/test_output_recovery.py`, `tests/fake_model.py`, `tests/conftest.py` | Verified the full workflow offline using scripted model responses, including incomplete runs and recovery from malformed output. |
| 1 | Liu Chang | `tests/test_deepseek.py`, `tests/test_regressions.py`, `tests/test_recipients.py`, `tests/test_smtp.py` | Checked search and model requests, failure handling, recipient selection, email preview, and SMTP behavior. |
| 1 | Sun Haojun | `deep_research/state.py`, `deep_research/manager_agent.py` | Tracked evidence by plan ID, enforced the two-extra-search limit, preserved the question on planner retries, and checked prerequisites before writing or preparing email. |
| 1 | Sun Haojun | `deep_research/writer_agent.py`, `deep_research/manager_agent.py`, `deep_research/research_manager.py` | Paired each query with its evidence for the Writer, returned a save confirmation and summary to the Manager, and checked for missing plan IDs before marking a run complete. |
| 1 | Sun Haojun | `tests/test_workflow.py`, `tests/test_output_recovery.py` | Added targeted regression coverage for repeated searches, early writing and email requests, exhausted search allowances, and retention of the question on retry. |
| 2 | Wang Jianyu | `deep_research/graph.py` | Built the LangGraph state graph, manager node, and tool-call routing. |
| 2 | Wang Jianyu | `deep_research/toolkit.py` | Implemented the research planning, web search, report writing, and email tools. |
| 2 | Wang Jianyu | `deep_research/service.py`, `deep_research/__init__.py` | Integrated the model, tools, and workflow, and streamed progress and reports to the UI. |
| 2 | Wang Jianyu | `deep_research/schemas.py` | Defined schemas for search plans, sources, and reports, including normalization for model output. |
| 2 | Tu Jiaen | `deep_research/clients.py` | Integrated Tavily search and NetEase SMTP, including search result normalization and email delivery. |
| 2 | Tu Jiaen | `deep_research/config.py`, `.env.example`, `pyproject.toml` | Managed environment variables, configuration validation, and project dependencies. |
| 2 | Tu Jiaen | `tests/test_clients.py`, `tests/test_config.py` | Tested search result handling, the email client, and configuration behavior. |
| 2 | Li Tangzishun | `app.py`, `styles.py` | Built the Gradio interface for entering questions, displaying progress, and rendering reports. |
| 2 | Li Tangzishun | `tests/test_workflow.py`, `tests/test_schemas.py` | Tested the complete workflow and compatibility with model output. |
| 2 | Li Tangzishun | `README.md`, `.gitignore` | Maintained setup and test instructions and Git ignore rules. |

## Implementations

| Subgroup | Implementation | Project README |
| --- | --- | --- |
| 1 | An OpenAI Agents SDK manager calls specialist agents as tools. | [OpenAI Agents SDK README](subgroup1/README.md) |
| 2 | A LangGraph manager routes tools through a state graph. `ToolNode` can run Tavily searches concurrently. | [LangGraph README](subgroup2/README.md) |

## Subgroup 1 — OpenAI Agents SDK

A manager agent calls specialist agents for planning, web search, report writing, and email. It tracks search coverage against the research plan before writing and supports email previews and optional SMTP delivery.

- [Setup, architecture, and tests](subgroup1/README.md)
- [File-level team contributions](subgroup1/README.md#responsibilities-by-file)

## Subgroup 2 — LangGraph

The LangGraph implementation uses DeepSeek for planning and writing, Tavily for evidence retrieval, and Gradio to show progress and the final report. It supports optional report delivery through NetEase SMTP.

- [Setup, architecture, and tests](subgroup2/README.md)
- [File-level team contributions](subgroup2/README.md#team-contributions)

Run each implementation from its own directory and use its `.env.example` template to configure the services it needs.
