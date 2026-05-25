import json

from app.services.llm_service import LLMService

# ========== 技能提取 ==========

SKILLS_EXTRACTION_PROMPT = """你是一个简历分析助手。请从简历文本中提取求职者的技能，并按类别归类。

输出格式（严格返回JSON，不要包含任何其他内容）：
{
  "tech_skills": ["Python", "FastAPI", "SQLAlchemy"],
  "soft_skills": ["团队协作", "沟通表达"],
  "tools": ["Git", "Docker", "Linux"],
  "languages": ["英语六级"],
  "certifications": []
}
"""


def extract_skills(text: str) -> dict:
    """
    调用 LLM 从简历文本中提取结构化技能清单。
    失败时返回空列表结构（不破坏 Pydantic 校验）。
    """
    llm = LLMService()

    raw_chat = llm.chat(SKILLS_EXTRACTION_PROMPT, text, structured=True)
    print("===== 原始 chat 返回 =====")
    print(raw_chat)
    print("==========================")


    result = llm.extract_json(SKILLS_EXTRACTION_PROMPT, text)
    if result is None:
        # 返回空结构，让 API 层正常序列化
        return {
            "tech_skills": [],
            "soft_skills": [],
            "tools": [],
            "languages": [],
            "certifications": [],
            "_error": "技能提取失败，请检查 API Key 或文本内容"
        }
    return result



# ========== 匹配度分析 ==========

MATCH_ANALYSIS_PROMPT = """你是一个资深HR招聘专家。请对比简历和岗位描述（JD），进行深度匹配分析。

简历文本：
{resume_text}

岗位描述：
{jd_text}

输出格式（严格返回JSON，不要包含任何其他内容）：
{{
  "match_level": "high/medium/low",
  "match_score": 75,
  "matched_skills": ["Python", "FastAPI"],
  "missing_skills": ["Kubernetes", "Redis"],
  "dimension_analysis": {{
    "技术深度": "候选人技术栈与岗位高度匹配，但缺乏大规模系统经验",
    "业务经验": "有电商后端经验，与岗位方向一致",
    "学历背景": "本科211，满足岗位要求"
  }},
  "summary": "综合评价一段话总结"
}}
"""


def analyze_match(resume_text: str, jd_text: str, skills: dict | None = None) -> dict:
    """
    对比简历和JD，输出匹配分析结果。
    如果已提取技能，可传入避免重复调用 LLM（保留在 skills 字段）。
    """
    llm = LLMService()
    user_prompt = MATCH_ANALYSIS_PROMPT.format(
        resume_text=resume_text[:3000],
        jd_text=jd_text[:3000],
    )
    if skills:
        skills_str = json.dumps(skills, ensure_ascii=False, indent=2)
        user_prompt = f"【已提取的简历技能，仅供参考】\n{skills_str}\n\n" + user_prompt

    result = llm.extract_json(
        "你是一个专业的HR招聘专家。严格按JSON格式输出。",
        user_prompt,
    )
    if result is None:
        return {
            "match_level": "unknown",
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "dimension_analysis": {},
            "summary": "匹配分析失败，请稍后重试",
            "_error": "匹配分析失败"
        }
    return result


# ========== 多轮迭代项目优化 ==========

ROUND1_PROMPT = """你是一名资深技术面试官 + 简历优化专家。请对项目描述进行第1轮基线优化。

原始项目描述：
{project_desc}

分析原始描述的问题（量化缺失、技术平淡、表达模糊），输出结构化建议 + 明显优于原始描述的优化版本。

严格返回JSON格式：
{{
  "round": 1,
  "current_issue": "问题总结",
  "suggestions": [
    {{"dimension": "量化成果", "advice": "..."}},
    {{"dimension": "技术深度", "advice": "..."}},
    {{"dimension": "表达清晰", "advice": "..."}}
  ],
  "optimized_version": "优化后的描述"
}}
"""

ROUND2_PROMPT = """你是一名资深技术面试官 + 简历优化专家。请对项目描述进行第2轮深度批判与增强。

上一轮优化后的版本：
{previous_version}

扮演挑剔的面试官，指出该版本仍然存在的不足（数据不够具体、技术难点未突出、动词选择不够有力等）。
针对不足，再次从三个维度给出更深入的建议，并产出比第1轮更强的版本。

严格返回JSON格式：
{{
  "round": 2,
  "current_issue": "上一版遗留问题",
  "suggestions": [
    {{"dimension": "量化成果", "advice": "..."}},
    {{"dimension": "技术深度", "advice": "..."}},
    {{"dimension": "表达清晰", "advice": "..."}}
  ],
  "optimized_version": "优化后的描述"
}}
"""

ROUND3_PROMPT = """你是一名资深技术面试官 + 简历优化专家。请对项目描述进行第3轮最终打磨与亮点提炼。

第2轮优化后的版本：
{previous_version}

检查是否有冗余词汇、是否能用更专业术语替换、是否突出了个人贡献（而非团队）。
最后输出一个可直接用于简历的最终版本，并附上一个"亮点摘要"（用一句话总结该项目的最大卖点）。

严格返回JSON格式：
{{
  "round": 3,
  "current_issue": "终审发现的微小瑕疵",
  "suggestions": [
    {{"dimension": "量化成果", "advice": "..."}},
    {{"dimension": "技术深度", "advice": "..."}},
    {{"dimension": "表达清晰", "advice": "..."}}
  ],
  "optimized_version": "最终版本",
  "final_highlight": "例如：通过索引优化将查询耗时从2s降至50ms，支撑了日均百万级请求"
}}
"""


