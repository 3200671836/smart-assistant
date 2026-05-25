from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import get_db
from app.services.history_service import HistoryService
from app.services.resume_service import (
    extract_skills,
    analyze_match,
    optimize_project,
    optimize_project_iterative,
    generate_questions,
    get_suggestions,
)
from app.api.schemas import SkillsRequest, SkillsResponse, MatchRequest, MatchResponse, SuggestionsRequest, OptimizeRequest, QuestionsRequest

router = APIRouter(prefix="/resume", tags=["简历分析"])


def _save_history(db: Session, tool_name: str, input_summary: str, result: dict):
    """统一记录历史"""
    svc = HistoryService(db)
    svc.create(tool_name=tool_name, input_summary=input_summary, result_json=result)


@router.post("/skills", response_model=SkillsResponse)
def api_extract_skills(req: SkillsRequest, db: Session = Depends(get_db)):
    """从简历文本中提取技能清单"""
    result = extract_skills(req.text)
    _save_history(db, "skills_extraction", f"提取简历技能（{len(req.text)}字）", result)
    return SkillsResponse(skills=result)


@router.post("/match")
def api_analyze_match(req: MatchRequest, db: Session = Depends(get_db)):
    """分析简历与岗位的匹配度"""
    result = analyze_match(req.text, req.jd_text, req.skills)
    _save_history(
        db, "match_analysis",
        f"匹配分析：简历{len(req.text)}字 vs JD{len(req.jd_text)}字",
        result,
    )
    return result


@router.post("/suggestions")
def api_suggestions(req: SuggestionsRequest, db: Session = Depends(get_db)):
    """对比简历和JD，给出修改建议"""
    result = get_suggestions(req.resume_text, req.jd_requirements)
    _save_history(
        db, "resume_suggestions",
        f"简历修改建议：简历{len(req.resume_text)}字 vs JD{len(req.jd_requirements)}字",
        result,
    )
    try:
        print(result)
    except UnicodeEncodeError:
        pass
    return result


@router.post("/optimize")
def api_optimize_project(req: OptimizeRequest, db: Session = Depends(get_db)):
    """对项目描述给出STAR优化建议"""
    result = optimize_project(req.desc)
    _save_history(db, "project_optimize", f"优化项目描述（{len(req.desc)}字）", result)
    try:
        print(result)
    except UnicodeEncodeError:
        pass
    return result


@router.post("/optimize-iterative")
def api_optimize_project_iterative(req: OptimizeRequest, db: Session = Depends(get_db)):
    """多轮迭代优化项目描述（3轮）"""
    result = optimize_project_iterative(req.desc)
    _save_history(db, "project_optimize_iterative", f"多轮优化项目描述（{len(req.desc)}字）", result)
    try:
        print(result)
    except UnicodeEncodeError:
        pass
    return result


@router.post("/questions")
def api_generate_questions(req: QuestionsRequest, db: Session = Depends(get_db)):
    """根据简历和岗位生成模拟面试题"""
    result = generate_questions(req.highlights, req.jd_requirements)
    _save_history(
        db, "interview_questions",
        f"生成面试题：简历{len(req.highlights)}字 vs JD{len(req.jd_requirements)}字",
        result,
    )
    try:
        print(result)
    except UnicodeEncodeError:
        pass
    return result
