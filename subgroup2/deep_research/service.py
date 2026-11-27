from __future__ import annotations

from collections.abc import AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI

from .config import Settings
from .graph import build_graph
from .toolkit import ResearchToolkit, default_toolkit

TOOL_LABELS = {
    "plan_research": "规划研究问题",
    "search_web": "检索网页证据",
    "write_report": "撰写引用报告",
    "send_report_email": "发送报告邮件",
}


class ResearchService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_env()

    def _model(self) -> ChatOpenAI:
        return ChatOpenAI(
            model=self.settings.model,
            api_key=self.settings.deepseek_api_key,
            base_url=self.settings.deepseek_base_url,
            temperature=0,
            max_retries=2,
            extra_body={"thinking": {"type": "disabled"}},
        )

    async def run(self, question: str, *, send_email: bool = False) -> AsyncIterator[str]:
        question = question.strip()
        if not question:
            yield "请输入一个研究问题。"
            return

        try:
            self.settings.validate(send_email=send_email)
        except ValueError as exc:
            yield f"### 配置未完成\n\n{exc}\n\n请复制 `.env.example` 为 `.env` 并填写密钥。"
            return

        model = self._model()
        toolkit = default_toolkit(
            model=model,
            tavily_api_key=self.settings.tavily_api_key,
            max_results=self.settings.max_results,
            search_count=self.settings.search_count,
            netease_email=self.settings.netease_email,
            netease_auth_code=self.settings.netease_auth_code,
            email_to=self.settings.email_to,
            smtp_host=self.settings.smtp_host,
            smtp_port=self.settings.smtp_port,
        )
        async for update in self.run_with(question, toolkit=toolkit, send_email=send_email):
            yield update

    async def run_with(
        self,
        question: str,
        *,
        toolkit: ResearchToolkit,
        send_email: bool = False,
    ) -> AsyncIterator[str]:
        graph = build_graph(model=toolkit.model, toolkit=toolkit, include_email=send_email)
        completed: list[str] = []
        yield self._progress(completed, current="启动研究管理器")

        try:
            async for event in graph.astream(
                {"messages": [HumanMessage(content=question)]},
                stream_mode="updates",
                config={"recursion_limit": 30},
            ):
                manager_update = event.get("manager")
                if manager_update:
                    message = manager_update["messages"][-1]
                    if isinstance(message, AIMessage) and message.tool_calls:
                        names = [TOOL_LABELS.get(call["name"], call["name"]) for call in message.tool_calls]
                        yield self._progress(completed, current="、".join(names))

                tools_update = event.get("tools")
                if tools_update:
                    messages = tools_update.get("messages", [])
                    for message in messages:
                        if isinstance(message, ToolMessage):
                            label = TOOL_LABELS.get(message.name or "", message.name or "工具")
                            completed.append(label)
                    if toolkit.report is not None:
                        yield toolkit.report.markdown_report
                    else:
                        yield self._progress(completed, current="管理器正在决定下一步")
        except Exception as exc:  # noqa: BLE001 - UI boundary must surface provider failures.
            yield f"### 研究中断\n\n`{type(exc).__name__}`: {exc}"
            return

        if toolkit.report is not None:
            yield toolkit.report.markdown_report
        else:
            yield "### 未生成报告\n\n管理器在调用报告工具之前结束了运行，请重试。"

    @staticmethod
    def _progress(completed: list[str], *, current: str) -> str:
        done = "\n".join(f"- ✅ {item}" for item in completed)
        if done:
            done += "\n"
        return f"### 深度研究进行中\n\n{done}- ⏳ {current}…"

