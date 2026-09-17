from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, UniqueConstraint, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from app.core.config import get_settings

class Base(DeclarativeBase): pass

class MeetingRow(Base):
    __tablename__ = "meetings"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(300)); domain: Mapped[str] = mapped_column(String(120), default="general")
    agenda: Mapped[str] = mapped_column(Text, default=""); manager_user_id: Mapped[str] = mapped_column(String(100), default="moderator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class ParticipantRow(Base):
    __tablename__ = "participants"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    meeting_id: Mapped[str] = mapped_column(ForeignKey("meetings.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(100), index=True)
    display_name: Mapped[str] = mapped_column(String(200)); expertise: Mapped[str] = mapped_column(Text, default="")
    __table_args__ = (UniqueConstraint("meeting_id", "user_id", name="uq_participant"),)


class CategoryRow(Base):
    __tablename__ = "categories"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    meeting_id: Mapped[str] = mapped_column(ForeignKey("meetings.id"), index=True)
    label: Mapped[str] = mapped_column(String(200))
    intent: Mapped[str] = mapped_column(Text)
    priority_score: Mapped[float] = mapped_column(Float, default=0.0)

class NomineeRow(Base):
    __tablename__ = "nominees"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    category_id: Mapped[str] = mapped_column(ForeignKey("categories.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    source_question_ids: Mapped[str] = mapped_column(Text, default="")

class QuestionRow(Base):
    __tablename__ = "questions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    meeting_id: Mapped[str] = mapped_column(ForeignKey("meetings.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(100), index=True)
    text: Mapped[str] = mapped_column(Text); normalized_text: Mapped[str] = mapped_column(Text, default="")
    expertise: Mapped[str] = mapped_column(Text, default=""); status: Mapped[str] = mapped_column(String(30), default="INTAKE")
    likes: Mapped[int] = mapped_column(Integer, default=0); category_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    score: Mapped[float] = mapped_column(Float, default=0.0); created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class LikeRow(Base):
    __tablename__ = "likes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True); question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), index=True)
    user_id: Mapped[str] = mapped_column(String(100), index=True); created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("question_id", "user_id", name="uq_like"),)

class DecisionRow(Base):
    __tablename__ = "moderation_decisions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True); meeting_id: Mapped[str] = mapped_column(String(36), index=True)
    category_id: Mapped[str] = mapped_column(String(36), index=True); action: Mapped[str] = mapped_column(String(30)); nominee_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    edited_text: Mapped[str | None] = mapped_column(Text, nullable=True); moderator_user_id: Mapped[str] = mapped_column(String(100)); reason: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class AskedQuestionRow(Base):
    __tablename__ = "asked_questions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True); meeting_id: Mapped[str] = mapped_column(String(36), index=True)
    category_id: Mapped[str] = mapped_column(String(36)); nominee_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    text: Mapped[str] = mapped_column(Text); moderator_user_id: Mapped[str] = mapped_column(String(100)); status: Mapped[str] = mapped_column(String(30), default="ASKED")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class OutcomeRow(Base):
    __tablename__ = "question_outcomes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True); asked_question_id: Mapped[str] = mapped_column(ForeignKey("asked_questions.id"), index=True)
    outcome: Mapped[str] = mapped_column(String(40)); usefulness: Mapped[int | None] = mapped_column(Integer, nullable=True); notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class AuditEventRow(Base):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True); meeting_id: Mapped[str] = mapped_column(String(36), index=True)
    event_type: Mapped[str] = mapped_column(String(80)); actor_id: Mapped[str | None] = mapped_column(String(100), nullable=True); payload: Mapped[str] = mapped_column(Text, default="{}"); trace_id: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

from sqlalchemy import create_engine
engine = create_engine(get_settings().database_url.replace("+aiosqlite", ""), future=True)
from sqlalchemy.orm import sessionmaker
SessionLocal = sessionmaker(engine, expire_on_commit=False)

def now(): return datetime.now(timezone.utc)
def init_db(): Base.metadata.create_all(engine)

def create_meeting(title, domain, agenda, manager_user_id):
    row = MeetingRow(id=str(uuid4()), title=title, domain=domain, agenda=agenda, manager_user_id=manager_user_id, created_at=now())
    with SessionLocal() as s: s.add(row); s.commit()
    return row

def get_meeting(mid):
    with SessionLocal() as s: return s.get(MeetingRow, mid)

def upsert_participant(meeting_id, user_id, display_name, expertise):
    with SessionLocal() as s:
        row = s.execute(select(ParticipantRow).where(ParticipantRow.meeting_id==meeting_id, ParticipantRow.user_id==user_id)).scalar_one_or_none()
        if row is None: row=ParticipantRow(id=str(uuid4()), meeting_id=meeting_id, user_id=user_id, display_name=display_name, expertise=",".join(expertise))
        else: row.display_name=display_name; row.expertise=",".join(expertise)
        s.add(row); s.commit(); return row

def add_question(meeting_id, user_id, text, expertise=None):
    row=QuestionRow(id=str(uuid4()), meeting_id=meeting_id, user_id=user_id, text=text, normalized_text=text.strip(), expertise=",".join(expertise or []), created_at=now())
    with SessionLocal() as s: s.add(row); s.commit()
    return row

def get_questions(mid):
    with SessionLocal() as s: return list(s.execute(select(QuestionRow).where(QuestionRow.meeting_id==mid).order_by(QuestionRow.created_at)).scalars())

def add_like(qid, uid):
    with SessionLocal() as s:
        if s.execute(select(LikeRow).where(LikeRow.question_id==qid, LikeRow.user_id==uid)).scalar_one_or_none(): return False
        q=s.get(QuestionRow,qid)
        if q is None: return False
        s.add(LikeRow(id=str(uuid4()), question_id=qid, user_id=uid, created_at=now())); q.likes+=1; s.commit(); return True

def save_categories(meeting_id, categories):
    import json
    with SessionLocal() as s:
        incoming={c.category_id:c for c in categories}
        existing={c.id:c for c in s.execute(select(CategoryRow).where(CategoryRow.meeting_id==meeting_id)).scalars()}
        for cid,c in incoming.items():
            row=existing.get(cid)
            if row is None:
                row=CategoryRow(id=cid,meeting_id=meeting_id,label=c.label,intent=c.intent,priority_score=c.priority_score); s.add(row)
            else:
                row.label=c.label; row.intent=c.intent; row.priority_score=c.priority_score
            current={n.id:n for n in s.execute(select(NomineeRow).where(NomineeRow.category_id==cid)).scalars()}
            for n in c.nominees:
                nr=current.get(n.nominee_id)
                if nr is None:
                    nr=NomineeRow(id=n.nominee_id,category_id=cid,text=n.text,quality_score=n.quality_score,source_question_ids=json.dumps(n.source_question_ids)); s.add(nr)
                else:
                    nr.text=n.text; nr.quality_score=n.quality_score; nr.source_question_ids=json.dumps(n.source_question_ids)
        # Do not delete old categories: decisions/audit may refer to them. Marking obsolete is safer than destructive replacement.
        s.commit()

def get_categories(mid):
    with SessionLocal() as s: return list(s.execute(select(CategoryRow).where(CategoryRow.meeting_id==mid).order_by(CategoryRow.priority_score.desc())).scalars())

def get_nominees(mid):
    with SessionLocal() as s:
        cats = [c.id for c in s.execute(select(CategoryRow).where(CategoryRow.meeting_id==mid)).scalars()]
        if not cats: return []
        return list(s.execute(select(NomineeRow).where(NomineeRow.category_id.in_(cats))).scalars())

def get_decisions(mid):
    with SessionLocal() as s: return list(s.execute(select(DecisionRow).where(DecisionRow.meeting_id==mid).order_by(DecisionRow.created_at)).scalars())

def get_asked_questions(mid):
    with SessionLocal() as s: return list(s.execute(select(AskedQuestionRow).where(AskedQuestionRow.meeting_id==mid).order_by(AskedQuestionRow.created_at)).scalars())

def get_outcomes(mid):
    with SessionLocal() as s:
        aqids=[a.id for a in s.execute(select(AskedQuestionRow).where(AskedQuestionRow.meeting_id==mid)).scalars()]
        if not aqids: return []
        return list(s.execute(select(OutcomeRow).where(OutcomeRow.asked_question_id.in_(aqids)).order_by(OutcomeRow.created_at)).scalars())

def get_category(mid, category_id):
    with SessionLocal() as s:
        return s.execute(select(CategoryRow).where(CategoryRow.meeting_id==mid, CategoryRow.id==category_id)).scalar_one_or_none()

def get_nominee(category_id, nominee_id):
    with SessionLocal() as s:
        return s.execute(select(NomineeRow).where(NomineeRow.category_id==category_id, NomineeRow.id==nominee_id)).scalar_one_or_none()

def update_questions_category(mid, mapping, scores):
    with SessionLocal() as s:
        for q in s.execute(select(QuestionRow).where(QuestionRow.meeting_id==mid)).scalars():
            if q.id in mapping: q.category_id=mapping[q.id]; q.status="NOMINATED"
            if q.id in scores: q.score=scores[q.id]
        s.commit()

def add_decision(meeting_id, category_id, action, nominee_id, edited_text, moderator_user_id, reason, asked_text=None):
    with SessionLocal() as s:
        row=DecisionRow(id=str(uuid4()), meeting_id=meeting_id, category_id=category_id, action=action.value if hasattr(action,'value') else str(action), nominee_id=nominee_id, edited_text=edited_text, moderator_user_id=moderator_user_id, reason=reason, created_at=now())
        s.add(row)
        asked=None
        if row.action in {"approve","edit"}:
            text=(edited_text or asked_text or "").strip()
            if not text: raise ValueError("approved/edited decision requires question text")
            asked=AskedQuestionRow(id=str(uuid4()), meeting_id=meeting_id, category_id=category_id, nominee_id=nominee_id, text=text, moderator_user_id=moderator_user_id, created_at=now())
            s.add(asked)
        s.commit(); return row, asked

def add_outcome(asked_question_id, outcome, usefulness, notes):
    with SessionLocal() as s:
        aq=s.get(AskedQuestionRow, asked_question_id)
        if aq is None: raise ValueError("asked question not found")
        aq.status="ANSWERED" if outcome=="answered" else "DEFERRED" if outcome=="deferred" else "CLOSED"
        row=OutcomeRow(id=str(uuid4()), asked_question_id=asked_question_id, outcome=outcome, usefulness=usefulness, notes=notes, created_at=now()); s.add(row); s.commit(); return row

def add_event(meeting_id, event_type, payload, actor_id=None, trace_id=None):
    import json
    with SessionLocal() as s:
        row=AuditEventRow(id=str(uuid4()), meeting_id=meeting_id, event_type=event_type, actor_id=actor_id, payload=json.dumps(payload, ensure_ascii=False), trace_id=trace_id or str(uuid4()), created_at=now()); s.add(row); s.commit(); return row

def get_participants(mid):
    with SessionLocal() as s: return list(s.execute(select(ParticipantRow).where(ParticipantRow.meeting_id==mid)).scalars())

def get_events(mid):
    with SessionLocal() as s: return list(s.execute(select(AuditEventRow).where(AuditEventRow.meeting_id==mid).order_by(AuditEventRow.created_at)).scalars())

def purge_meeting(mid):
    with SessionLocal() as s:
        qids=[q.id for q in s.execute(select(QuestionRow).where(QuestionRow.meeting_id==mid)).scalars()]
        for model, field, vals in [(LikeRow, LikeRow.question_id, qids)]:
            for row in s.execute(select(model).where(field.in_(vals))).scalars(): s.delete(row)
        for model in [OutcomeRow, AskedQuestionRow, DecisionRow, AuditEventRow, NomineeRow, CategoryRow, ParticipantRow, QuestionRow]:
            column=getattr(model,"meeting_id",None)
            if column is not None:
                for row in s.execute(select(model).where(column==mid)).scalars(): s.delete(row)
        meeting=s.get(MeetingRow,mid)
        if meeting: s.delete(meeting)
        s.commit()
