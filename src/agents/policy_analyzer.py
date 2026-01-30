"""
Policy Analyzer Agent

Analyzes federal AI policies using Claude with step-by-step reasoning.
Provides citations and actionable insights.
"""

import json
from dataclasses import dataclass
from typing import List, Optional

import anthropic

from ..utils.config import Config


@dataclass
class PolicyAnalysisResult:
    """Result of policy analysis"""
    question: str
    answer: str
    citations: List[dict]
    reasoning_steps: List[str]
    confidence: str
    related_policies: List[str]
    recommendations: List[str]


class PolicyAnalyzer:
    """
    Agent for analyzing federal AI policies with Claude.
    
    Features:
    - Step-by-step reasoning
    - Document citations
    - Confidence scoring
    - Related policy suggestions
    - Actionable recommendations
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Policy Analyzer.
        
        Args:
            api_key: Anthropic API key (defaults to Config.ANTHROPIC_API_KEY)
        """
        self.api_key = api_key or Config.ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("Anthropic API key required")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = Config.CLAUDE_MODEL
        self.max_tokens = Config.CLAUDE_MAX_TOKENS
    
    def analyze(
        self,
        question: str,
        policy: Optional[str] = None,
        context: Optional[str] = None
    ) -> PolicyAnalysisResult:
        """
        Analyze a policy question using Claude.
        
        Args:
            question: The compliance question to analyze
            policy: Specific policy to focus on (e.g., "M-25-21", "NIST AI RMF")
            context: Additional context about the organization or situation
            
        Returns:
            PolicyAnalysisResult with answer, citations, and recommendations
        """
        
        # Build the system prompt
        system_prompt = self._build_system_prompt()
        
        # Build the user message
        user_message = self._build_user_message(question, policy, context)
        
        # Call Claude
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        # Parse the response
        return self._parse_response(question, response.content[0].text)
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for policy analysis"""
        return """You are an expert federal AI compliance advisor specializing in:
- OMB M-25-21 (Accelerating Federal Use of AI)
- OMB M-25-22 (Driving Efficient AI Acquisition)
- NIST AI Risk Management Framework (AI 100-1)
- Executive Order 14110 (AI Safety and Security)
- Agency-specific AI strategies (DHS, DOE, CFPB, etc.)

Your role is to provide accurate, actionable compliance guidance based on official federal policy documents.

GUIDELINES:
1. Think step-by-step through the question
2. Cite specific sections, paragraphs, or requirements
3. Note confidence level (High/Medium/Low) based on document clarity
4. Suggest related policies that may be relevant
5. Provide concrete, actionable recommendations
6. If information is ambiguous, say so clearly
7. Never make up citations - only reference actual document content

RESPONSE FORMAT:
Return your response as a JSON object with this structure:
{
    "reasoning_steps": ["Step 1: ...", "Step 2: ...", "Step 3: ..."],
    "answer": "Your comprehensive answer with inline citations like [M-25-21, Section III.A]",
    "citations": [
        {"source": "M-25-21", "section": "Section III.A", "quote": "exact quote from document"}
    ],
    "confidence": "High|Medium|Low",
    "related_policies": ["M-25-22", "NIST AI RMF"],
    "recommendations": ["Specific action item 1", "Specific action item 2"]
}"""
    
    def _build_user_message(
        self,
        question: str,
        policy: Optional[str],
        context: Optional[str]
    ) -> str:
        """Build the user message with question and context"""
        message_parts = [f"QUESTION: {question}"]
        
        if policy:
            message_parts.append(f"\nFOCUS POLICY: {policy}")
        
        if context:
            message_parts.append(f"\nCONTEXT: {context}")
        
        message_parts.append("\nAnalyze this question and provide your response in the specified JSON format.")
        
        return "\n".join(message_parts)
    
    def _parse_response(self, question: str, response_text: str) -> PolicyAnalysisResult:
        """Parse Claude's JSON response"""
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
            else:
                json_str = response_text
            
            data = json.loads(json_str.strip())
            
            return PolicyAnalysisResult(
                question=question,
                answer=data.get("answer", ""),
                citations=data.get("citations", []),
                reasoning_steps=data.get("reasoning_steps", []),
                confidence=data.get("confidence", "Unknown"),
                related_policies=data.get("related_policies", []),
                recommendations=data.get("recommendations", [])
            )
        
        except json.JSONDecodeError as e:
            # Fallback if JSON parsing fails
            return PolicyAnalysisResult(
                question=question,
                answer=response_text,
                citations=[],
                reasoning_steps=["Response parsing error"],
                confidence="Unknown",
                related_policies=[],
                recommendations=["Please retry the question"]
            )
    
    def batch_analyze(
        self,
        questions: List[str],
        policy: Optional[str] = None
    ) -> List[PolicyAnalysisResult]:
        """
        Analyze multiple questions in batch.
        
        Args:
            questions: List of questions to analyze
            policy: Optional policy to focus on for all questions
            
        Returns:
            List of PolicyAnalysisResult objects
        """
        results = []
        for question in questions:
            result = self.analyze(question, policy)
            results.append(result)
        return results


# CLI interface
if __name__ == "__main__":
    import sys
    
    print("🏛️  Federal AI Policy Analyzer")
    print("=" * 50)
    
    try:
        analyzer = PolicyAnalyzer()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Example usage
    question = input("\nEnter your compliance question: ")
    policy = input("Specific policy (optional, e.g., M-25-21): ").strip() or None
    
    print("\n🔍 Analyzing...\n")
    
    result = analyzer.analyze(question, policy)
    
    print(f"\n{'=' * 50}")
    print(f"📊 CONFIDENCE: {result.confidence}")
    print(f"{'=' * 50}\n")
    
    print("🧠 REASONING:")
    for step in result.reasoning_steps:
        print(f"  • {step}")
    
    print(f"\n💡 ANSWER:\n{result.answer}\n")
    
    if result.citations:
        print("📚 CITATIONS:")
        for citation in result.citations:
            print(f"  • {citation['source']}, {citation['section']}")
    
    if result.recommendations:
        print("\n✅ RECOMMENDATIONS:")
        for rec in result.recommendations:
            print(f"  • {rec}")
    
    if result.related_policies:
        print(f"\n🔗 RELATED POLICIES: {', '.join(result.related_policies)}")
