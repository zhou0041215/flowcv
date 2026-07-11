"""知识库存储 — 支持 Redis 动态扩展知识库。"""

from __future__ import annotations

import json
import logging
from typing import Any

from redis.exceptions import RedisError

from app.core.config import settings
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

KNOWLEDGE_PREFIX = f"{settings.redis_key_prefix}:knowledge"


def _key(category: str) -> str:
    return f"{KNOWLEDGE_PREFIX}:{category}"


def get_knowledge(category: str) -> dict[str, Any]:
    """获取某个分类的知识库数据。"""
    try:
        data = redis_client.get(_key(category))
        return json.loads(data) if data else {}
    except (RedisError, json.JSONDecodeError):
        return {}


def set_knowledge(category: str, data: dict[str, Any]) -> bool:
    """设置某个分类的知识库数据。"""
    try:
        redis_client.set(_key(category), json.dumps(data, ensure_ascii=False))
        return True
    except RedisError:
        logger.warning("Failed to save knowledge: %s", category)
        return False


def add_item(category: str, key: str, value: Any) -> bool:
    """向某个分类添加一条知识。"""
    data = get_knowledge(category)
    data[key] = value
    return set_knowledge(category, data)


def remove_item(category: str, key: str) -> bool:
    """从某个分类删除一条知识。"""
    data = get_knowledge(category)
    if key in data:
        del data[key]
        return set_knowledge(category, data)
    return False


def list_categories() -> list[str]:
    """列出所有知识库分类。"""
    try:
        keys = redis_client.keys(f"{KNOWLEDGE_PREFIX}:*")
        return [key.decode().split(":")[-1] for key in keys]
    except RedisError:
        return []


def search_knowledge(category: str, query: str) -> list[dict[str, Any]]:
    """在某个分类中模糊搜索。"""
    data = get_knowledge(category)
    results = []
    query_lower = query.lower()

    for key, value in data.items():
        # 搜索 key
        if query_lower in key.lower():
            results.append({"key": key, "value": value, "match_type": "key"})
            continue

        # 搜索 value 中的文本
        if isinstance(value, dict):
            for v in value.values():
                if isinstance(v, str) and query_lower in v.lower():
                    results.append({"key": key, "value": value, "match_type": "value"})
                    break
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, str) and query_lower in item.lower():
                            results.append({"key": key, "value": value, "match_type": "list_item"})
                            break

    return results


def init_default_knowledge() -> None:
    """初始化默认知识库数据到 Redis（如果不存在）。"""
    from app.services.agent.knowledge_base import COMPANY_DB, POSITION_DB, SKILL_DB

    # 只在 Redis 为空时初始化
    if list_categories():
        return

    set_knowledge("companies", COMPANY_DB)
    set_knowledge("positions", POSITION_DB)
    set_knowledge("skills", SKILL_DB)
    logger.info("Default knowledge base initialized in Redis")
