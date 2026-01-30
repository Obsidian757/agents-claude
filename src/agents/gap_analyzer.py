"""
Gap Analyzer Agent

Compares organizational practices against federal compliance requirements.
Identifies gaps, severity levels, and remediation priorities.
"""

import json
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

import anthropic

from ..utils.config import Config


class Severity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ComplianceGap:
    """Individual compliance gap"""
    id: str
    requirement: str
    current_state: str
    gap_description: str
    severity: Severity
    regulation: str
    deadline: Optional[str]
    remediation_steps: List[str]
    estimated_effort: str  # e.g., "2-4 weeks"
    estimated_cost: str    # e.g., "$5K-$10K"


@dataclass
class GapAnalysisResult:
    """Complete gap analysis result"""
    organization: str
    analysis_date: str
    overall_score: int  # 0-100
    compliance_level: str  # "Critical", "At Risk", "Moderate", "Compliant"
    gaps: List[ComplianceGap]
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    priority_actions: List[str]
    timeline_estimate: str
    summary: str


class GapAnalyzer:
    """
    Agent for analyzing compliance gaps.
    
    Compares current organizational practices against federal requirements
    and identifies specific gaps with remediation guidance.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Config.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("Anthropic API key required")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = Config.CLAUDE_MODEL
        self.max_tokens = Config.CLAUDE_MAX_TOKENS
    
    def analyze(
        self,
        organization_description: str,
        current_practices: str,
        target_requirements: str,
        context: Optional[str] = None
    ) -> GapAnalysisResult:
        """
        Perform gap analysis.
        
        Args:
            organization_description: Brief description of the organization
            current_practices: Description of current AI governance practices
            target_requirements: Target compliance requirements (M-25-21, M-25-22, etc.)
            context: Additional context
            
        Returns:
            GapAnalysisResult with detailed gap analysis
        """
        
        system_prompt = self._build_system_prompt()
        user_message = self._build_user_message(
            organization_description,
            current_practices,
            target_requirements,
            context
        )
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        
        return self._parse_response(response.content[0].text)
    
    def analyze_from_assessment(
        self,
        assessment_answers: dict,
        organization_type: str = "federal_contractor"
    ) -> GapAnalysisResult:
        """
        Analyze gaps from assessment questionnaire answers.
        
        Args:
            assessment_answers: Dict of question_id -> answer_value
            organization_type: Type of organization
            
        Returns:
            GapAnalysisResult
        """
        # Convert assessment answers to current practices description
        current_practices = self._assessment_to_practices(assessment_answers)
        
        # Determine target requirements based on answers
        target_requirements = self._determine_requirements(assessment_answers)
        
        return self.analyze(
            organization_description=f"{organization_type} organization",
            current_practices=current_practices,
            target_requirements=target_requirements
        )
    
    def _build_system_prompt(self) -> str:
        return """You are an expert federal AI compliance gap analyst.

Your role is to compare an organization's current practices against federal AI compliance requirements and identify specific gaps.

REQUIREMENTS:
1. Analyze each requirement systematically
2. Compare against current practices described
3. Identify specific gaps with evidence
4. Assign severity based on risk and regulatory importance
5. Provide actionable remediation steps
6. Estimate effort and cost for each gap

SEVERITY LEVELS:
- CRITICAL: Legal/regulatory violation, immediate action required
- HIGH: Significant compliance risk, address within 30 days
- MEDIUM: Moderate risk, address within 90 days
- LOW: Minor gap, address within 6 months

