HEADER_HTML = """
<div class="hero">
  <div class="hero-kicker">LANGGRAPH · TOOL ORCHESTRATION</div>
  <h1>Deep Research</h1>
  <p>由管理器调度规划、网页检索、报告撰写与邮件工具，生成带来源的深度研究报告。</p>
</div>
"""

EXAMPLES = [
    ["比较 LangGraph 与 CrewAI 在生产级多智能体系统中的取舍"],
    ["What are the strongest current arguments for and against small modular reactors?"],
    ["分析近两年 AI Agent 评估方法的发展与主要争议"],
]

CSS = """
body { background: #f5f3ee; }
.gradio-container { max-width: 1060px !important; margin: 0 auto !important; }
.hero { padding: 48px 8px 28px; }
.hero-kicker { color: #b45309; font: 700 12px/1.4 ui-monospace, monospace; letter-spacing: .15em; }
.hero h1 { margin: 8px 0 6px; color: #172554; font-size: clamp(38px, 6vw, 64px); letter-spacing: -.045em; }
.hero p { max-width: 720px; margin: 0; color: #475569; font-size: 17px; }
#query textarea { font-size: 16px; }
#run { min-height: 54px; background: #172554; border-color: #172554; }
#report { background: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px 28px; }
"""

