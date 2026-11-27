from deep_research.schemas import ReportData, WebSearchPlan


def test_web_search_plan_accepts_deepseek_purpose_alias() -> None:
    plan = WebSearchPlan.model_validate(
        {
            "type": "json_object",
            "searches": [
                {
                    "purpose": "definitions",
                    "query": "small modular reactor definition and technology overview",
                }
            ],
        }
    )

    assert plan.searches[0].reason == "definitions"
    assert plan.model_dump() == {
        "searches": [
            {
                "query": "small modular reactor definition and technology overview",
                "reason": "definitions",
            }
        ]
    }


def test_report_data_accepts_deepseek_single_report_field() -> None:
    report = ReportData.model_validate(
        {
            "type": "json_object",
            "report": (
                "# AI Agent 评估方法\n\n"
                "## 执行摘要\n\n"
                "2024–2025 年间，评估从静态打分转向动态环境和过程追踪。\n\n"
                "## 正文\n\n完整报告内容。"
            ),
        }
    )

    assert report.title == "AI Agent 评估方法"
    assert report.short_summary.startswith("2024–2025 年间")
    assert report.markdown_report.startswith("# AI Agent 评估方法")
    assert report.follow_up_questions == []
