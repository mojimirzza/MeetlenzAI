from __future__ import annotations
from fastapi import APIRouter, HTTPException, UploadFile, File
from app.core.models import MeetingCreate, QuestionCreate, LikeCreate, ModerationDecision, ParticipantCreate, OutcomeCreate
from app.storage.db import (create_meeting, get_meeting, add_question, get_questions, add_like, add_decision,
                            update_questions_category, upsert_participant, get_participants, add_outcome,
                            add_event, get_events, purge_meeting, save_categories, get_category, get_nominee, get_decisions, get_asked_questions)
from app.services.pipeline import IntakeQuestion
from app.bootstrap.container import get_container
from app.agents.priority_agent import PriorityAgent
from app.services.evidence import build_evidence_report, report_dict

router=APIRouter()

def _require_meeting(mid):
    m=get_meeting(mid)
    if not m: raise HTTPException(404,"meeting not found")
    return m

@router.post("/meetings")
def create(payload: MeetingCreate):
    row=create_meeting(payload.title,payload.domain,payload.agenda,payload.manager_user_id); add_event(row.id,"MEETING_CREATED",{"title":row.title},payload.manager_user_id)
    return {"id":row.id,"title":row.title}

@router.post("/meetings/{meeting_id}/participants")
def participant(meeting_id: str, payload: ParticipantCreate):
    _require_meeting(meeting_id); row=upsert_participant(meeting_id,payload.user_id,payload.display_name,payload.expertise)
    return {"user_id":row.user_id,"display_name":row.display_name,"expertise":row.expertise.split(",") if row.expertise else []}

@router.post("/questions")
def intake(payload: QuestionCreate):
    _require_meeting(payload.meeting_id); row=add_question(payload.meeting_id,payload.user_id,payload.text,payload.expertise); add_event(payload.meeting_id,"QUESTION_SUBMITTED",{"question_id":row.id},payload.user_id)
    return {"id":row.id,"status":row.status}

def _require_question(qid: str):
    from app.storage.db import QuestionRow, SessionLocal
    with SessionLocal() as s:
        row=s.get(QuestionRow,qid)
        if not row: raise HTTPException(404,"question not found")
        return row

@router.post("/questions/like")
def like(payload: LikeCreate):
    row = next((q for q in get_questions(_require_question(payload.question_id).meeting_id) if q.id == payload.question_id), None)
    accepted=add_like(payload.question_id,payload.user_id)
    if accepted and row:
        add_event(row.meeting_id,"QUESTION_LIKED",{"question_id":row.id},payload.user_id)
    return {"accepted":accepted}

@router.post("/meetings/{meeting_id}/process")
async def process(meeting_id: str):
    m=_require_meeting(meeting_id); rows=get_questions(meeting_id)
    items=[IntakeQuestion(q.id,q.user_id,q.text,q.likes,q.created_at,[x for x in q.expertise.split(",") if x]) for q in rows]
    container = get_container()
    result=await container.pipeline.run(meeting_id=meeting_id, meeting_title=m.title,domain=m.domain,agenda=m.agenda,questions=items)
    result.categories=container.priority_agent.rank(result.categories)
    mapping={qid:c.category_id for c in result.categories for qid in c.source_question_ids}
    scores={q.id: next((c.priority_score for c in result.categories if q.id in c.source_question_ids),0.0) for q in items}
    update_questions_category(meeting_id,mapping,scores); save_categories(meeting_id,result.categories); add_event(meeting_id,"PIPELINE_COMPLETED",{"categories":len(result.categories),"fallback":result.fallback},m.manager_user_id)
    return result.model_dump(mode="json")

@router.post("/meetings/{meeting_id}/moderate")
def moderate(meeting_id: str,payload: ModerationDecision):
    m=_require_meeting(meeting_id)
    if payload.moderator_user_id!=m.manager_user_id: raise HTTPException(403,"only the meeting moderator can decide")
    if payload.action.value in {"approve","edit"} and not payload.nominee_id: raise HTTPException(422,"nominee_id required")
    category = get_category(meeting_id, payload.category_id)
    if not category: raise HTTPException(422,"category not found; process the meeting first")
    if payload.nominee_id and not get_nominee(payload.category_id, payload.nominee_id): raise HTTPException(422,"nominee does not belong to category")
    if payload.action.value=="edit" and not payload.edited_text: raise HTTPException(422,"edited_text required")
    asked_text=None
    if payload.action.value in {"approve","edit"}:
        asked_text = None
        if payload.nominee_id:
            nominee = get_nominee(payload.category_id, payload.nominee_id)
            asked_text = nominee.text if nominee else None
        if not asked_text: raise HTTPException(422,"selected nominee not found")
    try: row, asked=add_decision(meeting_id,payload.category_id,payload.action,payload.nominee_id,payload.edited_text,payload.moderator_user_id,payload.reason,asked_text)
    except ValueError as e: raise HTTPException(422,str(e))
    add_event(meeting_id,"MODERATOR_DECISION",{"decision_id":row.id,"action":row.action,"asked_question_id":getattr(asked,"id",None)},payload.moderator_user_id)
    return {"decision_id":row.id,"action":row.action,"asked_question_id":getattr(asked,"id",None)}

