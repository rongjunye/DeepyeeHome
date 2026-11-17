"""基于 CrewAI 的多智能体协作模块（可选组件）。

模拟一个设计小组：
* 空间规划师  —— 负责动线与分区
* 室内设计师  —— 负责风格、材质与配色
* 造价顾问    —— 负责预算与选材性价比

若运行环境未安装 ``crewai``，``run_design_crew`` 返回 ``None``，
由上层自动降级。
"""

from __future__ import annotations

from typing import Any

from app.ai.llm_provider import try_parse_json
from app.ai.prompts import OUTPUT_SCHEMA_HINT, build_user_prompt


def run_design_crew(
    style: str,
    area: float | None,
    rooms: str | None,
    budget_level: str,
    requirements: str = "",
) -> dict[str, Any] | None:
    """执行 CrewAI 多智能体协作；不可用或失败时返回 ``None``。"""
    try:
        from crewai import Agent, Crew, Process, Task  # type: ignore
    except Exception:
        return None

    try:
        brief = build_user_prompt(style, area, rooms, budget_level, requirements)

        planner = Agent(
            role="空间规划师",
            goal="根据户型给出合理的动线组织与功能分区方案",
            backstory="你精通住宅空间规划，善于在有限面积内提升居住体验。",
            verbose=False,
            allow_delegation=False,
        )
        designer = Agent(
            role="室内设计师",
            goal="确定风格定位、材质搭配与配色方案",
            backstory="你擅长把抽象的风格概念落地为具体的材质与色彩组合。",
            verbose=False,
            allow_delegation=False,
        )
        estimator = Agent(
            role="造价顾问",
            goal="在预算约束下给出可选的材料与工艺建议",
            backstory="你熟悉建材市场行情，擅长做性价比分析与成本控制。",
            verbose=False,
            allow_delegation=False,
        )

        task_plan = Task(
            description=f"基于以下需求完成空间规划：\n{brief}",
            expected_output="空间布局与动线建议，分点列出。",
            agent=planner,
        )
        task_design = Task(
            description="结合空间规划结果，给出风格落地要点与配色方案。",
            expected_output="风格要点与配色说明。",
            agent=designer,
        )
        task_estimate = Task(
            description="综合前三项成果，输出完整设计方案，并严格按要求返回 JSON。\n" + OUTPUT_SCHEMA_HINT,
            expected_output="符合指定 JSON 结构的最终方案。",
            agent=estimator,
        )

        crew = Crew(
            agents=[planner, designer, estimator],
            tasks=[task_plan, task_design, task_estimate],
            process=Process.sequential,
            verbose=False,
        )
        result = crew.kickoff()
        return try_parse_json(str(result))
    except Exception:  # noqa: BLE001 - 智能体任何异常都降级
        return None
