"""
SAM.gov Webhook Trigger Server

Listens for SAM.gov opportunity notifications (or any HTTP POST with solicitation
data) and automatically fires the full Orchestrator agentic workflow.

Setup:
    pip install fastapi uvicorn httpx apscheduler
    uvicorn src.webhook.samgov_webhook:app --host 0.0.0.0 --port 8080

Environment variables:
    ANTHROPIC_API_KEY   — required
    SAMGOV_API_KEY      — required for SAM.gov polling
    WEBHOOK_SECRET      — optional shared secret for request validation
    NOTIFY_EMAIL        — optional email address for completion notifications
    STATE_DIR           — path for workflow state persistence (default: ./workflow_states)

Endpoints:
    POST /webhook/solicitation  — receive a solicitation payload and run workflow
    POST /webhook/samgov        — SAM.gov-formatted opportunity notification
    GET  /workflow/{id}         — get status of a running/completed workflow
    GET  /health                — health check
    POST /poll/samgov           — manually trigger a SAM.gov poll
"""

import asyncio
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..agents import Orchestrator, WorkflowStatus

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Agents-Claude SAM.gov Webhook",
    description="Autonomous compliance workflow trigger for SAM.gov solicitations",
    version="1.0.0",
)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
SAMGOV_API_KEY    = os.getenv("SAMGOV_API_KEY", "")
WEBHOOK_SECRET   = os.getenv("WEBHOOK_SECRET", "")
STATE_DIR         = os.getenv("STATE_DIR", "./workflow_states")

# In-memory job registry (swap for Redis/SQLite in production)
_jobs: Dict[str, Dict] = {}


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class SolicitationPayload(BaseModel):
    """Generic solicitation payload — works for any source."""
    client_name: str
    solicitation_text: str
    report_type: Optional[str] = "full"
    notify_email: Optional[str] = None


class SamGovOpportunity(BaseModel):
    """SAM.gov opportunity notification schema."""
    noticeId: str
    title: str
    solicitationNumber: Optional[str] = None
    fullParentPathName: Optional[str] = None
    organizationName: Optional[str] = None
    description: Optional[str] = None
    naicsCode: Optional[str] = None
    classificationCode: Optional[str] = None
    active: Optional[str] = "Yes"
    type: Optional[str] = None
    postedDate: Optional[str] = None
    responseDeadLine: Optional[str] = None
    uiLink: Optional[str] = None
    # Additional fields passed through as-is
    extra: Optional[Dict[str, Any]] = None


