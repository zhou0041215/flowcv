"""Agent 共享工具层 — 把现有业务能力封装为 LangChain Tools。"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.exceptions import AppException
from app.models.resume import Resume, ResumeVersion
from app.services.resume_locale import detect_resume_language, normalize_resume_language

logger = logging.getLogger(__name__)

BUILT_IN_SECTIONS = ["basics", "summary", "education", "skills", "work", "projects", "awards"]


def _get_db() -> Session:
    return SessionLocal()


def _get_resume(db: Session, resume_id: int) -> Resume:
    resume = db.get(Resume, resume_id)
    if not resume:
        raise AppException("简历不存在")
    return resume


@tool
def read_resume(resume_id: int) -> str:
    """读取简历完整数据，返回 JSON 格式的简历内容。

    Args:
        resume_id: 简历 ID
    """
    db = _get_db()
    try:
        resume = _get_resume(db, resume_id)
        data = resume.resume_data or {}
        return json.dumps(data, ensure_ascii=False, indent=2)
    finally:
        db.close()


@tool
def update_resume_section(resume_id: int, section: str, content: str) -> str:
    """更新简历某个模块的内容。

    Args:
        resume_id: 简历 ID
        section: 模块名称，可选值: basics, summary, education, skills, work, projects, awards, custom_sections, layout
        content: 新内容的 JSON 字符串
    """
    if section not in BUILT_IN_SECTIONS and section not in ("custom_sections", "layout"):
        return f"错误：无效的模块名 '{section}'，可选值：{', '.join(BUILT_IN_SECTIONS + ['custom_sections', 'layout'])}"

    db = _get_db()
    try:
        resume = _get_resume(db, resume_id)
        data = resume.resume_data or {}

        try:
            new_content = json.loads(content)
        except json.JSONDecodeError:
            return "错误：content 不是有效的 JSON 字符串"

        data[section] = new_content
        data = normalize_resume_language(data, detect_resume_language(data))
        resume.resume_data = data
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(resume, "resume_data")
        db.commit()
        return f"成功更新 {section} 模块"
    except Exception as e:
        return f"更新失败：{e}"
    finally:
        db.close()


@tool
def append_resume_item(resume_id: int, section: str, item: str) -> str:
    """向简历的列表模块追加一条记录。

    Args:
        resume_id: 简历 ID
        section: 模块名称（必须是列表类型：education, skills, work, projects, awards, custom_sections）
        item: 要追加的内容的 JSON 字符串
    """
    list_sections = ["education", "skills", "work", "projects", "awards", "custom_sections"]
    if section not in list_sections:
        return f"错误：'{section}' 不是列表模块，可选值：{', '.join(list_sections)}"

    db = _get_db()
    try:
        resume = _get_resume(db, resume_id)
        data = resume.resume_data or {}

        try:
            new_item = json.loads(item)
        except json.JSONDecodeError:
            return "错误：item 不是有效的 JSON 字符串"

        if not isinstance(data.get(section), list):
            data[section] = []

        data[section].append(new_item)
        data = normalize_resume_language(data, detect_resume_language(data))
        resume.resume_data = data
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(resume, "resume_data")
        db.commit()
        return f"成功向 {section} 追加一条记录，当前共 {len(data[section])} 条"
    except Exception as e:
        return f"追加失败：{e}"
    finally:
        db.close()


@tool
def analyze_job_description(jd_text: str) -> str:
    """分析岗位 JD，提取目标岗位、核心技能、职责要求、加分项。

    Args:
        jd_text: 岗位描述文本
    """
    from app.services.ai.chains import _parse_json_content
    from app.services.ai.llm import get_llm
    from app.services.ai.prompts import JD_NODE_PROMPT

    try:
        chain = JD_NODE_PROMPT | get_llm()
        message = chain.invoke({
            "task": "只分析岗位 JD，返回目标岗位、核心技能、核心职责、加分项、硬性条件；去除招聘套话。",
            "input_json": jd_text,
        })
        content = getattr(message, "content", str(message))
        try:
            result = _parse_json_content(content)
        except Exception:
            result = {"raw_analysis": content}
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"JD 分析失败：{e}"


@tool
def match_resume_jd(resume_id: int, jd_text: str) -> str:
    """计算简历与 JD 的匹配度，返回匹配项、缺失项、匹配分数。

    Args:
        resume_id: 简历 ID
        jd_text: 岗位描述文本
    """
    from app.services.ai.chains import _parse_json_content, _normalize_resume_data
    from app.services.ai.llm import get_llm
    from copy import deepcopy

    db = _get_db()
    try:
        resume = _get_resume(db, resume_id)
        data = resume.resume_data or {}
        data = _normalize_resume_data(deepcopy(data), {})

        prompt_text = f"""你是简历匹配分析专家。请对比以下简历和 JD，返回 JSON 格式的匹配分析。

