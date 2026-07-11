"""规则引擎 — 基于知识库的简历内容生成，不调用 AI。"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from app.services.agent.knowledge_base import (
    ACHIEVEMENT_TEMPLATES,
    ACTION_VERBS,
    COMPANY_DB,
    INDUSTRY_TERMS,
    POSITION_DB,
    PROJECT_TEMPLATES,
    SKILL_DB,
)


def _fuzzy_match(text: str, candidates: list[str], threshold: float = 0.6) -> str | None:
    """模糊匹配，返回最相似的候选值。"""
    text_lower = text.lower().strip()
    best_match = None
    best_score = 0

    for candidate in candidates:
        candidate_lower = candidate.lower()

        # 完全包含
        if candidate_lower in text_lower or text_lower in candidate_lower:
            return candidate

        # SequenceMatcher 模糊匹配
        score = SequenceMatcher(None, text_lower, candidate_lower).ratio()
        if score > best_score:
            best_score = score
            best_match = candidate

    return best_match if best_score >= threshold else None


def match_company(text: str) -> dict[str, Any] | None:
    """从文本中模糊匹配公司信息。"""
    # 先尝试精确匹配
    for name, info in COMPANY_DB.items():
        if name in text:
            return {"name": name, **info}

    # 模糊匹配
    matched = _fuzzy_match(text, list(COMPANY_DB.keys()), threshold=0.5)
    if matched:
        return {"name": matched, **COMPANY_DB[matched]}
    return None


def match_position(text: str) -> dict[str, Any] | None:
    """从文本中模糊匹配职位信息。"""
    # 先尝试精确匹配
    for title, info in POSITION_DB.items():
        if title in text or any(kw in text for kw in info.get("keywords", [])):
            return {"title": title, **info}

    # 模糊匹配职位名称
    matched = _fuzzy_match(text, list(POSITION_DB.keys()), threshold=0.5)
    if matched:
        return {"title": matched, **POSITION_DB[matched]}
    return None


def extract_skills(text: str) -> list[str]:
    """从文本中模糊提取技能关键词。"""
    found = []
    text_lower = text.lower()

    for skill, info in SKILL_DB.items():
        skill_lower = skill.lower()

        # 精确匹配
        if skill_lower in text_lower:
            found.append(skill)
            continue

        # 模糊匹配（针对缩写和变体）
        score = SequenceMatcher(None, skill_lower, text_lower).ratio()
        if score > 0.7:
            found.append(skill)

    # 额外：匹配常见变体
    skill_aliases = {
        "vue": "Vue", "react": "React", "node": "Node.js",
        "java": "Java", "python": "Python", "golang": "Go",
        "mysql": "MySQL", "redis": "Redis", "docker": "Docker",
        "k8s": "Kubernetes", "spring": "Spring Boot",
    }
    for alias, skill in skill_aliases.items():
        if alias in text_lower and skill not in found:
            found.append(skill)

    return found


def match_project_type(text: str) -> str | None:
    """从文本中模糊匹配项目类型。"""
    keywords_map = {
        "支付系统": ["支付", "交易", "订单", "结算", "收款", "付款", "转账"],
        "用户系统": ["用户", "注册", "登录", "画像", "推荐", "认证", "权限"],
        "电商系统": ["电商", "商品", "购物车", "库存", "促销", "商城", "零售"],
        "数据平台": ["数据", "报表", "分析", "指标", "看板", "统计", "BI"],
        "管理系统": ["后台", "管理", "权限", "配置", "审核", "CMS", "ERP"],
    }

    # 精确匹配
    for project_type, keywords in keywords_map.items():
        if any(kw in text for kw in keywords):
            return project_type

    # 模糊匹配
    all_types = list(keywords_map.keys())
    matched = _fuzzy_match(text, all_types, threshold=0.4)
    return matched


def generate_work_experience(
    company: str,
    position: str,
    description: str,
    period: str = "",
) -> dict[str, Any]:
    """根据输入生成工作经历。"""
    # 匹配公司
    company_info = match_company(company)
    company_tags = company_info.get("tags", []) if company_info else []

    # 匹配职位
    position_info = match_position(position)
    skills = position_info.get("skills", []) if position_info else []
    keywords = position_info.get("keywords", []) if position_info else []

    # 提取用户提到的技能
    user_skills = extract_skills(description)
    all_skills = list(set(skills + user_skills))

    # 生成描述
    desc_parts = []
    if description.strip():
        desc_parts.append(description.strip())
    else:
        # 根据职位生成默认描述
        if keywords:
            desc_parts.append(f"负责{'、'.join(keywords[:3])}等核心工作")

    return {
        "company": company,
        "position": position,
        "period": period,
        "description": "\n".join(desc_parts),
        "suggested_skills": all_skills[:5],
        "company_tags": company_tags,
    }


def generate_project_experience(
    name: str,
    description: str,
    tech_stack: str = "",
) -> dict[str, Any]:
    """根据输入生成项目经历。"""
    # 匹配项目类型
    project_type = match_project_type(name + " " + description)

    # 提取技术栈
    user_tech = extract_skills(tech_stack) if tech_stack else []

    result = {
        "name": name,
        "description": description,
        "tech_stack": user_tech,
        "project_type": project_type,
    }

    # 如果匹配到项目模板，提供参考建议
    if project_type and project_type in PROJECT_TEMPLATES:
        templates = PROJECT_TEMPLATES[project_type]
        result["suggestions"] = [
            {
                "name": t["name"],
                "description": t["description"],
                "achievement_examples": t["achievements"][:2],
            }
            for t in templates[:1]
        ]

    return result


def generate_achievement(
    action: str,
    target: str,
    metric: str = "",
    result: str = "",
) -> str:
    """根据动作和目标生成成就描述。"""
    # 确定成就类别
    category = "技术"
    if any(kw in action for kw in ["增长", "提升", "转化", "留存"]):
        category = "业务"
    elif any(kw in action for kw in ["统筹", "协调", "推动", "带领"]):
        category = "管理"

    # 获取动词
    verbs = ACTION_VERBS.get(category, ACTION_VERBS["技术"])

    # 选择合适的动词
    verb = verbs[0]
    for v in verbs:
        if v in action:
            verb = v
            break

    # 组装描述
    if metric and result:
        return f"{verb}{target}，{metric}提升{result}%"
    elif metric:
        return f"{verb}{target}，{metric}得到显著提升"
    else:
        return f"{verb}{target}"


def suggest_skills_for_position(position: str) -> list[str]:
    """为指定职位推荐技能。"""
    position_info = match_position(position)
    if position_info:
        return position_info.get("skills", [])
    return []


def suggest_industry_terms(text: str) -> list[str]:
    """根据文本内容推荐行业术语。"""
    terms = []
    for industry, keywords in INDUSTRY_TERMS.items():
        if any(kw in text for kw in keywords[:3]):
            terms.extend(keywords[:3])
    return list(set(terms))[:5]


def enrich_resume_data(resume_data: dict[str, Any]) -> dict[str, Any]:
    """用知识库丰富简历数据。"""
    result = resume_data.copy()

    # 丰富工作经历
    work = result.get("work", [])
    for i, w in enumerate(work):
        company = w.get("company", "")
        position = w.get("position", "")
        desc = w.get("description", "")
        if company:
            info = match_company(company)
            if info:
                work[i]["_company_tags"] = info.get("tags", [])
        if position:
            info = match_position(position)
            if info:
                work[i]["_suggested_skills"] = info.get("skills", [])[:5]

    # 丰富项目经历
    projects = result.get("projects", [])
    for i, p in enumerate(projects):
        name = p.get("name", "")
        desc = p.get("description", "")
        if name:
            project_type = match_project_type(name)
            if project_type and project_type in PROJECT_TEMPLATES:
                projects[i]["_project_type"] = project_type

    # 丰富技能
    skills = result.get("skills", [])
    all_text = " ".join([
        w.get("description", "") for w in work
    ] + [
        p.get("description", "") for p in projects
    ])
    if all_text:
        suggested = extract_skills(all_text)
        current_skills = set()
        for s in skills:
            if isinstance(s, dict):
                current_skills.update(s.get("keywords", []))
            elif isinstance(s, str):
                current_skills.add(s)
        new_skills = [s for s in suggested if s not in current_skills]
        if new_skills:
            result["_suggested_skills"] = new_skills[:5]

    return result


def diagnose_resume(resume_data: dict[str, Any]) -> dict[str, Any]:
    """用规则诊断简历问题。"""
    issues = []
    warnings = []
    suggestions = []

    basics = resume_data.get("basics", {})
    work = resume_data.get("work", [])
    projects = resume_data.get("projects", [])
    skills = resume_data.get("skills", [])
    education = resume_data.get("education", [])
    summary = resume_data.get("summary", {})

    # 检查基本信息
    if not basics.get("name", "").strip():
        issues.append("缺少姓名")
    if not basics.get("email", "").strip() and not basics.get("phone", "").strip():
        issues.append("缺少联系方式（邮箱或电话）")
    if not basics.get("title", "").strip():
        warnings.append("建议填写目标岗位")

    # 检查个人简介
    summary_content = ""
    if isinstance(summary, dict):
        summary_content = summary.get("content", "")
    elif isinstance(summary, str):
        summary_content = summary
    if not summary_content.strip():
        warnings.append("个人简介为空，建议补充")
    elif len(summary_content) < 30:
        warnings.append("个人简介过短，建议扩充到 50-150 字")

    # 检查工作经历
    if not work:
        warnings.append("工作经历为空")
    else:
        for i, w in enumerate(work):
            if not w.get("company", "").strip():
                issues.append(f"工作经历第{i+1}条缺少公司名称")
            if not w.get("position", "").strip():
                issues.append(f"工作经历第{i+1}条缺少职位名称")
            desc = w.get("description", "")
            if len(desc) < 20:
                warnings.append(f"工作经历第{i+1}条描述过短，建议补充具体职责和成果")
            # 检查是否有量化数据
            if not re.search(r'\d+', desc):
                suggestions.append(f"工作经历第{i+1}条缺少量化数据，建议添加具体数字")

    # 检查项目经历
    if not projects:
        suggestions.append("建议添加项目经历以增强竞争力")
    else:
        for i, p in enumerate(projects):
            if not p.get("name", "").strip():
                issues.append(f"项目经历第{i+1}条缺少项目名称")
            desc = p.get("description", "")
            if len(desc) < 20:
                warnings.append(f"项目经历第{i+1}条描述过短")

    # 检查技能
    if not skills:
        warnings.append("专业技能为空")
    elif len(skills) < 3:
        warnings.append("专业技能较少，建议补充")

    # 检查教育经历
    if not education:
        warnings.append("教育经历为空")

    # 检查一致性
    work_positions = [w.get("position", "") for w in work if w.get("position")]
    if work_positions and basics.get("title"):
        target = basics["title"]
        if not any(target in pos or pos in target for pos in work_positions):
            suggestions.append("目标岗位与工作经历中的职位不一致，建议统一")

    # 计算完整度
    completeness = 100
    completeness -= len(issues) * 15
    completeness -= len(warnings) * 5
    completeness = max(0, min(100, completeness))

    return {
        "completeness": completeness,
        "issues": issues,
        "warnings": warnings,
        "suggestions": suggestions,
        "has_critical": len(issues) > 0,
    }
