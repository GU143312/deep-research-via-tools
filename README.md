# Deep Research Assignment

This assignment includes two implementations of a tool-orchestrated deep research agent. Both plan searches, collect evidence, and write a report with source citations. Each can email the report when configured.

| Subgroup | Implementation | Project README |
| --- | --- | --- |
| 1 | The OpenAI Agents SDK manager calls the planning, search, writing, and email agents as tools. | [Subgroup 1 · SDK](subgroup1/README.md) |
| 2 | A LangGraph state graph uses `ToolNode` to run tools, including concurrent Tavily searches. | [Subgroup 2 · LangGraph](subgroup2/README.md) |

Run each implementation from its own directory. Each README covers setup, configuration, and tests. Both projects include an `.env.example` template.
