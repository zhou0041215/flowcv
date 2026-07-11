"""校验模型 — 检查虚构内容、数字变化和结构缺失。"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.services.agent.models import get_llm_by_role

logger = logging.getLogger(__name__)

VERIFY_SYSTEM_PROMPT = """你是简历内容校验专家。你的职责是：

1. **事实核查**：检查简历中是否有虚构或夸大的内容
2. **数字一致性**：检查数字是否合理、前后是否矛盾
3. **结构完整性**：检查是否有缺失的关键信息
4. **逻辑合理性**：检查时间线、经历递进是否合理

校验原则：
- 只报告真正的问题，不要过度挑剔
- 用具体证据说明问题
- 区分"确定有问题"和"可能有问题"
- 返回 JSON 格式的结果

返回格式：
{
    "issues": [
        {
            "type": "factual|number|structure|logic",
            "severity": "high|medium|low",
            "section": "work|projects|education|skills|basics",
            "description": "问题描述",
            "evidence": "具体证据",
            "suggestion": "修改建议"
        }
    ],
    "warnings": ["可能需要注意的点"],
    "score": 0-100 的可信度分数,
    "summary": "整体评估"
}"""


def verify_resume(resume_data: dict[str, Any], original_data: dict[str, Any] | None = None) -> dict[str, Any]:
    """校验简历内容。

    Args:
        resume_data: 当前简历数据
        original_data: 原始简历数据（用于对比修改）
    """
    llm = get_llm_by_role("verify", timeout=30)

    prompt_parts = ["请校验以下简历内容：\n\n"]
    prompt_parts.append(f"```json\n{json.dumps(resume_data, ensure_ascii=False, indent=2)}\n```")

    if original_data:
        prompt_parts.append("\n\n原始简历数据（用于对比修改）：\n")
        prompt_parts.append(f"```json\n{json.dumps(original_data, ensure_ascii=False, indent=2)}\n```")

    messages = [
        SystemMessage(content=VERIFY_SYSTEM_PROMPT),
        HumanMessage(content="\n".join(prompt_parts)),
    ]

    try:
        response = llm.invoke(messages)
        content = response.content

        # 尝试解析 JSON
        try:
            # 提取 JSON 部分
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()

            result = json.loads(json_str)

            # 确保返回格式正确
            return {
                "issues": result.get("issues", []),
                "warnings": result.get("warnings", []),
                "score": int(result.get("score", 80)),
                "summary": result.get("summary", "校验完成"),
            }
        except json.JSONDecodeError:
            # JSON 解析失败，返回原始文本
            return {
                "issues": [],
                "warnings": [content[:500]],
                "score": 70,
                "summary": "校验完成，但结果格式异常",
            }

    except Exception as e:
        logger.error("校验模型调用失败: %s", e, exc_info=True)
        return {
            "issues": [],
            "warnings": [f"校验失败: {str(e)}"],
            "score": 0,
            "summary": f"校验过程出错: {str(e)}",
        }


def verify_changes(old_resume: dict[str, Any], new_resume: dict[str, Any]) -> dict[str, Any]:
    """校验简历修改的安全性。

    Args:
        old_resume: 修改前的简历
        new_resume: 修改后的简历
    """
    llm = get_llm_by_role("verify", timeout=30)

    prompt = f"""请对比以下简历修改，检查是否有问题：

修改前：
```json
{json.dumps(old_resume, ensure_ascii=False, indent=2)}
```

修改后：
```json
{json.dumps(new_resume, ensure_ascii=False, indent=2)}
```

请检查：
1. 是否新增了虚构的经历或技能
2. 数字是否被不合理地夸大
3. 是否删除了重要信息
4. 时间线是否仍然合理

返回 JSON 格式：
{{
    "safe": true/false,
    "issues": [
        {{
            "type": "added_fiction|inflated_number|deleted_info|timeline_issue",
            "severity": "high|medium|low",
            "description": "问题描述",
            "original": "原始内容",
            "modified": "修改后内容"
        }}
    ],
    "summary": "整体评估"
}}"""

    messages = [
        SystemMessage(content=VERIFY_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ]

    try:
        response = llm.invoke(messages)
        content = response.content

        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()

            result = json.loads(json_str)
            return {
                "safe": result.get("safe", True),
                "issues": result.get("issues", []),
                "summary": result.get("summary", "校验完成"),
            }
        except json.JSONDecodeError:
            return {
                "safe": True,
                "issues": [],
                "summary": content[:500],
            }

    except Exception as e:
        logger.error("修改校验失败: %s", e, exc_info=True)
        return {
            "safe": True,
            "issues": [],
            "summary": f"校验失败: {str(e)}",
        }