@router.post("/outcomes")
def outcome(payload: OutcomeCreate):
    try: row=add_outcome(payload.asked_question_id,payload.outcome,payload.usefulness,payload.notes)
    except ValueError as e: raise HTTPException(404,str(e))
    # Outcome event is attached to the asked question's meeting via a direct lookup.
    from app.storage.db import AskedQuestionRow, SessionLocal
    with SessionLocal() as s: aq=s.get(AskedQuestionRow,payload.asked_question_id)
    if aq:
        add_event(aq.meeting_id,"QUESTION_OUTCOME_RECORDED",{"asked_question_id":aq.id,"outcome":row.outcome,"usefulness":row.usefulness},None)
    return {"id":row.id,"outcome":row.outcome}

@router.get("/meetings/{meeting_id}/questions")
def questions(meeting_id:str):
    _require_meeting(meeting_id); rows=get_questions(meeting_id)
    return [{"id":q.id,"user_id":q.user_id,"text":q.text,"expertise":q.expertise.split(",") if q.expertise else [],"likes":q.likes,"status":q.status,"category_id":q.category_id,"score":q.score,"created_at":q.created_at} for q in rows]

@router.get("/meetings/{meeting_id}/questions/related")
def related_questions(meeting_id:str,viewer_user_id:str,limit:int=5):
    _require_meeting(meeting_id); rows=get_questions(meeting_id); own=[q for q in rows if q.user_id==viewer_user_id]; others=[q for q in rows if q.user_id!=viewer_user_id]
    if not own or not others:return []
    from app.services.semantic import SemanticEncoder
    enc=SemanticEncoder(); all_texts=[q.text for q in own] + [q.text for q in others]
    vectors=enc.encode(all_texts)
    own_vec=vectors[:len(own)]
    other_vec=vectors[len(own):]
    from sklearn.metrics.pairwise import cosine_similarity
    sims=cosine_similarity(own_vec,other_vec).max(axis=0)
    ranked=sorted(zip(others,sims.tolist()),key=lambda x:x[1],reverse=True)[:max(1,min(limit,20))]
    return [{"id":q.id,"text":q.text,"similarity":float(score),"likes":q.likes} for q,score in ranked]

@router.get("/meetings/{meeting_id}/events")
def events(meeting_id:str):
    _require_meeting(meeting_id); return [{"id":e.id,"event_type":e.event_type,"actor_id":e.actor_id,"payload":e.payload,"trace_id":e.trace_id,"created_at":e.created_at} for e in get_events(meeting_id)]

@router.get("/meetings/{meeting_id}/evidence")
def evidence(meeting_id:str):
    _require_meeting(meeting_id)
    return report_dict(build_evidence_report(meeting_id))

@router.get("/meetings/{meeting_id}/coverage")
def coverage(meeting_id:str):
    _require_meeting(meeting_id)
    from app.services.coverage import coverage_report
    return coverage_report(get_participants(meeting_id), get_questions(meeting_id))

@router.get("/meetings/{meeting_id}/analytics")
def analytics(meeting_id:str):
    _require_meeting(meeting_id)
    report=build_evidence_report(meeting_id)
    return {"meeting_id":meeting_id,"summary":report.summary,"metrics":report.metrics}

@router.get("/meetings/{meeting_id}/snapshot")
def snapshot(meeting_id:str):
    m=_require_meeting(meeting_id); rows=get_questions(meeting_id); participants=get_participants(meeting_id)
    count=len({q.category_id for q in rows if q.category_id})
    return {"meeting_id":m.id,"title":m.title,"domain":m.domain,"agenda":m.agenda,"manager_user_id":m.manager_user_id,"participant_count":max(len(participants),len({q.user_id for q in rows})),"question_count":len(rows),"category_count":count}

@router.delete("/meetings/{meeting_id}")
def delete_meeting(meeting_id:str,moderator_user_id:str):
    m=_require_meeting(meeting_id)
    if moderator_user_id!=m.manager_user_id: raise HTTPException(403,"moderator only")
    purge_meeting(meeting_id); return {"deleted":True}

@router.post("/audio/transcribe")
async def transcribe(file: UploadFile=File(...)):
    from app.core.config import get_settings
    s=get_settings()
    if not s.enable_asr: raise HTTPException(409,"ASR is disabled")
    import tempfile,os
    suffix=os.path.splitext(file.filename or "audio.wav")[1]
    with tempfile.NamedTemporaryFile(delete=False,suffix=suffix) as tmp:
        tmp.write(await file.read()); path=tmp.name
    try:
        from app.services.audio import AudioService
        return {"segments":AudioService(s.asr_model).transcribe(path)}
    finally: os.unlink(path)