def optimize_project_iterative(project_desc: str) -> dict:
    """
    多轮迭代优化项目描述，共3轮。
    返回包含所有轮次结果的字典。
    """
    llm = LLMService()
    
    # 第1轮：基线优化
    round1 = llm.extract_json(
        "你是一个资深技术面试官 + 简历优化专家。严格按JSON格式输出。",
        ROUND1_PROMPT.format(project_desc=project_desc[:2000]),
    )
    if round1 is None:
        return {
            "rounds": [],
            "final_version": project_desc,
            "final_highlight": "优化失败",
            "_error": "第1轮优化失败"
        }
    
    # 第2轮：深度批判与增强
    round2 = llm.extract_json(
        "你是一个资深技术面试官 + 简历优化专家。严格按JSON格式输出。",
        ROUND2_PROMPT.format(previous_version=round1.get("optimized_version", project_desc)),
    )
    if round2 is None:
        return {
            "rounds": [round1],
            "final_version": round1.get("optimized_version", project_desc),
            "final_highlight": "第2轮优化失败",
            "_error": "第2轮优化失败"
        }
    
    # 第3轮：最终打磨与亮点提炼
    round3 = llm.extract_json(
        "你是一个资深技术面试官 + 简历优化专家。严格按JSON格式输出。",
        ROUND3_PROMPT.format(previous_version=round2.get("optimized_version", project_desc)),
    )
    if round3 is None:
        return {
            "rounds": [round1, round2],
            "final_version": round2.get("optimized_version", project_desc),
            "final_highlight": "第3轮优化失败",
            "_error": "第3轮优化失败"
        }
    
    return {
        "rounds": [round1, round2, round3],
        "final_version": round3.get("optimized_version", ""),
        "final_highlight": round3.get("final_highlight", ""),
    }


# 保留旧版单轮优化接口（向后兼容）
OPTIMIZE_PROMPT = """你是一个资深技术面试官。请针对简历中的项目描述，给出优化建议，使其更有含金量。

项目描述：
{project_desc}

请从以下维度给出建议：
1. 量化成果：如何用数据支撑项目成果
2. 技术深度：如何突出技术难点和创新点
3. 表达清晰：如何让描述更精准、更有说服力

输出JSON格式：
{{
  "current_issue": "当前描述存在的问题",
  "suggestions": [
    {{"dimension": "量化成果", "advice": "建议内容"}},
    {{"dimension": "技术深度", "advice": "建议内容"}},
    {{"dimension": "表达清晰", "advice": "建议内容"}}
  ],
  "optimized_version": "优化后的版本"
}}
"""


def optimize_project(project_desc: str) -> dict:
    """单轮优化（向后兼容）"""
    llm = LLMService()
    result = llm.extract_json(
        "你是一个资深技术面试官。严格按JSON格式输出。",
        OPTIMIZE_PROMPT.format(project_desc=project_desc[:2000]),
    )
    if result is None:
        return {
            "current_issue": "（LLM调用失败）",
            "suggestions": [],
            "optimized_version": project_desc,
            "_error": "项目优化失败"
        }
    return result


# ========== 模拟面试题 ==========

QUESTIONS_PROMPT = """你是一个面试官。根据简历亮点和岗位要求，生成针对性的模拟面试题。

简历摘要：
{resume_highlights}

岗位要求：
{jd_requirements}

输出JSON格式（生成5-8道题）：
{{
  "questions": [
    {{
      "topic": "项目经验",
      "question": "面试题",
      "answer_tips": "参考答案要点",
      "difficulty": "medium"
    }}
  ]
}}
"""


def generate_questions(resume_highlights: str, jd_requirements: str) -> dict:
    llm = LLMService()
    result = llm.extract_json(
        "你是一个资深技术面试官。严格按JSON格式输出。",
        QUESTIONS_PROMPT.format(
            resume_highlights=resume_highlights[:2000],
            jd_requirements=jd_requirements[:2000],
        ),
    )
    if result is None:
        return {
            "questions": [],
            "_error": "面试题生成失败"
        }
    return result


# ========== 简历修改建议（整体优化） ==========
RESUME_SUGGESTIONS_PROMPT = """你是一位资深HR，请根据目标岗位的要求，对简历内容提出具体修改建议，让简历更匹配JD。

简历原文：
{resume_text}

岗位要求：
{jd_requirements}

输出JSON格式：
{{
  "overall_assessment": "整体评价，指出简历与JD的主要差距",
  "suggestions": [
    {{
      "section": "个人总结/工作经历/项目经验/技能等",
      "original": "原文片段（如有）",
      "suggested_change": "修改建议或重写内容",
      "reason": "为什么要这样改"
    }}
  ],
  "priority": ["按重要性排序的修改条目索引"]
}}
"""

def get_suggestions(resume_text: str, jd_requirements: str) -> dict:
    """
    根据简历和目标岗位要求，给出整体修改建议。
    """
    llm = LLMService()
    user_prompt = RESUME_SUGGESTIONS_PROMPT.format(
        resume_text=resume_text[:3000],
        jd_requirements=jd_requirements[:3000]
    )
    result = llm.extract_json(
        system_prompt="你是一个专业的HR，严格按JSON格式输出简历修改建议。",
        user_prompt=user_prompt
    )
    if result is None:
        return {
            "overall_assessment": "建议生成失败",
            "suggestions": [],
            "priority": [],
            "_error": "LLM调用失败"
        }
    return result