RESPONSE FORMAT:
Return JSON with this structure:
{
    "overall_score": 45,
    "compliance_level": "At Risk",
    "summary": "brief overall assessment",
    "gaps": [
        {
            "id": "GAP-001",
            "requirement": "specific requirement text",
            "current_state": "what org currently does",
            "gap_description": "what's missing",
            "severity": "CRITICAL|HIGH|MEDIUM|LOW",
            "regulation": "M-25-21 Section X",
            "deadline": "2025-06-01 or null",
            "remediation_steps": ["step 1", "step 2"],
            "estimated_effort": "2-4 weeks",
            "estimated_cost": "$5K-$10K"
        }
    ],
    "priority_actions": ["action 1", "action 2"],
    "timeline_estimate": "6 months to full compliance",
    "critical_count": 2,
    "high_count": 3,
    "medium_count": 4,
    "low_count": 1
}"""
    
    def _build_user_message(
        self,
        org_desc: str,
        current_practices: str,
        target_requirements: str,
        context: Optional[str]
    ) -> str:
        parts = [
            f"ORGANIZATION: {org_desc}",
            f"\nCURRENT PRACTICES:\n{current_practices}",
            f"\nTARGET REQUIREMENTS:\n{target_requirements}"
        ]
        
        if context:
            parts.append(f"\nADDITIONAL CONTEXT:\n{context}")
        
        parts.append("\nPerform a comprehensive gap analysis and return results in the specified JSON format.")
        
        return "\n".join(parts)
    
    def _parse_response(self, response_text: str) -> GapAnalysisResult:
        """Parse Claude's JSON response"""
        try:
            # Extract JSON
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
            else:
                json_str = response_text
            
            data = json.loads(json_str.strip())
            
            # Parse gaps
            gaps = []
            for gap_data in data.get("gaps", []):
                gap = ComplianceGap(
                    id=gap_data.get("id", "UNKNOWN"),
                    requirement=gap_data.get("requirement", ""),
                    current_state=gap_data.get("current_state", ""),
                    gap_description=gap_data.get("gap_description", ""),
                    severity=Severity(gap_data.get("severity", "MEDIUM").lower()),
                    regulation=gap_data.get("regulation", ""),
                    deadline=gap_data.get("deadline"),
                    remediation_steps=gap_data.get("remediation_steps", []),
                    estimated_effort=gap_data.get("estimated_effort", "TBD"),
                    estimated_cost=gap_data.get("estimated_cost", "TBD")
                )
                gaps.append(gap)
            
            return GapAnalysisResult(
                organization="Analyzed Organization",
                analysis_date="2025-01-30",
                overall_score=data.get("overall_score", 0),
                compliance_level=data.get("compliance_level", "Unknown"),
                gaps=gaps,
                critical_count=data.get("critical_count", 0),
                high_count=data.get("high_count", 0),
                medium_count=data.get("medium_count", 0),
                low_count=data.get("low_count", 0),
                priority_actions=data.get("priority_actions", []),
                timeline_estimate=data.get("timeline_estimate", ""),
                summary=data.get("summary", "")
            )
            
        except Exception as e:
            # Return error result
            return GapAnalysisResult(
                organization="Error",
                analysis_date="2025-01-30",
                overall_score=0,
                compliance_level="Error",
                gaps=[],
                critical_count=0,
                high_count=0,
                medium_count=0,
                low_count=0,
                priority_actions=[f"Error parsing response: {e}"],
                timeline_estimate="",
                summary="Error occurred during analysis"
            )
    
    def _assessment_to_practices(self, answers: dict) -> str:
        """Convert assessment answers to practices description"""
        # This would map assessment answers to practice descriptions
        # Simplified version
        practices = []
        
        if "q1" in answers:
            score = int(answers["q1"])
            if score >= 2:
                practices.append("Organization uses AI systems in federal contracts")
            else:
                practices.append("Limited AI use in federal contracts")
        
        if "q2" in answers:
            score = int(answers["q2"])
            if score >= 2:
                practices.append("Has designated AI governance lead")
            else:
                practices.append("No formal AI governance lead designated")
        
        return "\n".join(practices) if practices else "Limited information provided"
    
    def _determine_requirements(self, answers: dict) -> str:
        """Determine which requirements apply based on assessment"""
        requirements = ["M-25-21", "M-25-22", "NIST AI RMF"]
        return ", ".join(requirements)
    
    def generate_report_markdown(self, result: GapAnalysisResult) -> str:
        """Generate a markdown report from gap analysis"""
        lines = [
            f"# Gap Analysis Report",
            f"",
            f"**Organization:** {result.organization}",
            f"**Analysis Date:** {result.analysis_date}",
            f"**Overall Score:** {result.overall_score}/100",
            f"**Compliance Level:** {result.compliance_level}",
            f"",
            f"## Executive Summary",
            f"",
            result.summary,
            f"",
            f"## Gap Summary",
            f"",
            f"- 🔴 Critical: {result.critical_count}",
            f"- 🟠 High: {result.high_count}",
            f"- 🟡 Medium: {result.medium_count}",
            f"- 🟢 Low: {result.low_count}",
            f"",
            f"**Estimated Timeline:** {result.timeline_estimate}",
            f"",
            f"## Detailed Gaps",
            f""
        ]
        
        for gap in result.gaps:
            severity_emoji = {
                Severity.CRITICAL: "🔴",
                Severity.HIGH: "🟠",
                Severity.MEDIUM: "🟡",
                Severity.LOW: "🟢"
            }.get(gap.severity, "⚪")
            
            lines.extend([
                f"### {severity_emoji} {gap.id}: {gap.requirement[:60]}...",
                f"",
                f"**Severity:** {gap.severity.value.upper()}",
                f"**Regulation:** {gap.regulation}",
                f"",
                f"**Current State:** {gap.current_state}",
                f"",
                f"**Gap:** {gap.gap_description}",
                f"",
                f"**Remediation Steps:**"
            ])
            
            for step in gap.remediation_steps:
                lines.append(f"- {step}")
            
            lines.extend([
                f"",
                f"**Effort:** {gap.estimated_effort} | **Cost:** {gap.estimated_cost}",
                f""
            ])
        
        lines.extend([
            f"## Priority Actions",
            f""
        ])
        
        for i, action in enumerate(result.priority_actions, 1):
            lines.append(f"{i}. {action}")
        
        lines.append(f"")
        
        return "\n".join(lines)


if __name__ == "__main__":
    import sys
    
    print("🏛️  Federal AI Compliance Gap Analyzer")
    print("=" * 50)
    
    try:
        analyzer = GapAnalyzer()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Example usage
    org_desc = input("Organization description: ")
    print("\nDescribe current AI practices (end with blank line):")
    
    practices_lines = []
    while True:
        line = input()
        if not line:
            break
        practices_lines.append(line)
    
    current_practices = "\n".join(practices_lines)
    
    target = input("\nTarget requirements (e.g., M-25-21, M-25-22): ")
    
    print("\n🔍 Analyzing gaps...\n")
    
    result = analyzer.analyze(org_desc, current_practices, target)
    
    print(f"Overall Score: {result.overall_score}/100")
    print(f"Compliance Level: {result.compliance_level}")
    print(f"\nGaps Found:")
    print(f"  🔴 Critical: {result.critical_count}")
    print(f"  🟠 High: {result.high_count}")
    print(f"  🟡 Medium: {result.medium_count}")
    print(f"  🟢 Low: {result.low_count}")
    
    print(f"\nTop Priority Actions:")
    for action in result.priority_actions[:5]:
        print(f"  • {action}")
