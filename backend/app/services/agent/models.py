"""模型路由 — 按角色选择不同的 LLM。"""

from __future__ import annotations

import logging
from typing import Literal

from langchain_openai import ChatOpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.exceptions import AppException
from app.models.ai_config import AiModelConfig

logger = logging.getLogger(__name__)

ModelRole = Literal["lightweight", "main", "verify", "vision"]

# 角色用途说明
ROLE_DESCRIPTIONS = {
    "lightweight": "轻量模型 — 意图识别、内容分类、简单字段抽取",
    "main": "主力模型 — 简历生成、JD 分析、复杂改写",
    "verify": "校验模型 — 检查虚构内容、数字变化和结构缺失",
    "vision": "视觉模型 — 识别截图、扫描简历和排版问题",
}


def _config_to_llm(config: AiModelConfig, timeout: int | None = None) -> ChatOpenAI:
    return ChatOpenAI(
        api_key=config.api_key,
        base_url=config.base_url,
        model=config.model,
        temperature=float(config.temperature or 0.7),
        timeout=timeout or int(config.timeout or 60),
        max_tokens=int(config.max_tokens or 8192),
    )


def _fallback_llm(timeout: int | None = None) -> ChatOpenAI:
    return ChatOpenAI(
        api_key=settings.ai_api_key,
        base_url=settings.ai_base_url,
        model=settings.ai_model,
        temperature=float(settings.ai_temperature),
        timeout=timeout or int(settings.ai_timeout),
        max_tokens=int(settings.ai_max_tokens),
    )


def get_llm_by_role(role: ModelRole = "main", timeout: int | None = None) -> ChatOpenAI:
    """按角色获取 LLM 实例。

    优先从数据库查找对应 role 的模型配置，找不到则回退到环境变量配置。
    """
    db = SessionLocal()
    try:
        config = db.scalar(
            select(AiModelConfig)
            .where(AiModelConfig.role == role, AiModelConfig.is_active == True)  # noqa: E712
            .order_by(AiModelConfig.sort_order.asc(), AiModelConfig.id.desc())
            .limit(1)
        )
        if config:
            return _config_to_llm(config, timeout)

        # 回退到主模型
        if role != "main":
            main_config = db.scalar(
                select(AiModelConfig)
                .where(AiModelConfig.is_active == True)  # noqa: E712
                .order_by(AiModelConfig.sort_order.asc(), AiModelConfig.id.desc())
                .limit(1)
            )
            if main_config:
                logger.warning("未找到 role=%s 的模型，回退到主模型: %s", role, main_config.name)
                return _config_to_llm(main_config, timeout)

        # 最终回退到环境变量
        logger.warning("未找到任何模型配置，使用环境变量配置")
        return _fallback_llm(timeout)
    finally:
        db.close()


def get_all_model_roles() -> dict[str, dict]:
    """获取所有模型角色配置状态。"""
    db = SessionLocal()
    try:
        result = {}
        for role, desc in ROLE_DESCRIPTIONS.items():
            config = db.scalar(
                select(AiModelConfig)
                .where(AiModelConfig.role == role, AiModelConfig.is_active == True)  # noqa: E712
                .limit(1)
            )
            result[role] = {
                "description": desc,
                "configured": config is not None,
                "model_name": config.name if config else None,
                "model": config.model if config else None,
            }
        return result
    finally:
        db.close()
