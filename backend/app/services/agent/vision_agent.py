"""视觉模型 — 识别截图、扫描简历和排版问题。"""

from __future__ import annotations

import base64
import json
import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.services.agent.models import get_llm_by_role

logger = logging.getLogger(__name__)

VISION_SYSTEM_PROMPT = """你是简历图像识别专家。你的职责是：

1. **文字识别**：从截图或扫描件中提取简历内容
2. **结构识别**：识别简历的模块划分和排版
3. **排版分析**：分析简历的视觉效果和可读性

识别原则：
- 尽可能准确地提取文字内容
- 保持原始的模块结构
- 识别可能的排版问题
- 返回 JSON 格式的结果

返回格式（文字提取）：
{
    "sections": [
        {
            "type": "basics|summary|work|education|projects|skills|awards",
            "content": {},
            "confidence": 0-100
        }
    ],
    "raw_text": "原始文本",
    "issues": ["排版问题"]
}

返回格式（排版分析）：
{
    "layout_score": 0-100,
    "readability": "good|fair|poor",
    "issues": [
        {
            "type": "font|spacing|alignment|contrast|length",
            "description": "问题描述",
            "location": "问题位置",
            "suggestion": "改进建议"
        }
    ],
    "summary": "整体评估"
}"""


def extract_resume_from_image(image_base64: str, image_type: str = "image/png") -> dict[str, Any]:
    """从图片中提取简历内容。

    Args:
        image_base64: 图片的 base64 编码
        image_type: 图片类型（image/png, image/jpeg 等）
    """
    llm = get_llm_by_role("vision", timeout=60)

    messages = [
        SystemMessage(content=VISION_SYSTEM_PROMPT),
        HumanMessage(content=[
            {
                "type": "text",
                "text": "请识别这张简历图片中的内容，提取出各个模块的信息。返回 JSON 格式。"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image_type};base64,{image_base64}"
                }
            }
        ]),
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
                "sections": result.get("sections", []),
                "raw_text": result.get("raw_text", ""),
                "issues": result.get("issues", []),
                "success": True,
            }
        except json.JSONDecodeError:
            return {
                "sections": [],
                "raw_text": content[:2000],
                "issues": [],
                "success": True,
                "note": "JSON 解析失败，返回原始文本",
            }

    except Exception as e:
        logger.error("视觉模型调用失败: %s", e, exc_info=True)
        return {
            "sections": [],
            "raw_text": "",
            "issues": [f"识别失败: {str(e)}"],
            "success": False,
            "error": str(e),
        }


def analyze_resume_layout(image_base64: str, image_type: str = "image/png") -> dict[str, Any]:
    """分析简历排版。

    Args:
        image_base64: 图片的 base64 编码
        image_type: 图片类型
    """
    llm = get_llm_by_role("vision", timeout=60)

    messages = [
        SystemMessage(content=VISION_SYSTEM_PROMPT),
        HumanMessage(content=[
            {
                "type": "text",
                "text": "请分析这张简历的排版质量，包括字体、间距、对齐、对比度等方面。返回 JSON 格式。"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{image_type};base64,{image_base64}"
                }
            }
        ]),
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
                "layout_score": result.get("layout_score", 70),
                "readability": result.get("readability", "fair"),
                "issues": result.get("issues", []),
                "summary": result.get("summary", "分析完成"),
                "success": True,
            }
        except json.JSONDecodeError:
            return {
                "layout_score": 70,
                "readability": "fair",
                "issues": [],
                "summary": content[:500],
                "success": True,
            }

    except Exception as e:
        logger.error("排版分析失败: %s", e, exc_info=True)
        return {
            "layout_score": 0,
            "readability": "unknown",
            "issues": [f"分析失败: {str(e)}"],
            "summary": f"分析出错: {str(e)}",
            "success": False,
            "error": str(e),
        }


def image_to_base64(image_bytes: bytes) -> str:
    """将图片字节转换为 base64 编码。"""
    return base64.b64encode(image_bytes).decode("utf-8")
