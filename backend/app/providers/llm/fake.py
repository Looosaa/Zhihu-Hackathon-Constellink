import json
import re
from typing import TypeVar

from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


class FakeLLM:
    """Deterministic offline adapter for development, tests, and demo fallback."""

    @property
    def model_name(self) -> str:
        return "fake-zhijing-v1"

    async def generate_structured(
        self,
        *,
        task_name: str,
        system_prompt: str,
        user_prompt: str,
        response_model: type[ModelT],
        timeout_seconds: float | None = None,
        max_tokens: int | None = None,
    ) -> ModelT:
        payload = self._payload(task_name, user_prompt)
        return response_model.model_validate(payload)

    def _payload(self, task_name: str, prompt: str) -> dict:
        keys = sorted(
            set(re.findall(r"\bS(?:[1-9]|1[0-9]|20)\b", prompt)),
            key=lambda item: int(item[1:]),
        )
        keys = keys or ["S1", "S2", "S3"]
        if task_name in {"extract_viewpoint", "extract_viewpoints_batch"}:

            def viewpoint(source_key: str) -> dict:
                return {
                    "source_key": source_key,
                    "relevance_score": 0.9,
                    "position_summary": "先形成实践闭环，再按遇到的问题补充理论。",
                    "claims": [
                        {
                            "text": "实践和理论应交替进行",
                            "evidence": "来源强调通过小项目获得反馈，并按需补足知识。",
                            "confidence": 0.85,
                        }
                    ],
                    "concepts": [
                        {"name": "项目实践", "definition": "用小任务验证所学知识。"}
                    ],
                    "suitable_for": ["零基础学习者", "以项目为目标的人"],
                    "limitations": ["研究型目标仍需要更系统的数学训练"],
                }

            if task_name == "extract_viewpoints_batch":
                return {"items": [viewpoint(key) for key in keys]}
            return viewpoint(keys[0])
        if task_name in {"synthesize", "analyze_sources"}:
            return {
                "overview": "多数观点认可实践与基础并行，但在数学学习的先后顺序上存在分歧。",
                "consensus": [
                    {
                        "id": "consensus_1",
                        "title": "尽早建立实践闭环",
                        "detail": "通过小项目验证理解，再根据问题补充理论。",
                        "source_keys": keys[: min(3, len(keys))],
                    },
                    {
                        "id": "consensus_2",
                        "title": "掌握基础编程能力",
                        "detail": "Python 与数据处理能力是后续实践的共同前置条件。",
                        "source_keys": keys[:2],
                    },
                    {
                        "id": "consensus_3",
                        "title": "需要持续自测",
                        "detail": "能解释、比较并完成任务比只阅读更能证明掌握。",
                        "source_keys": keys[-2:],
                    },
                ],
                "disagreements": [
                    {
                        "id": "disagreement_1",
                        "question": "是否应该先系统学习数学？",
                        "side_a": {
                            "title": "先补数学",
                            "reason": "系统基础有助于理解模型原理和边界。",
                            "suitable_for": ["算法研究", "时间充足"],
                            "source_keys": [keys[0]],
                        },
                        "side_b": {
                            "title": "先做项目",
                            "reason": "快速反馈可以降低入门门槛。",
                            "suitable_for": ["应用开发", "时间有限"],
                            "source_keys": [keys[1] if len(keys) > 1 else keys[0]],
                        },
                        "how_to_choose": "以完成应用为目标时先实践；以算法研究为目标时先补数学。",
                    }
                ],
                "concepts": [
                    {"id": "python", "label": "Python 基础", "category": "prerequisite", "description": "能阅读和修改基础代码。", "source_keys": keys[:2]},
                    {"id": "linear_algebra", "label": "线性代数", "category": "prerequisite", "description": "理解向量、矩阵与常见运算。", "source_keys": keys[:2]},
                    {"id": "probability", "label": "概率统计", "category": "prerequisite", "description": "理解不确定性与模型评估。", "source_keys": keys[:2]},
                    {"id": "ml_workflow", "label": "机器学习流程", "category": "core", "description": "数据、训练、评估和迭代的完整流程。", "source_keys": keys[:3]},
                    {"id": "data_preparation", "label": "数据准备", "category": "core", "description": "清洗并划分可用的数据。", "source_keys": keys[:2]},
                    {"id": "model_training", "label": "模型训练", "category": "core", "description": "用训练数据优化模型参数。", "source_keys": keys[:2]},
                    {"id": "evaluation", "label": "模型评估", "category": "core", "description": "用独立数据判断泛化能力。", "source_keys": keys[-2:]},
                    {"id": "mini_project", "label": "小型项目", "category": "practice", "description": "完成一个端到端练习。", "source_keys": keys[-2:]},
                ],
                "edges": [
                    {"source": "python", "target": "data_preparation", "type": "PREREQUISITE_OF", "label": "前置知识"},
                    {"source": "linear_algebra", "target": "model_training", "type": "PREREQUISITE_OF", "label": "帮助理解"},
                    {"source": "probability", "target": "evaluation", "type": "PREREQUISITE_OF", "label": "帮助理解"},
                    {"source": "data_preparation", "target": "model_training", "type": "LEARN_AFTER", "label": "学习顺序"},
                    {"source": "model_training", "target": "evaluation", "type": "LEARN_AFTER", "label": "学习顺序"},
                    {"source": "ml_workflow", "target": "mini_project", "type": "PREREQUISITE_OF", "label": "用于实践"},
                    {"source": "evaluation", "target": "mini_project", "type": "PART_OF", "label": "项目环节"},
                ],
                "warnings": ["当前为离线演示模型输出，请在接入真实模型后重新验证。"],
            }
        if task_name == "create_plan":
            concepts = ["python", "ml_workflow", "data_preparation", "model_training", "evaluation", "mini_project", "probability"]
            return {
                "strategy": "先建立完整流程认识，再完成小项目并按问题补充理论。",
                "days": [
                    {
                        "day": day,
                        "title": ["准备环境", "认识流程", "准备数据", "训练模型", "评估模型", "完成项目", "复盘输出"][day - 1],
                        "goal": f"完成第 {day} 天的可验证学习目标",
                        "concept_ids": [concepts[day - 1]],
                        "activities": ["阅读对应观点", "完成一个小练习"],
                        "source_keys": [keys[(day - 1) % len(keys)]],
                        "output": "一份简短笔记或可运行结果",
                        "self_check": "我能否不用原文解释今天的核心概念？",
                        "estimated_minutes": 15,
                    }
                    for day in range(1, 8)
                ],
            }
        if task_name == "create_quiz":
            return {
                "concept_id": "evaluation",
                "question": "为什么训练集和测试集需要分开？请用自己的话说明。",
                "reference_answer": "训练集用于学习参数，测试集用于评估模型面对未见数据时的泛化能力；混用会导致评估偏高。",
                "rubric": [
                    {"criterion": "区分训练和评估用途", "points": 40},
                    {"criterion": "提到未见数据或泛化", "points": 40},
                    {"criterion": "表达清晰", "points": 20},
                ],
                "source_keys": keys[:2],
            }
        if task_name == "grade_quiz":
            return {
                "score": 82,
                "strengths": ["正确区分了训练与测试的作用", "表达清晰"],
                "improvements": ["可以进一步说明数据泄漏会让评估结果虚高"],
                "next_step": "尝试解释验证集与测试集的区别。",
            }
        raise ValueError(f"Unsupported fake task: {task_name}")
