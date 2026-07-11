"""编排器 — 根据任务类型路由到对应的 Agent 和模型。"""

from __future__ import annotations

import json
import logging
from typing import Any, Literal

from langchain_core.messages import HumanMessage, SystemMessage

from app.services.agent.models import get_llm_by_role
from app.services.agent.verify_agent import verify_resume, verify_changes

logger = logging.getLogger(__name__)

TaskType = Literal[
    "intent_recognition",
    "content_classification",
    "field_extraction",
    "resume_generation",
    "jd_analysis",
    "complex_rewrite",
    "verify_content",
    "verify_changes",
    "vision_extract",
    "vision_layout",
]


# 任务类型到模型角色的映射
TASK_MODEL_MAP = {
    # 轻量模型任务
    "intent_recognition": "lightweight",
    "content_classification": "lightweight",
    "field_extraction": "lightweight",

    # 主力模型任务
    "resume_generation": "main",
    "jd_analysis": "main",
    "complex_rewrite": "main",

    # 校验模型任务
    "verify_content": "verify",
    "verify_changes": "verify",

    # 视觉模型任务
    "vision_extract": "vision",
    "vision_layout": "vision",
}


def get_model_for_task(task_type: TaskType) -> str:
    """获取任务对应的模型角色。"""
    return TASK_MODEL_MAP.get(task_type, "main")


def recognize_intent(user_message: str) -> dict[str, Any]:
    """轻量模型：识别用户意图。"""
    llm = get_llm_by_role("lightweight", timeout=10)

    prompt = f"""判断用户意图，只返回 JSON：
用户消息：{user_message}

可选意图：
- generate: 生成新简历
- optimize: 优化简历内容
- diagnose: 诊断简历问题
- chat: 对话式修改
- translate: 翻译简历
- export: 导出简历
- unknown: 无法识别

返回：{{"intent": "xxx", "confidence": 0.9}}"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content

        # 提取 JSON
        if "{" in content:
            json_str = content[content.index("{"):content.rindex("}") + 1]
            result = json.loads(json_str)
            return {
                "intent": result.get("intent", "unknown"),
                "confidence": float(result.get("confidence", 0.5)),
            }
        return {"intent": "unknown", "confidence": 0.3}
    except Exception as e:
        logger.warning("意图识别失败: %s", e)
        return {"intent": "unknown", "confidence": 0.0, "error": str(e)}


def classify_content(text: str) -> dict[str, Any]:
    """轻量模型：分类内容类型。"""
    llm = get_llm_by_role("lightweight", timeout=10)

    prompt = f"""对以下内容分类，只返回 JSON：
内容：{text[:500]}

分类选项：
- work_experience: 工作经历
- project_experience: 项目经历
- education: 教育经历
- skills: 技能
- personal_info: 个人信息
- other: 其他

返回：{{"category": "xxx", "confidence": 0.9}}"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content

        if "{" in content:
            json_str = content[content.index("{"):content.rindex("}") + 1]
            result = json.loads(json_str)
            return {
                "category": result.get("category", "other"),
                "confidence": float(result.get("confidence", 0.5)),
            }
        return {"category": "other", "confidence": 0.3}
    except Exception as e:
        logger.warning("内容分类失败: %s", e)
        return {"category": "other", "confidence": 0.0, "error": str(e)}


def extract_fields(text: str) -> dict[str, Any]:
    """轻量模型：提取结构化字段。"""
    llm = get_llm_by_role("lightweight", timeout=15)

    prompt = f"""从以下文本提取结构化字段，只返回 JSON：
文本：{text}

提取字段：
- company: 公司名称
- position: 职位
- period: 时间段
- description: 描述
- skills: 技能列表
- achievements: 成就列表

返回：{{"fields": {{...}}, "confidence": 0.9}}"""

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content

        if "{" in content:
            json_str = content[content.index("{"):content.rindex("}") + 1]
            result = json.loads(json_str)
            return {
                "fields": result.get("fields", {}),
                "confidence": float(result.get("confidence", 0.5)),
            }
        return {"fields": {}, "confidence": 0.3}
    except Exception as e:
        logger.warning("字段提取失败: %s", e)
        return {"fields": {}, "confidence": 0.0, "error": str(e)}


def route_and_execute(task_type: TaskType, **kwargs) -> dict[str, Any]:
    """根据任务类型路由到对应的模型执行。"""
    role = get_model_for_task(task_type)

    if task_type == "intent_recognition":
        return recognize_intent(kwargs.get("message", ""))
    elif task_type == "content_classification":
        return classify_content(kwargs.get("text", ""))
    elif task_type == "field_extraction":
        return extract_fields(kwargs.get("text", ""))
    elif task_type == "verify_content":
        return verify_resume(kwargs.get("resume_data", {}))
    elif task_type == "verify_changes":
        return verify_changes(
            kwargs.get("old_resume", {}),
            kwargs.get("new_resume", {}),
        )
    else:
        # 其他任务返回角色信息，由调用方处理
        return {"role": role, "task_type": task_type}