class WorkflowStatusResponse(BaseModel):
    workflow_id: str
    status: str
    client_name: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    results: Optional[Dict] = None
    errors: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _verify_signature(body: bytes, signature: str) -> bool:
    """Verify HMAC-SHA256 webhook signature if WEBHOOK_SECRET is set."""
    if not WEBHOOK_SECRET:
        return True
    expected = hmac.new(
        WEBHOOK_SECRET.encode(), body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


def _register_job(workflow_id: str, client_name: str) -> None:
    _jobs[workflow_id] = {
        "workflow_id": workflow_id,
        "client_name": client_name,
        "status": WorkflowStatus.PENDING.value,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "results": None,
        "errors": [],
    }


def _update_job(workflow_id: str, status: WorkflowStatus, results=None, error=None):
    if workflow_id in _jobs:
        _jobs[workflow_id]["status"]     = status.value
        _jobs[workflow_id]["updated_at"] = datetime.utcnow().isoformat()
        if results:
            _jobs[workflow_id]["results"] = results
        if error:
            _jobs[workflow_id]["errors"].append(error)


async def _run_workflow_background(
    workflow_id: str,
    client_name: str,
    solicitation_text: str,
    report_type: str,
    notify_email: Optional[str],
) -> None:
    """Background task: run orchestrator and persist results."""
    _update_job(workflow_id, WorkflowStatus.RUNNING)
    try:
        orch = Orchestrator(api_key=ANTHROPIC_API_KEY, state_dir=STATE_DIR)
        result = await orch.run_from_rfp(
            client_name=client_name,
            rfp_text=solicitation_text,
            report_type=report_type,
        )
        summary = {
            "gap_score":         result.gap_analysis.overall_score if result.gap_analysis else None,
            "critical_gaps":     result.gap_analysis.critical_count if result.gap_analysis else None,
            "research_findings": len(result.research_report.findings) if result.research_report else 0,
            "escalated":         result.escalated,
            "duration_seconds":  result.duration_seconds,
            "report_title":      result.compliance_report.title if result.compliance_report else None,
        }
        _update_job(workflow_id, WorkflowStatus.COMPLETE, results=summary)

        # Optional email notification
        if notify_email:
            await _notify_email(notify_email, client_name, workflow_id, summary)

    except Exception as exc:
        _update_job(workflow_id, WorkflowStatus.FAILED, error=str(exc))
        raise


async def _notify_email(email: str, client_name: str, workflow_id: str, summary: Dict) -> None:
    """Send a simple completion notification via email (stub — wire to SendGrid/SES)."""
    # Replace this stub with your email provider SDK call
    print(
        f"[Notify] Workflow {workflow_id} for '{client_name}' complete. "
        f"Score: {summary.get('gap_score')}/100 | "
        f"Critical gaps: {summary.get('critical_gaps')} → {email}"
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.post("/webhook/solicitation", status_code=202)
async def receive_solicitation(
    payload: SolicitationPayload,
    background_tasks: BackgroundTasks,
    request: Request,
    x_webhook_signature: Optional[str] = Header(None),
):
    """
    Receive a solicitation payload and fire the full agentic workflow.

    Returns immediately with a workflow_id. Poll GET /workflow/{id} for status.
    """
    if x_webhook_signature:
        body = await request.body()
        if not _verify_signature(body, x_webhook_signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    # Generate workflow ID and register
    import uuid
    workflow_id = str(uuid.uuid4())[:8]
    _register_job(workflow_id, payload.client_name)

    background_tasks.add_task(
        _run_workflow_background,
        workflow_id=workflow_id,
        client_name=payload.client_name,
        solicitation_text=payload.solicitation_text,
        report_type=payload.report_type or "full",
        notify_email=payload.notify_email,
    )

    return {
        "accepted": True,
        "workflow_id": workflow_id,
        "status": WorkflowStatus.PENDING.value,
        "poll_url": f"/workflow/{workflow_id}",
        "message": f"Workflow queued for '{payload.client_name}'",
    }


@app.post("/webhook/samgov", status_code=202)
async def receive_samgov_opportunity(
    opportunity: SamGovOpportunity,
    background_tasks: BackgroundTasks,
    x_webhook_signature: Optional[str] = Header(None),
):
    """
    Receive a SAM.gov opportunity notification and auto-run the compliance workflow.

    SAM.gov does not natively push webhooks, but you can:
      1. Use a polling Lambda/cron that POSTs here when new notices are found
      2. Use the /poll/samgov endpoint to trigger a manual poll
      3. Subscribe to third-party SAM.gov notification services
    """
    if not ANTHROPIC_API_KEY:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not configured")

    # Build solicitation text from opportunity fields
    solicitation_text = f"""
Solicitation: {opportunity.title}
Notice ID: {opportunity.noticeId}
Solicitation Number: {opportunity.solicitationNumber or 'N/A'}
Organization: {opportunity.organizationName or opportunity.fullParentPathName or 'Federal Agency'}
NAICS Code: {opportunity.naicsCode or 'N/A'}
Posted: {opportunity.postedDate or 'N/A'}
Response Deadline: {opportunity.responseDeadLine or 'N/A'}
SAM.gov Link: {opportunity.uiLink or 'N/A'}

Description:
{opportunity.description or 'No description provided.'}
"""

    client_name = opportunity.organizationName or opportunity.title[:40]

    import uuid
    workflow_id = str(uuid.uuid4())[:8]
    _register_job(workflow_id, client_name)

    background_tasks.add_task(
        _run_workflow_background,
        workflow_id=workflow_id,
        client_name=client_name,
        solicitation_text=solicitation_text,
        report_type="executive",   # default to executive summary for RFP triage
        notify_email=os.getenv("NOTIFY_EMAIL"),
    )

    return {
        "accepted": True,
        "workflow_id": workflow_id,
        "notice_id": opportunity.noticeId,
        "client_name": client_name,
        "poll_url": f"/workflow/{workflow_id}",
    }


@app.get("/workflow/{workflow_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(workflow_id: str):
    """Poll the status of a workflow by its ID."""
    # Check in-memory registry first
    if workflow_id in _jobs:
        job = _jobs[workflow_id]
        return WorkflowStatusResponse(**job)

    # Fall back to persisted state file
    try:
        from ..agents import WorkflowState
        state = WorkflowState.load(workflow_id, STATE_DIR)
        return WorkflowStatusResponse(
            workflow_id=state.workflow_id,
            status=state.status.value,
            client_name=state.client_name,
            created_at=state.created_at,
            updated_at=state.updated_at,
            results=state.results,
            errors=state.errors,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")


@app.get("/workflows")
async def list_workflows():
    """List all in-memory tracked workflows."""
    return {"workflows": list(_jobs.values()), "count": len(_jobs)}


@app.post("/poll/samgov")
async def poll_samgov(
    background_tasks: BackgroundTasks,
    keywords: Optional[str] = "artificial intelligence",
    naics_code: Optional[str] = None,
    posted_from: Optional[str] = None,   # YYYY-MM-DD
    limit: int = 10,
):
    """
    Manually trigger a SAM.gov API poll for new AI-related solicitations.

    Requires SAMGOV_API_KEY environment variable.
    Qualifying opportunities are automatically queued as workflows.
    """
    if not SAMGOV_API_KEY:
        raise HTTPException(status_code=500, detail="SAMGOV_API_KEY not configured")

    background_tasks.add_task(
        _poll_samgov_background,
        keywords=keywords,
        naics_code=naics_code,
        posted_from=posted_from or (datetime.utcnow() - timedelta(days=1)).strftime("%m/%d/%Y"),
        limit=limit,
    )

    return {"message": "SAM.gov poll queued", "keywords": keywords, "limit": limit}


async def _poll_samgov_background(
    keywords: str,
    naics_code: Optional[str],
    posted_from: str,
    limit: int,
) -> None:
    """Background task: poll SAM.gov API and queue workflows for new opportunities."""
    params = {
        "api_key":    SAMGOV_API_KEY,
        "keyword":    keywords,
        "postedFrom": posted_from,
        "limit":      limit,
        "status":     "active",
    }
    if naics_code:
        params["naicsCode"] = naics_code

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.get(
                "https://api.sam.gov/opportunities/v2/search",
                params=params
            )
            response.raise_for_status()
            data = response.json()

            opportunities = data.get("opportunitiesData", [])
            print(f"[SAM.gov Poll] Found {len(opportunities)} opportunities for '{keywords}'")

            import uuid
            for opp in opportunities:
                notice_id = opp.get("noticeId", str(uuid.uuid4())[:8])
                client_name = opp.get("organizationName") or opp.get("title", "Unknown Agency")[:40]

                solicitation_text = f"""
Solicitation: {opp.get('title', 'N/A')}
Notice ID: {notice_id}
Organization: {client_name}
NAICS: {opp.get('naicsCode', 'N/A')}
Posted: {opp.get('postedDate', 'N/A')}
Deadline: {opp.get('responseDeadLine', 'N/A')}
Link: {opp.get('uiLink', 'N/A')}

Description:
{opp.get('description', 'No description available.')}
"""
                workflow_id = str(uuid.uuid4())[:8]
                _register_job(workflow_id, client_name)

                asyncio.create_task(_run_workflow_background(
                    workflow_id=workflow_id,
                    client_name=client_name,
                    solicitation_text=solicitation_text,
                    report_type="executive",
                    notify_email=os.getenv("NOTIFY_EMAIL"),
                ))

        except Exception as exc:
            print(f"[SAM.gov Poll] Error: {exc}")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.webhook.samgov_webhook:app", host="0.0.0.0", port=8080, reload=True)
