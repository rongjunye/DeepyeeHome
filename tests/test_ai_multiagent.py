"""多智能体编排的接线测试。

这些测试**不需要真实 API Key**：
* LangGraph 部分用「假 provider」验证节点与连线确实跑通；
* CrewAI 部分只验证模块可导入、入口可调用（真正执行需真实模型，
  代价高且依赖网络，故不在此测试）。
"""

from __future__ import annotations

import pytest


def test_langgraph_workflow_wiring(monkeypatch):
    """用假 provider 驱动 LangGraph 工作流，验证 analyze→design→review 全链路。"""
    pytest.importorskip("langgraph")
    import app.ai.graph as graph_mod

    class FakeProvider:
        name = "fake"

        def available(self) -> bool:
            return True

        def generate(self, system: str, prompt: str) -> str:
            # review 节点：返回最终 JSON
            if "审阅" in prompt:
                return (
                    '{"summary":"最终方案结论","layout_plan":"布局建议",'
                    '"style_recommendation":"风格建议",'
                    '"color_palette":[{"name":"奶白","hex":"#F5EEE4"}]}'
                )
            # design 节点：返回草稿 JSON
            if "JSON 结构" in prompt:
                return '{"summary":"草稿"}'
            # analyze 节点：返回纯文本分析
            return "户型分析要点：南北通透、动静分区合理。"

    monkeypatch.setattr(graph_mod, "get_provider", lambda: FakeProvider())

    result = graph_mod.run_design_workflow("北欧", 100, "3室2厅", "standard", "想要书房")

    assert result is not None, "LangGraph 工作流应返回结构化结果"
    assert result["summary"] == "最终方案结论"
    assert result["color_palette"][0]["hex"] == "#F5EEE4"


def test_langgraph_degrades_without_provider():
    """无可用模型时，工作流应安全返回 None，而不是抛异常。"""
    pytest.importorskip("langgraph")
    from app.ai.graph import run_design_workflow
    from app.ai.llm_provider import NullProvider
    import app.ai.graph as graph_mod
    from unittest.mock import patch

    with patch.object(graph_mod, "get_provider", lambda: NullProvider()):
        # NullProvider.generate 返回 None -> 节点抛错 -> 工作流捕获后返回 None
        assert run_design_workflow("北欧", 100, "3室2厅", "standard", "") is None


def test_crewai_module_available():
    """CrewAI 已安装时，入口函数应可调用。"""
    pytest.importorskip("crewai")
    from app.ai.agents import run_design_crew

    assert callable(run_design_crew)
