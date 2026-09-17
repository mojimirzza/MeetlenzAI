from fastapi.testclient import TestClient
from app.main import create_app


def test_api_human_gate_end_to_end():
    app = create_app()
    with TestClient(app) as client:
        m=client.post('/api/meetings',json={'title':'Roadmap','domain':'product','agenda':'launch','manager_user_id':'mod'}).json()
        mid=m['id']
        client.post(f'/api/meetings/{mid}/participants',json={'user_id':'u1','display_name':'A','expertise':['product']})
        q=client.post('/api/questions',json={'meeting_id':mid,'user_id':'u1','text':'When will the product launch?'}).json()
        assert q['id']
        out=client.post(f'/api/meetings/{mid}/process').json()
        cat=out['categories'][0]; nom=cat['nominees'][0]
        d=client.post(f'/api/meetings/{mid}/moderate',json={'category_id':cat['category_id'],'action':'approve','nominee_id':nom['nominee_id'],'moderator_user_id':'mod'}).json()
        assert d['asked_question_id']
        outcome=client.post('/api/outcomes',json={'asked_question_id':d['asked_question_id'],'outcome':'answered','usefulness':5}).json()
        assert outcome['outcome']=='answered'


def test_moderator_cannot_approve_with_invalid_nominee():
    from fastapi.testclient import TestClient
    from app.main import create_app
    with TestClient(create_app()) as client:
        m=client.post('/api/meetings',json={'title':'Security Review','domain':'fintech','agenda':'controls','manager_user_id':'mod-2'}).json()
        mid=m['id']
        client.post('/api/questions',json={'meeting_id':mid,'user_id':'u1','text':'What controls cover this change?'})
        out=client.post(f'/api/meetings/{mid}/process').json()
        cat=out['categories'][0]
        r=client.post(f'/api/meetings/{mid}/moderate',json={'category_id':cat['category_id'],'action':'approve','nominee_id':'not-real','moderator_user_id':'mod-2'})
        assert r.status_code == 422


def test_evidence_endpoint_returns_measurable_report():
    from fastapi.testclient import TestClient
    from app.main import create_app
    with TestClient(create_app()) as client:
        m=client.post('/api/meetings',json={'title':'Evidence API','domain':'architecture','agenda':'launch','manager_user_id':'mod-3'}).json()
        mid=m['id']
        client.post('/api/questions',json={'meeting_id':mid,'user_id':'u1','text':'When is launch?'})
        client.post(f'/api/meetings/{mid}/process')
        r=client.get(f'/api/meetings/{mid}/evidence')
        assert r.status_code==200
        body=r.json()
        assert 'metrics' in body and 'summary' in body
        assert body['summary']['questions']==1


def test_related_questions_and_nominee_text():
    from fastapi.testclient import TestClient
    with TestClient(create_app()) as client:
        r=client.post("/api/meetings",json={"title":"Review","domain":"architecture","agenda":"migration","manager_user_id":"mod"})
        mid=r.json()["id"]
        assert client.post(f"/api/meetings/{mid}/participants",json={"user_id":"u1","display_name":"A","expertise":["db"]}).status_code==200
        assert client.post(f"/api/meetings/{mid}/participants",json={"user_id":"u2","display_name":"B","expertise":["db"]}).status_code==200
        client.post("/api/questions",json={"meeting_id":mid,"user_id":"u1","text":"When is the database migration target date?","expertise":["db"]})
        client.post("/api/questions",json={"meeting_id":mid,"user_id":"u2","text":"What is the planned migration date?","expertise":["db"]})
        client.post(f"/api/meetings/{mid}/process")
        related=client.get(f"/api/meetings/{mid}/questions/related",params={"viewer_user_id":"u1"})
        assert related.status_code==200
        body=client.post(f"/api/meetings/{mid}/process").json()
        cat=body["categories"][0]
        nominee=cat["nominees"][0]
        mod=client.post(f"/api/meetings/{mid}/moderate",json={"category_id":cat["category_id"],"action":"approve","nominee_id":nominee["nominee_id"],"moderator_user_id":"mod"})
        assert mod.status_code==200
        asked_id=mod.json()["asked_question_id"]
        evidence=client.get(f"/api/meetings/{mid}/evidence").json()
        assert evidence["summary"]["participants"]==2
        assert asked_id
        # The asked question must be the selected nominee, not an arbitrary raw question.
        from app.storage.db import SessionLocal, AskedQuestionRow
        with SessionLocal() as s:
            asked=s.get(AskedQuestionRow,asked_id)
            assert asked is not None
            assert asked.text==nominee["text"]


def test_coverage_endpoint_exposes_evidence_backed_signals():
    from fastapi.testclient import TestClient
    with TestClient(create_app()) as client:
        m=client.post('/api/meetings',json={'title':'Coverage','domain':'architecture','agenda':'review','manager_user_id':'mod'}).json()
        mid=m['id']
        assert client.post(f'/api/meetings/{mid}/participants',json={'user_id':'a','display_name':'A','expertise':['architecture','security']}).status_code==200
        assert client.post(f'/api/meetings/{mid}/participants',json={'user_id':'b','display_name':'B','expertise':['backend']}).status_code==200
        client.post('/api/questions',json={'meeting_id':mid,'user_id':'a','text':'What is the architecture risk?','expertise':['architecture']})
        body=client.get(f'/api/meetings/{mid}/coverage').json()
        assert 'security' in body['underrepresented']
        assert body['signals']


def test_readiness_endpoint_reports_degraded_or_ready_without_crashing():
    from fastapi.testclient import TestClient
    with TestClient(create_app()) as client:
        r=client.get('/ready')
        assert r.status_code == 200
        body=r.json()
        assert body['app'] == 'MeetLens'
        assert isinstance(body['degraded'], bool)
        assert 'llm' in body
