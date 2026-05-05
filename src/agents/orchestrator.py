"""
Orchestrator Agent - Autonomous Agentic Workflow Coordinator

Coordinates PolicyAnalyzer, GapAnalyzer, ComplianceResearcher, and ReportGenerator
in an autonomous pipeline. Supports:
  - Sequential and parallel async execution
  - Confidence-based routing and escalation
  - Persistent workflow state
  - SAM.gov / RFP document intake
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import anthropic

from ..utils.config import Config
from .policy_analyzer import PolicyAnalyzer
from .gap_analyzer import GapAnalyzer
from .report_generator import ReportGenerator
from .compliance_researcher import ComplianceResearcher


# ---------------------------------------------------------------------------
# Enums & Data Contracts
# ---------------------------------------------------------------------------

class WorkflowStatus(str, Enum):
    PENDING   = "pending"
    RUNNING   = "running"
    ESCALATED = "escalated"   # low-confidence path
    COMPLETE  = "complete"
    FAILED    = "failed"


class AgentRole(str, Enum):
    POLICY_ANALYZER      = "PolicyAnalyzer"
    GAP_ANALYZER         = "GapAnalyzer"
    COMPLIANCE_RESEARCHER = "ComplianceResearcher"
    REPORT_GENERATOR     = "ReportGenerator"
    ORCHESTRATOR         = "Orchestrator"


@dataclass
class AgentMessage:
    """Structured handoff contract between agents."""
    sender: AgentRole
    recipient: AgentRole
    payload: Dict[str, Any]
    confidence: str = "Medium"   # High | Medium | Low
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class WorkflowState:
    """Persistent workflow state — survives Streamlit reruns or process restarts."""
    workflow_id: str
    client_name: str
    intake: Dict[str, Any]                  # raw intake payload
    status: WorkflowStatus = WorkflowStatus.PENDING
    messages: List[Dict] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def save(self, state_dir: str = "./workflow_states") -> str:
        """Persist state to JSON file. Returns file path."""
        Path(state_dir).mkdir(parents=True, exist_ok=True)
        path = Path(state_dir) / f"{self.workflow_id}.json"
        self.updated_at = datetime.utcnow().isoformat()
        with open(path, "w") as f:
            data = asdict(self)
            data["status"] = self.status.value
            json.dump(data, f, indent=2)
        return str(path)

    @classmethod
    def load(cls, workflow_id: str, state_dir: str = "./workflow_states") -> "WorkflowState":
        """Load persisted state from JSON file."""
        path = Path(state_dir) / f"{workflow_id}.json"
        with open(path) as f:
            data = json.load(f)
        data["status"] = WorkflowStatus(data["status"])
        return cls(**data)


@dataclass
class OrchestratorResult:
    """Final output of a full agentic workflow run."""
    workflow_id: str
    client_name: str
    policy_analysis: Optional[Any] = None
    research_report: Optional[Any] = None
    gap_analysis: Optional[Any] = None
    compliance_report: Optional[Any] = None
    escalated: bool = False
    status: WorkflowStatus = WorkflowStatus.COMPLETE
    errors: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class Orchestrator:
    """
    Autonomous multi-agent workflow coordinator.

    Workflow (default):
      1. Parse & classify intake (client description + practices)
      2. Run PolicyAnalyzer + ComplianceResearcher IN PARALLEL (async)
      3. Confidence check — if Low, escalate to deeper research before continuing
      4. Run GapAnalyzer with enriched context from steps 2-3
      5. Run ReportGenerator with gap results
      6. Persist final WorkflowState and return OrchestratorResult

    Usage::

        orch = Orchestrator(api_key="sk-ant-...")

        # Full autonomous run
        result = await orch.run(
            client_name="Acme Federal IT",
            org_description="200-person DOD contractor...",
            current_practices="No CAIO, 3 AI systems in prod...",
            target_requirements=["M-25-21", "M-25-22", "NIST AI RMF"],
            report_type="full"
        )

        # Or from a raw RFP/SAM.gov document text
        result = await orch.run_from_rfp(
            client_name="Acme Federal IT",
            rfp_text="...solicitation text..."
        )
    """

    CONFIDENCE_ESCALATION_THRESHOLD = "Low"  # trigger deep research if at or below

    def __init__(self, api_key: Optional[str] = None, state_dir: str = "./workflow_states"):
        self.api_key   = api_key or Config.ANTHROPIC_API_KEY
        self.state_dir = state_dir
        if not self.api_key:
            raise ValueError("Anthropic API key required")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model  = Config.CLAUDE_MODEL

        # Instantiate all agents once — reused across workflow steps
        self._policy_agent    = PolicyAnalyzer(api_key=self.api_key)
        self._gap_agent       = GapAnalyzer(api_key=self.api_key)
        self._report_agent    = ReportGenerator(api_key=self.api_key)
        self._research_agent  = ComplianceResearcher(api_key=self.api_key)

    # ------------------------------------------------------------------
    # Public entrypoints
    # ------------------------------------------------------------------

    async def run(
        self,
        client_name: str,
        org_description: str,
        current_practices: str,
        target_requirements: Optional[List[str]] = None,
        report_type: str = "full",
        research_depth: str = "standard",
    ) -> OrchestratorResult:
        """
        Execute the full agentic compliance workflow.

        Args:
            client_name:          Human-readable client identifier
            org_description:      Free-text description of the organization
            current_practices:    Description of current AI practices
            target_requirements:  Policies to assess against (default: M-25-21, M-25-22, NIST AI RMF)
            report_type:          'full' | 'executive' | 'technical'
            research_depth:       'quick' | 'standard' | 'comprehensive'

        Returns:
            OrchestratorResult
        """
        start = datetime.utcnow()
        target_requirements = target_requirements or ["M-25-21", "M-25-22", "NIST AI RMF"]

        workflow_id = str(uuid.uuid4())[:8]
        state = WorkflowState(
            workflow_id=workflow_id,
            client_name=client_name,
            intake={
                "org_description": org_description,
                "current_practices": current_practices,
                "target_requirements": target_requirements,
                "report_type": report_type,
            },
            status=WorkflowStatus.RUNNING,
        )
        state.save(self.state_dir)

        result = OrchestratorResult(
            workflow_id=workflow_id,
            client_name=client_name,
        )

        try:
            # ----------------------------------------------------------
            # STEP 1: Classify & enrich intake
            # ----------------------------------------------------------
            primary_question = self._build_primary_question(
                org_description, current_practices, target_requirements
            )
            self._log(state, AgentRole.ORCHESTRATOR, "Intake classified. Dispatching parallel agents.")

            # ----------------------------------------------------------
            # STEP 2: PolicyAnalyzer + ComplianceResearcher in PARALLEL
            # ----------------------------------------------------------
            policy_task   = asyncio.to_thread(
                self._policy_agent.analyze, primary_question
            )
            research_task = asyncio.to_thread(
                self._research_agent.research,
                primary_question,
                research_depth,
                ["Governance", "Acquisition", "Risk Management"]
            )

            policy_result, research_result = await asyncio.gather(
                policy_task, research_task
            )

            result.policy_analysis  = policy_result
            result.research_report  = research_result

            self._log(
                state, AgentRole.POLICY_ANALYZER,
                f"Policy analysis complete. Confidence: {policy_result.confidence}"
            )
            self._log(
                state, AgentRole.COMPLIANCE_RESEARCHER,
                f"Research complete. Findings: {len(research_result.findings)}"
            )

            # ----------------------------------------------------------
            # STEP 3: Confidence-based routing
            # ----------------------------------------------------------
            if policy_result.confidence == self.CONFIDENCE_ESCALATION_THRESHOLD:
                state.status = WorkflowStatus.ESCALATED
                state.save(self.state_dir)
                self._log(
                    state, AgentRole.ORCHESTRATOR,
                    "Low confidence detected — escalating to comprehensive deep research."
                )
                research_result = await asyncio.to_thread(
                    self._research_agent.research,
                    primary_question,
                    "comprehensive",
                    None
                )
                result.research_report = research_result
                result.escalated = True

            # ----------------------------------------------------------
            # STEP 4: GapAnalyzer — enriched with research context
            # ----------------------------------------------------------
            enriched_practices = self._enrich_practices(
                current_practices, research_result
            )
            target_str = ", ".join(target_requirements)

            gap_result = await asyncio.to_thread(
                self._gap_agent.analyze,
                org_description,
                enriched_practices,
                target_str
            )
            result.gap_analysis = gap_result

            self._log(
                state, AgentRole.GAP_ANALYZER,
                f"Gap analysis complete. Score: {gap_result.overall_score}/100. "
                f"Critical gaps: {gap_result.critical_count}"
            )

            # ----------------------------------------------------------
            # STEP 5: ReportGenerator
            # ----------------------------------------------------------
            compliance_report = await asyncio.to_thread(
                self._report_agent.generate_compliance_report,
                gap_result,
                client_name,
                report_type
            )
            result.compliance_report = compliance_report

            self._log(
                state, AgentRole.REPORT_GENERATOR,
                f"Report generated: {compliance_report.title}"
            )

            state.status   = WorkflowStatus.COMPLETE
            state.results  = {
                "policy_confidence":    policy_result.confidence,
                "gap_score":           gap_result.overall_score,
                "critical_gaps":       gap_result.critical_count,
                "research_findings":   len(research_result.findings),
                "escalated":           result.escalated,
                "report_title":        compliance_report.title,
            }
            state.save(self.state_dir)

        except Exception as exc:
            result.status = WorkflowStatus.FAILED
            result.errors.append(str(exc))
            state.status = WorkflowStatus.FAILED
            state.errors.append(str(exc))
            state.save(self.state_dir)
            raise

        result.status           = WorkflowStatus.COMPLETE
        result.duration_seconds = (datetime.utcnow() - start).total_seconds()
        return result

    async def run_from_rfp(
        self,
        client_name: str,
        rfp_text: str,
        report_type: str = "full",
    ) -> OrchestratorResult:
        """
        Intake a raw SAM.gov solicitation or RFP document and run the full workflow.

        The orchestrator uses Claude to extract org context and AI requirements
        from the document before dispatching the standard workflow.

        Args:
            client_name:  Client identifier
            rfp_text:     Full text of the solicitation / RFP document
            report_type:  'full' | 'executive' | 'technical'

        Returns:
            OrchestratorResult
        """
        parsed = self._parse_rfp(rfp_text)
        return await self.run(
            client_name=client_name,
            org_description=parsed.get("org_description", "Federal contractor (parsed from RFP)"),
            current_practices=parsed.get("current_practices", "Not specified in solicitation"),
            target_requirements=parsed.get("requirements", ["M-25-21", "M-25-22", "NIST AI RMF"]),
            report_type=report_type,
            research_depth="comprehensive",
        )

    def resume(self, workflow_id: str) -> WorkflowState:
        """Load a previously saved workflow state."""
        return WorkflowState.load(workflow_id, self.state_dir)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_primary_question(
        self,
        org_description: str,
        current_practices: str,
        target_requirements: List[str]
    ) -> str:
        reqs = ", ".join(target_requirements)
        return (
            f"What are the key {reqs} compliance requirements for an organization described as: "
            f"{org_description[:300]}? Current practices: {current_practices[:300]}"
        )

    def _enrich_practices(
        self,
        current_practices: str,
        research_result: Any
    ) -> str:
        """Append top research findings to current practices for richer gap analysis."""
        top_findings = sorted(
            research_result.findings,
            key=lambda f: f.relevance_score,
            reverse=True
        )[:5]
        enrichment = " | ".join(
            f"{f.topic}: {f.finding[:120]}" for f in top_findings
        )
        return f"{current_practices}\n\n[Research context: {enrichment}]"

    def _parse_rfp(self, rfp_text: str) -> Dict:
        """Use Claude to extract org context and AI requirements from an RFP document."""
        prompt = f"""Extract compliance-relevant information from this federal solicitation:

{rfp_text[:6000]}

Return JSON:
{{
    "org_description": "description of the contractor requirements",
    "current_practices": "any specified AI/IT practices or constraints",
    "requirements": ["list of AI policy references found, e.g. M-25-21"]
}}"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        try:
            text = response.content[0].text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            return json.loads(text.strip())
        except Exception:
            return {}

    def _log(
        self,
        state: WorkflowState,
        sender: AgentRole,
        message: str
    ) -> None:
        """Append a log entry to the workflow state and save."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "sender":    sender.value,
            "message":   message,
        }
        state.messages.append(entry)
        state.save(self.state_dir)
        print(f"[{sender.value}] {message}")