简历数据：
{json.dumps(data, ensure_ascii=False, indent=2)}

岗位 JD：
{jd_text}

请返回以下格式的 JSON：
{{
    "score": 0-100 的匹配分数,
    "matched": ["已匹配的能力项1", "已匹配的能力项2"],
    "partial": ["部分匹配的能力项1"],
    "missing": ["缺失的能力项1", "缺失的能力项2"],
    "suggestions": ["建议1", "建议2"]
}}"""

        from langchain_core.messages import HumanMessage
        llm = get_llm()
        message = llm.invoke([HumanMessage(content=prompt_text)])
        content = getattr(message, "content", str(message))

        try:
            result = _parse_json_content(content)
        except Exception:
            result = {"raw_analysis": content}

        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"匹配分析失败：{e}"
    finally:
        db.close()


@tool
def validate_resume(resume_id: int) -> str:
    """检查简历完整性，返回缺失字段、格式问题、改进建议。

    Args:
        resume_id: 简历 ID
    """
    db = _get_db()
    try:
        resume = _get_resume(db, resume_id)
        data = resume.resume_data or {}

        issues = []
        warnings = []
        suggestions = []

        # 检查基本信息
        basics = data.get("basics", {})
        if not basics.get("name", "").strip():
            issues.append("缺少姓名")
        if not basics.get("email", "").strip() and not basics.get("phone", "").strip():
            issues.append("缺少联系方式（邮箱或电话）")

        # 检查个人简介
        summary = data.get("summary", {})
        if isinstance(summary, dict):
            content = summary.get("content", "")
        elif isinstance(summary, str):
            content = summary
        else:
            content = ""
        if not content.strip():
            warnings.append("个人简介为空")

        # 检查工作经历
        work = data.get("work", [])
        if not work:
            warnings.append("工作经历为空")
        else:
            for i, w in enumerate(work):
                if not w.get("company", "").strip():
                    warnings.append(f"工作经历第{i+1}条缺少公司名称")
                if not w.get("position", "").strip():
                    warnings.append(f"工作经历第{i+1}条缺少职位名称")

        # 检查教育经历
        education = data.get("education", [])
        if not education:
            warnings.append("教育经历为空")

        # 检查技能
        skills = data.get("skills", [])
        if not skills:
            warnings.append("专业技能为空")

        # 检查项目经历
        projects = data.get("projects", [])
        if not projects:
            suggestions.append("建议添加项目经历以增强竞争力")

        result = {
            "completeness": max(0, 100 - len(issues) * 15 - len(warnings) * 5),
            "issues": issues,
            "warnings": warnings,
            "suggestions": suggestions,
            "has_critical": len(issues) > 0,
        }

        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"验证失败：{e}"
    finally:
        db.close()


@tool
def create_version_snapshot(resume_id: int) -> str:
    """创建当前简历的版本快照，用于修改前备份。

    Args:
        resume_id: 简历 ID
    """
    db = _get_db()
    try:
        resume = _get_resume(db, resume_id)
        data = resume.resume_data or {}

        version = ResumeVersion(
            resume_id=resume_id,
            title=f"Agent 自动备份",
            resume_data=data,
            template_config=resume.template_config,
            reason="Agent 自动备份",
        )
        db.add(version)
        db.commit()
        return f"成功创建版本快照，版本 ID: {version.id}"
    except Exception as e:
        return f"创建快照失败：{e}"
    finally:
        db.close()


@tool
def get_resume_summary(resume_id: int) -> str:
    """获取简历摘要信息（不含完整数据，用于快速了解简历概况）。

    Args:
        resume_id: 简历 ID
    """
    db = _get_db()
    try:
        resume = _get_resume(db, resume_id)
        data = resume.resume_data or {}

        basics = data.get("basics", {})
        summary = {
            "name": basics.get("name", ""),
            "title": basics.get("headline", basics.get("title", "")),
            "email": basics.get("email", ""),
            "phone": basics.get("phone", ""),
            "location": basics.get("location", ""),
            "sections": {
                "work": len(data.get("work", [])),
                "education": len(data.get("education", [])),
                "projects": len(data.get("projects", [])),
                "skills": len(data.get("skills", [])),
                "awards": len(data.get("awards", [])),
            },
            "language": resume.language or "zh",
        }
        return json.dumps(summary, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"获取摘要失败：{e}"
    finally:
        db.close()
