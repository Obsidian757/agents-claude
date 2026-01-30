"""
Report Generator Agent

Generates comprehensive compliance reports, roadmaps, and documentation.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

import anthropic

from ..utils.config import Config
from .gap_analyzer import GapAnalysisResult


@dataclass
class ComplianceReport:
    """Generated compliance report"""
    title: str
    executive_summary: str
    current_state: str
    findings: List[Dict]
    recommendations: List[Dict]
    roadmap: "ComplianceRoadmap"
    appendices: List[Dict]
    generated_at: str


@dataclass
class ComplianceRoadmap:
    """Implementation roadmap"""
    phases: List["RoadmapPhase"]
    total_duration: str
    total_budget: str
    milestones: List[Dict]


@dataclass
class RoadmapPhase:
    """Single phase of roadmap"""
    name: str
    duration: str
    tasks: List[Dict]
    deliverables: List[str]
    dependencies: List[str]


class ReportGenerator:
    """
    Agent for generating compliance reports and implementation roadmaps.
    
    Creates professional, client-ready documents including:
    - Compliance assessment reports
    - Implementation roadmaps
    - Executive summaries
    - Technical documentation
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Config.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("Anthropic API key required")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = Config.CLAUDE_MODEL
        self.max_tokens = Config.CLAUDE_MAX_TOKENS
    
    def generate_compliance_report(
        self,
        gap_analysis: GapAnalysisResult,
        organization_name: str,
        report_type: str = "full"
    ) -> ComplianceReport:
        """
        Generate comprehensive compliance report from gap analysis.
        
        Args:
            gap_analysis: Results from GapAnalyzer
            organization_name: Name of the organization
            report_type: 'full', 'executive', or 'technical'
            
        Returns:
            ComplianceReport object
        """
        
        system_prompt = self._build_report_prompt()
        
        user_message = f"""Generate a {report_type} compliance report for:

ORGANIZATION: {organization_name}

GAP ANALYSIS DATA:
- Overall Score: {gap_analysis.overall_score}/100
- Compliance Level: {gap_analysis.compliance_level}
- Critical Gaps: {gap_analysis.critical_count}
- High Gaps: {gap_analysis.high_count}
- Medium Gaps: {gap_analysis.medium_count}
- Low Gaps: {gap_analysis.low_count}
- Timeline Estimate: {gap_analysis.timeline_estimate}

DETAILED GAPS:
{json.dumps([{
    'id': g.id,
    'requirement': g.requirement,
    'severity': g.severity.value,
    'regulation': g.regulation,
    'remediation': g.remediation_steps
} for g in gap_analysis.gaps], indent=2)}

PRIORITY ACTIONS:
{json.dumps(gap_analysis.priority_actions, indent=2)}

Return the report in the specified JSON format."""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        
        return self._parse_report_response(response.content[0].text, organization_name)
    
    def generate_roadmap(
        self,
        gaps: List,
        constraints: Optional[Dict] = None
    ) -> ComplianceRoadmap:
        """
        Generate implementation roadmap from gaps.
        
        Args:
            gaps: List of compliance gaps
            constraints: Budget, timeline, resource constraints
            
        Returns:
            ComplianceRoadmap with phases and milestones
        """
        
        system_prompt = """You are an expert compliance implementation planner.

Create a practical implementation roadmap that:
1. Groups related tasks into phases
2. Respects dependencies (e.g., governance before assessment)
3. Considers resource constraints
4. Balances quick wins with foundational work
5. Provides realistic timelines

RESPONSE FORMAT:
{
    "phases": [
        {
            "name": "Phase 1: Foundation",
            "duration": "4-6 weeks",
            "tasks": [
                {"name": "task name", "effort": "1 week", "owner": "CAIO"}
            ],
            "deliverables": ["deliverable 1"],
            "dependencies": []
        }
    ],
    "total_duration": "6 months",
    "total_budget": "$50K-$75K",
    "milestones": [
        {"date": "Month 1", "milestone": "Governance established"}
    ]
}"""
        
        user_message = f"""Create an implementation roadmap for these compliance gaps:

GAPS:
{json.dumps([{
    'id': g.id,
    'severity': g.severity.value,
    'requirement': g.requirement[:100],
    'effort': g.estimated_effort,
    'cost': g.estimated_cost
} for g in gaps], indent=2)}

CONSTRAINTS:
{json.dumps(constraints or {}, indent=2)}

Return the roadmap in JSON format."""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        
        return self._parse_roadmap_response(response.content[0].text)
    
    def generate_executive_summary(
        self,
        gap_analysis: GapAnalysisResult,
        organization_name: str
    ) -> str:
        """Generate executive summary document"""
        
        prompt = f"""Write an executive summary for a federal AI compliance report.

ORGANIZATION: {organization_name}
OVERALL SCORE: {gap_analysis.overall_score}/100
COMPLIANCE LEVEL: {gap_analysis.compliance_level}
CRITICAL GAPS: {gap_analysis.critical_count}
HIGH GAPS: {gap_analysis.high_count}

Write a compelling 1-page executive summary that:
1. Opens with the bottom line (compliance status)
2. Highlights top 3 risks
3. Outlines recommended approach
4. States investment required
5. Ends with clear next steps

Use professional business language. Keep it under 500 words."""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    def _build_report_prompt(self) -> str:
        return """You are an expert compliance report writer.

Generate professional, client-ready compliance reports that include:
1. Executive summary (key findings, recommendations)
2. Current state assessment
3. Detailed findings with evidence
4. Prioritized recommendations
5. Implementation roadmap
6. Appendices (methodology, references)

RESPONSE FORMAT:
{
    "title": "AI Compliance Assessment Report",
    "executive_summary": "markdown text",
    "current_state": "markdown text",
    "findings": [
        {
            "category": "Governance",
            "finding": "description",
            "impact": "High",
            "evidence": "specific evidence"
        }
    ],
    "recommendations": [
        {
            "priority": 1,
            "recommendation": "action",
            "rationale": "why",
            "effort": "2-4 weeks",
            "investment": "$5K-$10K"
        }
    ],
    "roadmap": {
        "phases": [
            {
                "name": "Phase 1",
                "duration": "4-6 weeks",
                "tasks": [{"name": "task", "owner": "role"}],
                "deliverables": ["doc 1"]
            }
        ],
        "total_duration": "6 months",
        "total_budget": "$50K"
    },
    "appendices": [
        {"title": "Methodology", "content": "text"}
    ]
}"""
    
    def _parse_report_response(self, text: str, org_name: str) -> ComplianceReport:
        """Parse report JSON"""
        try:
            # Extract JSON
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0]
            else:
                json_str = text
            
            data = json.loads(json_str.strip())
            
            # Build roadmap
            roadmap_data = data.get("roadmap", {})
            phases = []
            for phase_data in roadmap_data.get("phases", []):
                phases.append(RoadmapPhase(
                    name=phase_data.get("name", ""),
                    duration=phase_data.get("duration", ""),
                    tasks=phase_data.get("tasks", []),
                    deliverables=phase_data.get("deliverables", []),
                    dependencies=phase_data.get("dependencies", [])
                ))
            
            roadmap = ComplianceRoadmap(
                phases=phases,
                total_duration=roadmap_data.get("total_duration", ""),
                total_budget=roadmap_data.get("total_budget", ""),
                milestones=roadmap_data.get("milestones", [])
            )
            
            return ComplianceReport(
                title=data.get("title", "Compliance Report"),
                executive_summary=data.get("executive_summary", ""),
                current_state=data.get("current_state", ""),
                findings=data.get("findings", []),
                recommendations=data.get("recommendations", []),
                roadmap=roadmap,
                appendices=data.get("appendices", []),
                generated_at=datetime.now().isoformat()
            )
            
        except Exception as e:
            return ComplianceReport(
                title="Error Generating Report",
                executive_summary=f"Error: {e}",
                current_state="",
                findings=[],
                recommendations=[],
                roadmap=ComplianceRoadmap([], "", "", []),
                appendices=[],
                generated_at=datetime.now().isoformat()
            )
    
    def _parse_roadmap_response(self, text: str) -> ComplianceRoadmap:
        """Parse roadmap JSON"""
        try:
            # Extract JSON
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0]
            else:
                json_str = text
            
            data = json.loads(json_str.strip())
            
            phases = []
            for phase_data in data.get("phases", []):
                phases.append(RoadmapPhase(
                    name=phase_data.get("name", ""),
                    duration=phase_data.get("duration", ""),
                    tasks=phase_data.get("tasks", []),
                    deliverables=phase_data.get("deliverables", []),
                    dependencies=phase_data.get("dependencies", [])
                ))
            
            return ComplianceRoadmap(
                phases=phases,
                total_duration=data.get("total_duration", ""),
                total_budget=data.get("total_budget", ""),
                milestones=data.get("milestones", [])
            )
            
        except Exception:
            return ComplianceRoadmap([], "", "", [])
    
    def export_to_markdown(self, report: ComplianceReport) -> str:
        """Export report to Markdown"""
        lines = [
            f"# {report.title}",
            f"",
            f"**Generated:** {report.generated_at}",
            f"",
            f"---",
            f"",
            f"## Executive Summary",
            f"",
            report.executive_summary,
            f"",
            f"## Current State",
            f"",
            report.current_state,
            f"",
            f"## Key Findings",
            f""
        ]
        
        for finding in report.findings:
            lines.extend([
                f"### {finding.get('category', 'Finding')}",
                f"",
                f"**Finding:** {finding.get('finding', '')}",
                f"",
                f"**Impact:** {finding.get('impact', '')}",
                f"",
                f"**Evidence:** {finding.get('evidence', '')}",
                f""
            ])
        
        lines.extend([
            f"## Recommendations",
            f""
        ])
        
        for rec in report.recommendations:
            lines.extend([
                f"### Priority {rec.get('priority', 0)}: {rec.get('recommendation', '')[:50]}",
                f"",
                f"{rec.get('recommendation', '')}",
                f"",
                f"**Rationale:** {rec.get('rationale', '')}",
                f"",
                f"**Effort:** {rec.get('effort', 'TBD')} | **Investment:** {rec.get('investment', 'TBD')}",
                f""
            ])
        
        lines.extend([
            f"## Implementation Roadmap",
            f"",
            f"**Total Duration:** {report.roadmap.total_duration}",
            f"**Total Budget:** {report.roadmap.total_budget}",
            f""
        ])
        
        for phase in report.roadmap.phases:
            lines.extend([
                f"### {phase.name}",
                f"",
                f"**Duration:** {phase.duration}",
                f"",
                f"**Tasks:**"
            ])
            
            for task in phase.tasks:
                lines.append(f"- {task.get('name', '')} ({task.get('effort', '')}) - Owner: {task.get('owner', '')}")
            
            lines.extend([
                f"",
                f"**Deliverables:**"
            ])
            
            for deliverable in phase.deliverables:
                lines.append(f"- {deliverable}")
            
            lines.append(f"")
        
        return "\n".join(lines)
