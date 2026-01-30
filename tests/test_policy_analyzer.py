"""
Tests for Policy Analyzer Agent
"""

import os
import pytest
from unittest.mock import Mock, patch

from src.agents.policy_analyzer import PolicyAnalyzer, PolicyAnalysisResult


class TestPolicyAnalyzer:
    """Test suite for PolicyAnalyzer"""
    
    def test_initialization_requires_api_key(self):
        """Test that initialization requires API key"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': ''}):
            with pytest.raises(ValueError, match="Anthropic API key required"):
                PolicyAnalyzer()
    
    def test_initialization_with_api_key(self):
        """Test successful initialization with API key"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            analyzer = PolicyAnalyzer()
            assert analyzer.api_key == 'test-key'
    
    def test_initialization_with_explicit_key(self):
        """Test initialization with explicit API key parameter"""
        analyzer = PolicyAnalyzer(api_key='explicit-key')
        assert analyzer.api_key == 'explicit-key'
    
    def test_build_system_prompt(self):
        """Test system prompt construction"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            analyzer = PolicyAnalyzer()
            prompt = analyzer._build_system_prompt()
            
            assert "federal AI compliance" in prompt.lower()
            assert "M-25-21" in prompt
            assert "M-25-22" in prompt
            assert "NIST AI RMF" in prompt
            assert "JSON" in prompt
    
    def test_build_user_message_basic(self):
        """Test user message with just question"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            analyzer = PolicyAnalyzer()
            message = analyzer._build_user_message("Test question?", None, None)
            
            assert "Test question?" in message
            assert "QUESTION:" in message
    
    def test_build_user_message_with_policy(self):
        """Test user message with policy focus"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            analyzer = PolicyAnalyzer()
            message = analyzer._build_user_message("Test?", "M-25-21", None)
            
            assert "FOCUS POLICY: M-25-21" in message
    
    def test_build_user_message_with_context(self):
        """Test user message with context"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            analyzer = PolicyAnalyzer()
            message = analyzer._build_user_message("Test?", None, "Context info")
            
            assert "CONTEXT: Context info" in message
    
    def test_parse_response_valid_json(self):
        """Test parsing valid JSON response"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            analyzer = PolicyAnalyzer()
            
            valid_json = """{
                "reasoning_steps": ["Step 1", "Step 2"],
                "answer": "Test answer",
                "citations": [{"source": "M-25-21", "section": "III.A", "quote": "test"}],
                "confidence": "High",
                "related_policies": ["M-25-22"],
                "recommendations": ["Rec 1"]
            }"""
            
            result = analyzer._parse_response("Test question?", valid_json)
            
            assert isinstance(result, PolicyAnalysisResult)
            assert result.question == "Test question?"
            assert result.answer == "Test answer"
            assert result.confidence == "High"
            assert len(result.citations) == 1
            assert len(result.recommendations) == 1
    
    def test_parse_response_with_code_block(self):
        """Test parsing JSON inside markdown code block"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            analyzer = PolicyAnalyzer()
            
            code_block_json = """```json
            {
                "reasoning_steps": ["Step 1"],
                "answer": "Answer",
                "citations": [],
                "confidence": "Medium",
                "related_policies": [],
                "recommendations": []
            }
            ```"""
            
            result = analyzer._parse_response("Q?", code_block_json)
            
            assert result.answer == "Answer"
            assert result.confidence == "Medium"
    
    def test_parse_response_invalid_json(self):
        """Test fallback for invalid JSON"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            analyzer = PolicyAnalyzer()
            
            invalid_response = "This is not JSON"
            result = analyzer._parse_response("Q?", invalid_response)
            
            assert result.answer == "This is not JSON"
            assert result.confidence == "Unknown"
    
    @patch('src.agents.policy_analyzer.anthropic.Anthropic')
    def test_analyze_integration(self, mock_anthropic):
        """Test full analyze flow with mocked API"""
        # Setup mock
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text='{"reasoning_steps": [], "answer": "Test", "citations": [], "confidence": "High", "related_policies": [], "recommendations": []}')]
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client
        
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            analyzer = PolicyAnalyzer()
            analyzer.client = mock_client
            
            result = analyzer.analyze("What is M-25-21?")
            
            assert result.answer == "Test"
            assert result.confidence == "High"
            mock_client.messages.create.assert_called_once()


class TestPolicyAnalysisResult:
    """Test PolicyAnalysisResult dataclass"""
    
    def test_dataclass_creation(self):
        """Test creating result object"""
        result = PolicyAnalysisResult(
            question="Test?",
            answer="Answer",
            citations=[{"source": "M-25-21"}],
            reasoning_steps=["Step 1"],
            confidence="High",
            related_policies=["M-25-22"],
            recommendations=["Do this"]
        )
        
        assert result.question == "Test?"
        assert result.confidence == "High"
