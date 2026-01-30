"""
Compliance Researcher - Multi-Agent System

Orchestrates multiple agents for complex compliance research tasks.
Uses a planner-executor pattern with specialized sub-agents.
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Optional

import anthropic

from ..utils.config import Config


@dataclass
class ResearchFinding:
    """Individual research finding"""
    topic: str
    finding: str
    source: str
    confidence: str
    relevance_score: int  # 1-10


@dataclass
class ResearchReport:
    """Complete research report"""
    query: str
    summary: str
    findings: List[ResearchFinding]
    sources: List[Dict]
    gaps: List[str]  # Information gaps identified
    recommendations: List[str]
    confidence: str
    generated_at: str


class ComplianceResearcher:
    """
    Multi-agent compliance research system.
    
    Breaks complex research tasks into sub-tasks and coordinates
    multiple specialized agents:
    - Policy Finder: Locates relevant policy documents
    - Requirement Extractor: Extracts specific requirements
    - Cross-Reference Agent: Compares related policies
    - Synthesizer: Combines findings into coherent report
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or Config.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("Anthropic API key required")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = Config.CLAUDE_MODEL
        self.max_tokens = Config.CLAUDE_MAX_TOKENS
    
    def research(
        self,
        query: str,
        depth: str = "comprehensive",  # 'quick', 'standard', 'comprehensive'
        focus_areas: Optional[List[str]] = None
    ) -> ResearchReport:
        """
        Perform multi-agent compliance research.
        
        Args:
            query: Research question or topic
            depth: Research depth level
            focus_areas: Specific areas to focus on
            
        Returns:
            ResearchReport with comprehensive findings
        """
        
        # Step 1: Plan the research
        research_plan = self._plan_research(query, depth, focus_areas)
        
        # Step 2: Execute research tasks
        findings = self._execute_research(research_plan)
        
        # Step 3: Synthesize results
        report = self._synthesize_findings(query, findings, research_plan)
        
        return report
    
    def compare_policies(
        self,
        policy1: str,
        policy2: str,
        aspect: Optional[str] = None
    ) -> Dict:
        """
        Compare two policies for similarities, differences, and conflicts.
        
        Args:
            policy1: First policy (e.g., "M-25-21")
            policy2: Second policy (e.g., "M-25-22")
            aspect: Specific aspect to compare (e.g., "acquisition")
            
        Returns:
            Comparison results
        """
        
        prompt = f"""Compare {policy1} and {policy2}{f" on {aspect}" if aspect else ""}.

Analyze for:
1. Similar requirements
2. Conflicting requirements
3. Complementary guidance
4. Implementation implications

Return JSON:
{
    "similarities": ["similar req 1"],
    "differences": ["different req 1"],
    "conflicts": [{"topic": "x", "policy1_view": "y", "policy2_view": "z", "resolution": "how to reconcile"}],
    "complementary": ["how they work together"],
    "recommendations": ["practical guidance"]
}"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            text = response.content[0].text
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0]
            else:
                json_str = text
            
            return json.loads(json_str.strip())
        except:
            return {"error": "Failed to parse comparison", "raw": response.content[0].text}
    
    def find_precedents(
        self,
        scenario: str,
        agency: Optional[str] = None
    ) -> List[Dict]:
        """
        Find precedent cases or examples for a compliance scenario.
        
        Args:
            scenario: Description of the scenario
            agency: Specific agency to focus on
            
        Returns:
            List of precedent cases
        """
        
        agency_context = f" for {agency}" if agency else ""
        
        prompt = f"""Find precedent cases{agency_context} related to this scenario:

SCENARIO: {scenario}

Look for:
1. Published agency guidance
2. Known implementation examples
3. GAO reports or audits
4. Industry best practices

Return as JSON list of precedents with relevance scores."""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            text = response.content[0].text
            # Try to extract JSON list
            if "[" in text and "]" in text:
                json_str = text[text.find("["):text.rfind("]")+1]
                return json.loads(json_str)
            return []
        except:
            return []
    
    def _plan_research(
        self,
        query: str,
        depth: str,
        focus_areas: Optional[List[str]]
    ) -> Dict:
        """Plan research tasks"""
        
        prompt = f"""Create a research plan for this compliance query:

QUERY: {query}
DEPTH: {depth}
{f"FOCUS AREAS: {', '.join(focus_areas)}" if focus_areas else ""}

Create a research plan with:
1. Sub-questions to investigate
2. Relevant policies to review
3. Research approach for each

