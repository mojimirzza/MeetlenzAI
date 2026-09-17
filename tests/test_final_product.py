import pytest
from datetime import datetime, timezone
from app.services.pipeline import QuestionPipeline, IntakeQuestion
from app.services.semantic import keyword_overlap
from app.services.ranking import diminishing_ratio

@pytest.mark.asyncio
async def test_persian_duplicate_fallback_clusters():
    p=QuestionPipeline()
    async def fail(*a,**k): raise RuntimeError("no model")
    p.llm.structured=fail
    now=datetime.now(timezone.utc)
    qs=[IntakeQuestion("1","u1","تاریخ لانچ محصول کی هست؟",2,now,[]),IntakeQuestion("2","u2","چه زمانی محصول لانچ می‌شود؟",1,now,[]),IntakeQuestion("3","u3","بودجه استخدام چقدر است؟",0,now,[])]
    r=await p.run(meeting_title="Roadmap",domain="product",agenda="launch",questions=qs)
    assert r.fallback is True
    assert len(r.categories)==2
    assert any(len(c.source_question_ids)==2 for c in r.categories)


def test_diminishing_returns_prevent_frequency_explosion():
    assert diminishing_ratio(100,100) == 1.0
    assert diminishing_ratio(10,100) < 0.6


def test_keyword_overlap_bilingual_tokens():
    assert keyword_overlap("تاریخ لانچ محصول", "لانچ محصول") > 0.5

from app.core.models import QuestionCategory, Nominee
from app.agents.priority_agent import PriorityAgent


def test_priority_agent_exposes_diversity_selection_score():
    cats=[
        QuestionCategory(category_id='a',label='a',intent='launch date',source_question_ids=['1'],nominees=[Nominee(nominee_id='n1',text='When is launch?',source_question_ids=['1'])],priority_score=.9),
        QuestionCategory(category_id='b',label='b',intent='launch date for customers',source_question_ids=['2'],nominees=[Nominee(nominee_id='n2',text='When do customers receive it?',source_question_ids=['2'])],priority_score=.89),
        QuestionCategory(category_id='c',label='c',intent='hiring budget',source_question_ids=['3'],nominees=[Nominee(nominee_id='n3',text='What is the hiring budget?',source_question_ids=['3'])],priority_score=.7),
    ]
    out=PriorityAgent().rank(cats)
    assert len(out)==3
    assert all('mmr_selection_score' in c.priority_explanation for c in out)

@pytest.mark.asyncio
async def test_reprocessing_keeps_stable_ids(monkeypatch):
    p=QuestionPipeline()
    async def fail(*a,**k): raise RuntimeError('offline')
    monkeypatch.setattr(p.llm,'structured',fail)
    now=datetime.now(timezone.utc)
    qs=[IntakeQuestion('q1','u1','When will the product launch?',0,now,[]),IntakeQuestion('q2','u2','What is the launch date?',0,now,[])]
    a=await p.run(meeting_title='Roadmap',domain='product',agenda='launch',questions=qs)
    b=await p.run(meeting_title='Roadmap',domain='product',agenda='launch',questions=qs)
    assert [c.category_id for c in a.categories]==[c.category_id for c in b.categories]
    assert [n.text for n in a.categories[0].nominees]==[n.text for n in b.categories[0].nominees]
    assert [n.nominee_id for n in a.categories[0].nominees]==[n.nominee_id for n in b.categories[0].nominees]


def test_evidence_report_after_human_gate():
    from app.services.evidence import build_evidence_report
    from app.storage.db import init_db, create_meeting, add_question, save_categories, add_decision, add_outcome
    from app.core.models import ModeratorAction, QuestionCategory, Nominee
    init_db()
    m=create_meeting('Evidence Test','architecture','launch','mod')
    q=add_question(m.id,'u1','When is production launch?',['architecture'])
    cid='cat-evidence-' + m.id[:8]
    nid='nom-evidence-' + m.id[:8]
    c=QuestionCategory(category_id=cid,label='Launch timing',intent='production launch timing',source_question_ids=[q.id],nominees=[Nominee(nominee_id=nid,text='What is the target production launch date?',source_question_ids=[q.id])],priority_score=.8)
    save_categories(m.id,[c])
    d, asked=add_decision(m.id,cid,ModeratorAction.APPROVE,nid,None,'mod','test','What is the target production launch date?')
    add_outcome(asked.id,'answered',5,'done')
    report=build_evidence_report(m.id)
    assert report.summary['questions']==1
    assert report.summary['asked_questions']==1
    assert report.metrics['answer_rate']==1.0
    assert 'semantic_compression_rate' in report.metrics


def test_category_ids_are_isolated_per_meeting():
    import asyncio
    from datetime import datetime, timezone
    from app.services.pipeline import QuestionPipeline, IntakeQuestion
    async def run():
        p=QuestionPipeline()
        async def fail(*a,**k): raise RuntimeError('offline')
        p.llm.structured=fail
        now=datetime.now(timezone.utc)
        q=[IntakeQuestion('q','u','When is the product launch?',0,now,[])]
        a=await p.run(meeting_id='meeting-a',meeting_title='Roadmap',domain='product',agenda='launch',questions=q)
        b=await p.run(meeting_id='meeting-b',meeting_title='Roadmap',domain='product',agenda='launch',questions=q)
        assert a.categories[0].category_id != b.categories[0].category_id
    asyncio.run(run())


def test_benchmark_script_runs_from_repository_root():
    import subprocess
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    r = subprocess.run([sys.executable, "scripts/benchmark.py"], cwd=root, capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stdout + r.stderr
    assert 'controlled_synthetic_benchmark' in r.stdout
