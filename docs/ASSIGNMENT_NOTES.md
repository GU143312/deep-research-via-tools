# Lab 4 作业改造说明

## 目标与完成内容

截图中的任务是对 `agents/2_openai/deep_research/` 做 **Orchestration via Tools**。
本实现将 Lab 2 的 Sales Manager 调用邮件生成 Agent 的方式迁移到 Deep Research：
Research Manager 调用规划、搜索、报告和邮件四种专业能力，并接收它们的返回结果。

## 改造前后

原 `research_manager.py` 的执行方式：

```python
search_plan = await self.plan_searches(query)
search_results = await self.perform_searches(search_plan)
report = await self.write_report(query, search_results)
await self.send_email(report)
```

步骤由 Python 程序决定。原 `ResearchManager` 不是 Agents SDK 的 Agent。

改造后的核心（省略结果保存回调，实际实现见 `deep_research/manager_agent.py`）：

```python
planner_tool = planner_agent.as_tool(
    tool_name="plan_research",
    tool_description="Plan web searches for the original research question.",
)
search_tool = search_agent.as_tool(
    tool_name="search_web",
    tool_description="Search one term and return evidence and source URLs.",
)
writer_tool = writer_agent.as_tool(
    tool_name="write_report",
    tool_description="Write a full report from the question and research evidence.",
)
email_tool = email_agent.as_tool(
    tool_name="email_report",
    tool_description="Format the full report and create a preview or send it.",
)
manager_agent = Agent(
    name="Research Manager",
    instructions=INSTRUCTIONS,
    tools=[planner_tool, search_tool, writer_tool, email_tool],
    model=settings.model,
)
```

外层只有一个 `Runner.run_streamed(manager_agent, ...)`。
流程要求放在 Manager 的 instructions 中，实际调用由模型产生。
工具执行后返回 Manager，符合 Lab 2 的 `A → B → A` 模式；没有通过 handoff 转移最终控制权。

## 保留与调整

- 保留四个专业 Agent 的职责、`WebSearchPlan` 和 `ReportData`。
- 按用户提供的平台适配 DeepSeek 官方 Responses API 和 Search API；OpenAI 模式仍可选。
- 保留长篇 Markdown 报告目标；新增来源 URL、限制与不确定性说明。
- 保留 Gradio 使用方式，简化上游外观，新增调用日志与产物下载。
- 上游 Python 并发搜索改为 Manager 逐次发起搜索，便于教学观察及明确步骤依赖。
- 邮件沿用当前完整项目的 SMTP 方式；新增默认预览模式，仍执行 Email Agent 和函数工具。
- 完整报告从 Writer 的结构化输出直接保存；Manager 的最终短回复不覆盖正文。
- Planner / Writer 格式错误允许 Manager 各重试一次；其他错误向上抛出。
  邮件同一次运行最多尝试发送一次，不参与格式重试。

## 验证记录（2026-10-25）

当前界面统一使用英文，独立的 Email settings 区域包含 Send report by email 开关与
Recipient email 输入框。收件地址保存在每次研究的 ResearchState，不读取 `.env` 的
EMAIL_TO；该旧字段已从示例及当前本地配置移除。发送开启时在 API 调用前验证单一收件地址，
预览不要求收件地址，发件登录凭据继续保存在本地环境。CLI 使用 `--recipient` 传入本次地址。
新增测试验证两次研究分别投递到各自传入的地址、忽略旧环境收件人、预览不投递以及无效地址早停。
Writer 的报告、摘要、后续问题与 Email Agent 的主题、正文统一使用英文。
以中文问题在线运行成功，证据位于 `outputs/20261025T091219Z_d771f8c6/`，
报告标题为 Retrieval Practice versus Repeated Reading: Effects on Long-Term Memory in University Students。
该轮只生成预览；真实发送用模拟 SMTP 验证收件路由，没有发送新的实际邮件。
浏览器已确认独立设置区域、空地址发送前拦截及英文界面；Gradio 本地化页脚已隐藏。

环境：Windows、Python 3.12.7、openai-agents 0.24.0、openai 3.37.0、Gradio 6.30.0。

| 检查 | 结果 |
| --- | --- |
| `.venv/Scripts/python.exe -m pytest -q --tb=short` | 52 passed（含逐次收件地址与发送开关） |
| `.venv/Scripts/ruff.exe check deep_research tests` | All checks passed |
| `.venv/Scripts/ruff.exe format --check deep_research tests` | 26 files already formatted |
| `.venv/Scripts/python.exe -m compileall -q deep_research tests` | 成功，无语法错误 |
| `uv pip check --python .venv/Scripts/python.exe` | 82 个安装包依赖兼容 |
| `.venv/Scripts/python.exe -m deep_research.app` | 本地页面成功启动，浏览器确认问题框、发送选项、编排记录与下载区域正常显示 |

测试覆盖真实 SDK 的嵌套工具执行、额外搜索分支、工具结果回传、报告原样保存、
邮件预览、不完整流程拒绝、缺少配置、空问题、四工具无 handoff、无报告时拒绝邮件、
邮件防重复与 SMTP 失败；新增 DeepSeek HTTP 路由、SDK 结构化输出、搜索函数工具、
搜索服务错误/空结果和 OpenAI 回退配置测试。
测试夹具阻止外部网络（Windows asyncio 回环连接除外），并显式替换 SDK 的原生共享 HTTP 传输。
开发首次运行 HTTP 路由测试时，原生传输曾绕过 Python socket 拦截，向 DeepSeek 发送一次
固定的无效测试 Key，收到 401；已修正隔离夹具，最终 52 项测试均使用模拟响应。