Return JSON:
{
    "sub_questions": ["question 1", "question 2"],
    "policies_to_review": ["M-25-21", "NIST AI RMF"],
    "approach": "methodology description",
    "tasks": [
        {"agent": "PolicyFinder", "task": "find X"},
        {"agent": "RequirementExtractor", "task": "extract Y"}
    ]
}"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            text = response.content[0].text
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0]
            else:
                json_str = text
            
            return json.loads(json_str.strip())
        except:
            return {
                "sub_questions": [query],
                "policies_to_review": ["M-25-21", "M-25-22", "NIST AI RMF"],
                "approach": "Direct research",
                "tasks": []
            }
    
    def _execute_research(self, plan: Dict) -> List[ResearchFinding]:
        """Execute research tasks"""
        
        findings = []
        
        # Simulate sub-agent execution
        for task in plan.get("tasks", []):
            # In a full implementation, this would dispatch to actual sub-agents
            # For now, we'll do a single comprehensive query
            pass
        
        # Comprehensive research query
        research_prompt = f"""Research this compliance topic comprehensively:

PLAN: {json.dumps(plan, indent=2)}

Execute the research and provide findings with:
1. Specific facts and requirements
2. Source citations
3. Confidence levels
4. Relevance scores

Return as JSON list of findings:
[
    {
        "topic": "topic name",
        "finding": "specific finding with details",
        "source": "document and section",
        "confidence": "High|Medium|Low",
        "relevance_score": 9
    }
]"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": research_prompt}]
        )
        
        try:
            text = response.content[0].text
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0]
            else:
                json_str = text
            
            findings_data = json.loads(json_str.strip())
            
            for finding_data in findings_data:
                findings.append(ResearchFinding(
                    topic=finding_data.get("topic", ""),
                    finding=finding_data.get("finding", ""),
                    source=finding_data.get("source", ""),
                    confidence=finding_data.get("confidence", "Medium"),
                    relevance_score=finding_data.get("relevance_score", 5)
                ))
        except:
            pass
        
        return findings
    
    def _synthesize_findings(
        self,
        query: str,
        findings: List[ResearchFinding],
        plan: Dict
    ) -> ResearchReport:
        """Synthesize findings into final report"""
        
        synthesis_prompt = f"""Synthesize these research findings into a comprehensive report:

ORIGINAL QUERY: {query}

FINDINGS:
{json.dumps([{
    'topic': f.topic,
    'finding': f.finding,
    'source': f.source,
    'confidence': f.confidence,
    'relevance': f.relevance_score
} for f in findings], indent=2)}

Create a synthesis with:
1. Executive summary
2. Key findings organized by topic
3. Information gaps
4. Actionable recommendations
5. Source list

Return JSON:
{
    "summary": "executive summary",
    "key_findings": ["organized finding 1"],
    "gaps": ["information not found"],
    "recommendations": ["action 1"],
    "confidence": "High|Medium|Low",
    "sources": [{"title": "doc", "relevance": "why"}]
}"""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": synthesis_prompt}]
        )
        
        try:
            text = response.content[0].text
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0]
            else:
                json_str = text
            
            data = json.loads(json_str.strip())
            
            return ResearchReport(
                query=query,
                summary=data.get("summary", ""),
                findings=findings,
                sources=data.get("sources", []),
                gaps=data.get("gaps", []),
                recommendations=data.get("recommendations", []),
                confidence=data.get("confidence", "Medium"),
                generated_at="2025-01-30"
            )
        except:
            return ResearchReport(
                query=query,
                summary="Error synthesizing findings",
                findings=findings,
                sources=[],
                gaps=["Synthesis failed"],
                recommendations=["Retry research"],
                confidence="Low",
                generated_at="2025-01-30"
            )


if __name__ == "__main__":
    import sys
    
    print("🔬 Compliance Researcher - Multi-Agent System")
    print("=" * 50)
    
    try:
        researcher = ComplianceResearcher()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    query = input("Research query: ")
    depth = input("Depth (quick/standard/comprehensive) [comprehensive]: ").strip() or "comprehensive"
    
    print(f"\n🔍 Conducting {depth} research...\n")
    
    report = researcher.research(query, depth)
    
    print(f"Research Complete!")
    print(f"Confidence: {report.confidence}")
    print(f"Findings: {len(report.findings)}")
    print(f"\nSummary:\n{report.summary}")
    
    if report.gaps:
        print(f"\n⚠️ Information Gaps:")
        for gap in report.gaps:
            print(f"  • {gap}")
    
    if report.recommendations:
        print(f"\n💡 Recommendations:")
        for rec in report.recommendations:
            print(f"  • {rec}")
