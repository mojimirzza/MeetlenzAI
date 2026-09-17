from __future__ import annotations
import httpx
import gradio as gr
from app.core.config import get_settings

S = get_settings()
BASE = f"http://127.0.0.1:{S.port}"


def _json_or_error(response: httpx.Response):
    try:
        data = response.json()
    except Exception:
        data = {"error": response.text}
    if response.status_code >= 400:
        raise RuntimeError(f"HTTP {response.status_code}: {data}")
    return data


def create_meeting(title, domain, agenda, manager):
    r = httpx.post(
        f"{BASE}/api/meetings",
        json={"title": title, "domain": domain, "agenda": agenda, "manager_user_id": manager},
        timeout=30,
    )
    data = _json_or_error(r)
    return data["id"], f"Meeting created: {data['id']}"


def submit_question(meeting_id, user_id, text):
    if not meeting_id or not user_id or not text:
        return {"error": "meeting_id, user_id and question are required"}
    r = httpx.post(
        f"{BASE}/api/questions",
        json={"meeting_id": meeting_id, "user_id": user_id, "text": text},
        timeout=30,
    )
    return _json_or_error(r)


def run_pipeline_payload(meeting_id):
    if not meeting_id:
        return {"error": "meeting_id is required"}, ""
    r = httpx.post(f"{BASE}/api/meetings/{meeting_id}/process", timeout=120)
    data = _json_or_error(r)
    lines = []
    for i, c in enumerate(data.get("categories", []), 1):
        lines.append(f"### {i}. {c['label']} — priority {c['priority_score']:.3f}")
        lines.append(f"**Category ID:** `{c['category_id']}`")
        for n in c.get("nominees", []):
            lines.append(f"- `{n['nominee_id']}` — {n['text']}  ")
            lines.append(f"  quality={n['quality_score']:.2f} | rationale={n.get('rationale','')}")
    return data, "\n".join(lines) or "No categories yet."


def moderate(meeting_id, manager, category_id, action, nominee_id, edited, reason):
    payload = {
        "category_id": category_id,
        "action": action,
        "nominee_id": nominee_id or None,
        "edited_text": edited or None,
        "moderator_user_id": manager,
        "reason": reason or "",
    }
    r = httpx.post(f"{BASE}/api/meetings/{meeting_id}/moderate", json=payload, timeout=30)
    return _json_or_error(r)


def evidence(meeting_id):
    if not meeting_id:
        return {"error": "meeting_id is required"}
    r = httpx.get(f"{BASE}/api/meetings/{meeting_id}/evidence", timeout=30)
    return _json_or_error(r)


def coverage(meeting_id):
    if not meeting_id:
        return {"error": "meeting_id is required"}
    r = httpx.get(f"{BASE}/api/meetings/{meeting_id}/coverage", timeout=30)
    return _json_or_error(r)


def run_demo():
    return {
        "command": "python scripts/demo_pilot.py",
        "note": "Run this from the project root for the deterministic zero-cloud demo.",
    }


def build_ui():
    with gr.Blocks(title="MeetLens") as demo:
        gr.Markdown(
            "# MeetLens\n"
            "### Meeting Question Intelligence & Moderation\n"
            "**Many questions → fewer intents → diverse nominees → human decision → measurable outcome.**"
        )

        with gr.Tab("1. Start meeting"):
            title = gr.Textbox(label="Meeting title", value="Technical Architecture Review")
            domain = gr.Textbox(label="Domain", value="architecture")
            agenda = gr.Textbox(label="Agenda", lines=4, value="Migration, failover, release readiness")
            manager = gr.Textbox(label="Moderator user id", value="moderator")
            create = gr.Button("Create meeting", variant="primary")
            meeting_id = gr.Textbox(label="Meeting ID", interactive=False)
            status = gr.Textbox(label="Status", interactive=False)
            create.click(create_meeting, [title, domain, agenda, manager], [meeting_id, status])

        with gr.Tab("2. Submit question"):
            m2 = gr.Textbox(label="Meeting ID")
            uid = gr.Textbox(label="User ID", value="participant-1")
            q = gr.Textbox(label="Question", lines=4)
            out = gr.JSON()
            gr.Button("Submit", variant="primary").click(submit_question, [m2, uid, q], out)

        with gr.Tab("3. Moderate"):
            m3 = gr.Textbox(label="Meeting ID")
            mgr3 = gr.Textbox(label="Moderator user id", value="moderator")
            process = gr.Button("Run clustering + prioritization", variant="primary")
            structured = gr.JSON(label="Pipeline result")
            results = gr.Markdown(label="Nominees")
            process.click(run_pipeline_payload, [m3], [structured, results])

            gr.Markdown("### Human decision gate")
            category_id = gr.Textbox(label="Category ID")
            nominee_id = gr.Textbox(label="Nominee ID (required for approve/edit)")
            action = gr.Dropdown(["approve", "edit", "reject"], value="approve", label="Action")
            edited = gr.Textbox(label="Edited question (for edit)", lines=3)
            reason = gr.Textbox(label="Decision reason", lines=2)
            decide = gr.Button("Apply moderator decision", variant="primary")
            decision_result = gr.JSON(label="Decision result")
            decide.click(moderate, [m3, mgr3, category_id, action, nominee_id, edited, reason], decision_result)
            gr.Markdown("The server validates moderator identity, category membership, nominee membership, and lifecycle rules.")

        with gr.Tab("4. Evidence"):
            me = gr.Textbox(label="Meeting ID")
            ev = gr.JSON(label="Evidence report")
            gr.Button("Generate evidence", variant="primary").click(evidence, me, ev)

        with gr.Tab("5. Coverage / Blind Spot Radar"):
            mc = gr.Textbox(label="Meeting ID")
            cov = gr.JSON(label="Evidence-backed coverage signals")
            gr.Button("Analyze coverage", variant="primary").click(coverage, mc, cov)
            gr.Markdown("Signals are moderator aids based on declared expertise and submitted questions; they are not claims that a perspective is objectively required.")

        with gr.Tab("6. Demo / Reproduce"):
            gr.Markdown("## Zero-cloud deterministic demo")
            gr.Markdown("Run from the repository root:")
            gr.Code("python scripts/demo_pilot.py", language="shell")
            demo_info = gr.JSON(value=run_demo())

    return demo