真实完整流程暴露出此前单接口检查遗漏的兼容问题：DeepSeek 默认思考模式拒绝
Search / Email Agent 的 `tool_choice="required"`，返回 HTTP 400，再由 SDK 包装为 UserError。
这两个 Agent 现发送 `reasoning.effort="none"`；Manager 和 Writer 的编排职责不变。
依据：[DeepSeek 思考模式](https://api-docs.deepseek.com/guides/thinking_mode/) 与
[Responses 参数](https://api-docs.deepseek.com/api/create-response/)。
真实报告生成还出现过一次结构化输出校验失败；Writer 增加明确 JSON 示例与转义要求，
输出上限设为 16000 tokens。无法从该已脱敏异常断定失败是截断还是格式问题。
随后用户的检索练习研究再次在 Writer 失败，证明仅添加格式提示不够。
现使用严格的 ResearchOutputSchema，允许去除完整 JSON 外层围栏；任何截断、
缺少必需字段或其他结构错误均不伪造报告。Planner / Writer 通过 `.as_tool()` 的
错误处理向 Manager 返回 `retry_required`，由 Manager 最多重试该阶段一次。
Writer 直接读取原问题与已保存证据，DeepSeek Writer 使用非思考模式，把输出预算留给报告。
新增真实 SDK 测试覆盖两个阶段的失败恢复、连续两次失败停止、证据下载、围栏处理及内容保真。
每次研究创建并逐步更新 `evidence.json`；失败后先写入 workflow，再把可下载文件传回界面。
格式诊断只记录阶段、类型和字符数，不记录原始模型响应或配置凭据。
2026-10-25 对用户原问题「检索练习与重复阅读对大学生长期记忆的影响」完整在线复测成功：
7 次搜索，Writer 返回 completed 且无 incomplete_details，结构校验通过，随后邮件预览完成。
证据位于 `outputs/20261025T085750Z_285bcc5b/`；报告、JSON 与邮件纯文本一致，未发送邮件。
这次在线运行未触发格式重试；重试及重试耗尽路径由模拟坏输出的真实 SDK 测试验证。
此前失败未保存原始响应，因此不能还原用户那次具体的坏 JSON，也不声称所有失败都是截断。
新增测试在真实 SDK 的 HTTP 序列化边界验证 Search / Email 的实际请求参数，
并验证 Gmail 空格规范化只影响 Gmail、UI 异常保留部分输出且不显示原始响应或凭据。
长报告的邮件步骤也出现过格式失败：Manager 现仅传简短的准备指令，Email Agent
在执行时从当前研究状态获取完整报告，避免把长正文重复序列化进 Manager 工具参数。
Email Agent 输出上限设为 32768 tokens，邮件纯文本仍严格保留原报告。
已对一份 18677 字符的真实中文报告单独重跑邮件预览成功，纯文本与报告一致；
这次单步骤恢复不把原先失败的 workflow.json 改写为成功。

这些结果证明代码接线与本地行为经过验证，不代表 LLM 一定遵循所有提示词。
后续在线完整验证（2026-10-25）：使用真实 DeepSeek 模型和搜索接口，Manager 自行完成
规划、6 次搜索（默认规划 5 次及 1 次补充）、写报告、邮件预览，并返回完成状态。
结果状态为 `preview_only_not_sent`，16682 字符报告及五个输出文件成功保存。
本地证据位于 `outputs/20261025T083017Z_0e721abd/`，输出不打包提交。
此前对真实中文长报告单独验证的邮件预览也成功；报告事实未逐条独立审计。
Gmail 587 和 465 直连超时；现有代理的 HTTP / SOCKS5 方式也未能建立 Gmail SMTP 会话。
用户因此选择 QQ 邮箱。已验证 `smtp.qq.com:465` 的 TLS 证书和 EHLO 250 响应，
新增隐式 TLS 支持、只登录不发送的 `python -m deep_research.check_email` 检查命令，
并测试 465/587 分支、证书校验、TLS 失败阻止登录和诊断不发送邮件。
2026-10-25 用户填写 QQ 配置后，运行 `.venv/Scripts/python.exe -m deep_research.check_email`，
退出码 0，TLS 连接与 SMTP 登录均成功；诊断不发送邮件，实际发送和收件仍待验证。
本次没有发送邮件，日志和文档不包含任何凭据或个人邮箱地址。
SMTP 说明见 `docs/EMAIL_SETUP.md`。

## 配置后建议演示

1. 启动 Gradio，输入一个具体、可搜索的研究问题。
2. 观察 Manager 的 `plan_research`、多次 `search_web`、`write_report`、`email_report` 调用。
3. 查看完整报告、来源链接、`report.json` 和 `workflow.json`。
4. 默认预览时说明邮件未发送；配置 SMTP 后可另行演示真实邮件。
5. DeepSeek 模式展示本地调用记录；只有配置 OpenAI 模式后，才可另行启用 OpenAI 云端 trace。

提交源码时包含 `deep_research/`、依赖文件、说明及 `LICENSE`；测试可用于复现验证。
不要提交 `.venv/`、`.env`、缓存或未检查的运行输出。
截图未说明必须提交 notebook 或运行截图，实际提交格式以课程平台的完整要求为准。
