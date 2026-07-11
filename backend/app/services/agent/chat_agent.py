"""对话式 Chat Agent — 带工具调用，能直接读写简历。"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langgraph.prebuilt import create_react_agent

from app.services.agent.models import get_llm_by_role
from app.services.agent.prompts import CHAT_SYSTEM_PROMPT
from app.services.agent.tools import (
    append_resume_item,
    analyze_job_description,
    create_version_snapshot,
    get_resume_summary,
    match_resume_jd,
    read_resume,
    update_resume_section,
    validate_resume,
)

logger = logging.getLogger(__name__)

# Agent 可用的工具列表
AGENT_TOOLS = [
    read_resume,
    update_resume_section,
    append_resume_item,
    analyze_job_description,
    match_resume_jd,
    validate_resume,
    create_version_snapshot,
    get_resume_summary,
]


def build_chat_agent():
    """构建带工具调用的 Chat Agent。"""
    llm = get_llm_by_role("main")
    return create_react_agent(
        llm,
        AGENT_TOOLS,
        prompt=CHAT_SYSTEM_PROMPT,
    )


def run_chat_agent(
    user_message: str,
    resume_id: int | None = None,
    history: list[dict[str, str]] | None = None,
    *,
    max_iterations: int = 10,
) -> dict[str, Any]:
    """运行 Chat Agent 并返回结果。

    Args:
        user_message: 用户消息
        resume_id: 当前简历 ID（可选）
        history: 对话历史（可选）
        max_iterations: 最大工具调用轮数

    Returns:
        {
            "reply": "AI 回复文本",
            "tool_calls": [{"tool": "xxx", "args": {...}, "result": "..."}],
            "resume_modified": bool,
        }
    """
    agent = build_chat_agent()

    # 构建消息列表
    messages = []

    # 添加简历上下文
    if resume_id:
        messages.append(SystemMessage(
            content=f"用户当前正在编辑简历 ID: {resume_id}。如果需要读取或修改简历，请使用这个 ID。"
        ))

    # 添加历史对话
    if history:
        for msg in history[-10:]:  # 最近 10 轮
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

    # 添加当前用户消息
    messages.append(HumanMessage(content=user_message))

    # 运行 Agent
    tool_calls_log = []
    resume_modified = False

    try:
        result = agent.invoke({"messages": messages})

        # 提取工具调用记录
        for msg in result.get("messages", []):
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    tool_calls_log.append({
                        "tool": tc.get("name", ""),
                        "args": tc.get("args", {}),
                        "result": "",
                    })
            if isinstance(msg, ToolMessage):
                # 关联结果到最后一个工具调用
                for tc in reversed(tool_calls_log):
                    if not tc["result"]:
                        tc["result"] = msg.content[:500]
                        break
                # 检查是否修改了简历
                if any(kw in msg.content for kw in ["成功更新", "成功向", "成功创建版本"]):
                    resume_modified = True

        # 提取最终回复
        last_message = result["messages"][-1]
        reply = last_message.content if hasattr(last_message, "content") else str(last_message)

        return {
            "reply": reply,
            "tool_calls": tool_calls_log,
            "resume_modified": resume_modified,
        }

    except Exception as e:
        logger.error("Chat Agent 执行失败: %s", e, exc_info=True)
        return {
            "reply": f"抱歉，处理过程中出现了问题：{e}",
            "tool_calls": tool_calls_log,
            "resume_modified": False,
        }
