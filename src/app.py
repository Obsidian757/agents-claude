"""
Streamlit interface for Agents-Claude
Policy Analyzer with Claude
"""

import os
import sys

import streamlit as st

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.policy_analyzer import PolicyAnalyzer
from src.utils.config import Config

# Page configuration
st.set_page_config(
    page_title="Agents-Claude | Federal AI Policy Analyzer",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1e3a5f;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.25rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .confidence-high {
        background: #d1fae5;
        color: #065f46;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-weight: 600;
    }
    .confidence-medium {
        background: #fef3c7;
        color: #92400e;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-weight: 600;
    }
    .confidence-low {
        background: #fee2e2;
        color: #991b1b;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-weight: 600;
    }
    .citation-box {
        background: #f3f4f6;
        border-left: 3px solid #2563eb;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
    .recommendation-box {
        background: #f0fdf4;
        border-left: 3px solid #059669;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
    .reasoning-step {
        background: #eff6ff;
        border-left: 3px solid #3b82f6;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🏛️ Agents-Claude")
    st.markdown("**Federal AI Policy Analyzer**")
    st.markdown("---")
    
    # API Key input
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        value=os.getenv("ANTHROPIC_API_KEY", ""),
        help="Your Claude API key from console.anthropic.com"
    )
    
    if api_key:
        os.environ["ANTHROPIC_API_KEY"] = api_key
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("""
    This tool uses **Claude** (Anthropic's AI) to analyze federal AI compliance questions with:
    - Step-by-step reasoning
    - Document citations
    - Actionable recommendations
    """)
    
    st.markdown("---")
    st.markdown("### ⚠️ Disclaimer")
    st.markdown("This is an AI assistant. Always verify critical compliance decisions with legal counsel.")

# Main content
st.markdown('<h1 class="main-header">🏛️ Federal AI Policy Analyzer</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">AI-powered compliance analysis with Claude</p>', unsafe_allow_html=True)

# Check API key
if not api_key:
    st.error("⚠️ Please enter your Anthropic API key in the sidebar to continue.")
    st.stop()

# Initialize analyzer
@st.cache_resource
def get_analyzer():
    return PolicyAnalyzer(api_key=api_key)

try:
    analyzer = get_analyzer()
except Exception as e:
    st.error(f"Error initializing analyzer: {e}")
    st.stop()

# Quick questions
st.markdown("### 💡 Quick Questions")
quick_questions = [
    "What are the Chief AI Officer requirements under M-25-21?",
    "What does M-25-22 require for AI acquisition?",
    "How should agencies implement the NIST AI Risk Management Framework?",
    "What are the requirements for high-impact AI systems?",
    "What safety testing is required before AI deployment?",
    "What data ownership rights does M-25-22 address?"
]

cols = st.columns(2)
for i, question in enumerate(quick_questions):
    with cols[i % 2]:
        if st.button(question, use_container_width=True, key=f"quick_{i}"):
            st.session_state.question = question
            st.rerun()

# Input section
st.markdown("---")
st.markdown("### 🔍 Ask Your Compliance Question")

question = st.text_area(
    "Enter your question:",
    value=st.session_state.get("question", ""),
    height=100,
    placeholder="e.g., What are the CAO responsibilities for high-impact AI systems under M-25-21?"
)

policy_focus = st.selectbox(
    "Focus on specific policy (optional):",
    ["Auto-detect", "M-25-21", "M-25-22", "NIST AI RMF", "EO 14110", "M-22-09"],
    index=0
)

context = st.text_area(
    "Additional context (optional):",
    height=80,
    placeholder="e.g., We are a DOD contractor with 500 employees implementing AI for logistics..."
)

if st.button("🔍 Analyze with Claude", type="primary", use_container_width=True):
    if not question:
        st.warning("Please enter a question.")
    else:
        with st.spinner("🤖 Claude is analyzing..."):
            try:
                policy = None if policy_focus == "Auto-detect" else policy_focus
                result = analyzer.analyze(question, policy, context if context else None)
                
                # Store result in session state
                st.session_state.last_result = result
                
            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()

# Display results
if "last_result" in st.session_state:
    result = st.session_state.last_result
    
    st.markdown("---")
    st.markdown("### 📊 Analysis Results")
    
    # Confidence badge
    confidence_class = f"confidence-{result.confidence.lower()}"
    st.markdown(f"**Confidence:** <span class='{confidence_class}'>{result.confidence}</span>", unsafe_allow_html=True)
    
    # Reasoning steps
    if result.reasoning_steps:
        with st.expander("🧠 Reasoning Steps", expanded=True):
            for i, step in enumerate(result.reasoning_steps, 1):
                st.markdown(f'<div class="reasoning-step"><strong>Step {i}:</strong> {step}</div>', unsafe_allow_html=True)
    
    # Answer
    st.markdown("### 💡 Answer")
    st.markdown(result.answer)
    
    # Citations
    if result.citations:
        with st.expander("📚 Citations"):
            for citation in result.citations:
                st.markdown(f"""
                <div class="citation-box">
                    <strong>{citation.get('source', 'Unknown')}</strong> - {citation.get('section', '')}<br>
                    <em>"{citation.get('quote', '')}"</em>
                </div>
                """, unsafe_allow_html=True)
    
    # Recommendations
    if result.recommendations:
        st.markdown("### ✅ Recommendations")
        for rec in result.recommendations:
            st.markdown(f'<div class="recommendation-box">{rec}</div>', unsafe_allow_html=True)
    
    # Related policies
    if result.related_policies:
        st.markdown("### 🔗 Related Policies")
        st.write(", ".join(result.related_policies))

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280; font-size: 0.875rem;">
    <strong>Agents-Claude</strong> — Built with Anthropic Claude<br>
    Part of <a href="https://12thhouseai.com" target="_blank">12th House AI</a>
</div>
"", unsafe_allow_html=True)
