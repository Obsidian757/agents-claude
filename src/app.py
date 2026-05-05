"""
Streamlit interface for Agents-Claude
Multi-agent compliance analysis system
"""

import asyncio
import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents import (
    PolicyAnalyzer, GapAnalyzer, ReportGenerator, ComplianceResearcher,
    Orchestrator, WorkflowStatus
)
from src.utils.config import Config

st.set_page_config(
    page_title="Agents-Claude | Federal AI Compliance Suite",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: 700; color: #1e3a5f; margin-bottom: 0.5rem; }
    .sub-header { font-size: 1.25rem; color: #6b7280; margin-bottom: 2rem; }
    .agent-card { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 0.75rem; padding: 1.5rem; margin: 1rem 0; }
    .confidence-high { background: #d1fae5; color: #065f46; padding: 0.25rem 0.75rem; border-radius: 1rem; font-weight: 600; }
    .confidence-medium { background: #fef3c7; color: #92400e; padding: 0.25rem 0.75rem; border-radius: 1rem; font-weight: 600; }
    .confidence-low { background: #fee2e2; color: #991b1b; padding: 0.25rem 0.75rem; border-radius: 1rem; font-weight: 600; }
    .citation-box { background: #f3f4f6; border-left: 3px solid #2563eb; padding: 1rem; margin: 0.5rem 0; border-radius: 0.25rem; }
    .recommendation-box { background: #f0fdf4; border-left: 3px solid #059669; padding: 1rem; margin: 0.5rem 0; border-radius: 0.25rem; }
    .reasoning-step { background: #eff6ff; border-left: 3px solid #3b82f6; padding: 0.75rem 1rem; margin: 0.5rem 0; border-radius: 0.25rem; }
    .gap-critical { background: #fee2e2; border-left: 4px solid #dc2626; padding: 1rem; margin: 0.5rem 0; }
    .gap-high { background: #ffedd5; border-left: 4px solid #ea580c; padding: 1rem; margin: 0.5rem 0; }
    .gap-medium { background: #fef9c3; border-left: 4px solid #ca8a04; padding: 1rem; margin: 0.5rem 0; }
    .gap-low { background: #dcfce7; border-left: 4px solid #16a34a; padding: 1rem; margin: 0.5rem 0; }
    .workflow-step { background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 0.5rem; padding: 0.75rem 1rem; margin: 0.35rem 0; }
    .workflow-complete { background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 0.5rem; padding: 0.75rem 1rem; margin: 0.35rem 0; }
    .workflow-escalated { background: #fef9c3; border: 1px solid #fde047; border-radius: 0.5rem; padding: 0.75rem 1rem; margin: 0.35rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏛️ Agents-Claude")
    st.markdown("**Federal AI Compliance Suite**")
    st.markdown("---")
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        value=os.getenv("ANTHROPIC_API_KEY", ""),
        help="Your Claude API key from console.anthropic.com"
    )
    if api_key:
        os.environ["ANTHROPIC_API_KEY"] = api_key
    st.markdown("---")
    st.markdown("### 🤖 Available Agents")
    st.markdown("""
    1. **Policy Analyzer** — Analyze specific policies
    2. **Gap Analyzer** — Identify compliance gaps
    3. **Report Generator** — Create compliance reports
    4. **Compliance Researcher** — Multi-agent research
    5. **🆕 Auto-Workflow** — Full agentic pipeline
    """)
    st.markdown("---")
    st.markdown("### ⚠️ Disclaimer")
    st.markdown("AI-generated guidance. Verify critical decisions with legal counsel.")

st.markdown('<h1 class="main-header">🏛️ Federal AI Compliance Suite</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Multi-agent compliance analysis powered by Claude</p>', unsafe_allow_html=True)

if not api_key:
    st.error("⚠️ Please enter your Anthropic API key in the sidebar to continue.")
    st.stop()


@st.cache_resource
def get_agents():
    return {
        'policy':   PolicyAnalyzer(api_key=api_key),
        'gap':      GapAnalyzer(api_key=api_key),
        'report':   ReportGenerator(api_key=api_key),
        'research': ComplianceResearcher(api_key=api_key),
    }

try:
    agents = get_agents()
except Exception as e:
    st.error(f"Error initializing agents: {e}")
    st.stop()

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Policy Analyzer",
    "🔍 Gap Analyzer",
    "📊 Report Generator",
    "🔬 Compliance Researcher",
    "🤖 Auto-Workflow",
])

# ── Tab 1: Policy Analyzer ────────────────────────────────────────────────────
with tab1:
    st.markdown("### Analyze Federal AI Policies")
    st.markdown("Get detailed analysis of specific policy questions with citations and reasoning.")
    st.markdown("#### 💡 Quick Questions")
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
                st.session_state.policy_question = question
                st.rerun()
    st.markdown("---")
    question = st.text_area(
        "Your question:",
        value=st.session_state.get("policy_question", ""),
        height=100, key="policy_input"
    )
    policy_focus = st.selectbox(
        "Focus policy:",
        ["Auto-detect", "M-25-21", "M-25-22", "NIST AI RMF", "EO 14110", "M-22-09"],
        key="policy_focus"
    )
    if st.button("🔍 Analyze with Claude", type="primary", key="policy_btn"):
        if not question:
            st.warning("Please enter a question.")
        else:
            with st.spinner("🤖 Analyzing..."):
                try:
                    policy = None if policy_focus == "Auto-detect" else policy_focus
                    result = agents['policy'].analyze(question, policy)
                    st.session_state.policy_result = result
                except Exception as e:
                    st.error(f"Error: {e}")
    if "policy_result" in st.session_state:
        result = st.session_state.policy_result
        st.markdown("---")
        confidence_class = f"confidence-{result.confidence.lower()}"
        st.markdown(f"**Confidence:** <span class='{confidence_class}'>{result.confidence}</span>", unsafe_allow_html=True)
        if result.reasoning_steps:
            with st.expander("🧠 Reasoning Steps", expanded=True):
                for i, step in enumerate(result.reasoning_steps, 1):
                    st.markdown(f'<div class="reasoning-step"><strong>Step {i}:</strong> {step}</div>', unsafe_allow_html=True)
        st.markdown("### 💡 Answer")
        st.markdown(result.answer)
        if result.citations:
            with st.expander("📚 Citations"):
                for citation in result.citations:
                    st.markdown(f"""
                    <div class="citation-box">
                        <strong>{citation.get('source', 'Unknown')}</strong> - {citation.get('section', '')}<br>
                        <em>"{citation.get('quote', '')}"</em>
                    </div>
                    """, unsafe_allow_html=True)
        if result.recommendations:
            st.markdown("### ✅ Recommendations")
            for rec in result.recommendations:
                st.markdown(f'<div class="recommendation-box">{rec}</div>', unsafe_allow_html=True)

# ── Tab 2: Gap Analyzer ───────────────────────────────────────────────────────
with tab2:
    st.markdown("### Identify Compliance Gaps")
    st.markdown("Compare your current practices against federal requirements.")
    col1, col2 = st.columns(2)
    with col1:
        org_desc = st.text_area("Organization description:", height=100,
            placeholder="e.g., 200-person IT contractor supporting DOD and HHS...")
    with col2:
        current_practices = st.text_area("Current AI practices:", height=100,
            placeholder="e.g., We have informal AI governance, no CAIO yet, 3 AI systems in production...")
    target_requirements = st.multiselect(
        "Target requirements:",
        ["M-25-21", "M-25-22", "NIST AI RMF", "EO 14110", "DOD AI Strategy", "DHS AI Strategy"],
        default=["M-25-21", "M-25-22", "NIST AI RMF"]
    )
    if st.button("🔍 Analyze Gaps", type="primary", key="gap_btn"):
        if not org_desc or not current_practices:
            st.warning("Please fill in both fields.")
        else:
            with st.spinner("🤖 Analyzing gaps..."):
                try:
                    target = ", ".join(target_requirements)
                    result = agents['gap'].analyze(org_desc, current_practices, target)
                    st.session_state.gap_result = result
                except Exception as e:
                    st.error(f"Error: {e}")
    if "gap_result" in st.session_state:
        result = st.session_state.gap_result
        st.markdown("---")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: st.metric("Overall Score", f"{result.overall_score}/100")
        with col2: st.metric("Critical", result.critical_count)
        with col3: st.metric("High", result.high_count)
        with col4: st.metric("Medium", result.medium_count)
        with col5: st.metric("Low", result.low_count)
        st.markdown(f"**Compliance Level:** {result.compliance_level}")
        st.markdown(f"**Timeline Estimate:** {result.timeline_estimate}")
        with st.expander("📋 Summary", expanded=True):
            st.markdown(result.summary)
        st.markdown("### 🚨 Identified Gaps")
        for gap in result.gaps:
            severity_class = f"gap-{gap.severity.value}"
            st.markdown(f"""
            <div class="{severity_class}">
                <strong>{gap.id}</strong> - {gap.severity.value.upper()}<br>
                <strong>Requirement:</strong> {gap.requirement}<br>
                <strong>Gap:</strong> {gap.gap_description}<br>
                <strong>Remediation:</strong> {'; '.join(gap.remediation_steps[:2])}...<br>
                <em>Effort: {gap.estimated_effort} | Cost: {gap.estimated_cost}</em>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("### 🎯 Priority Actions")
        for action in result.priority_actions[:5]:
            st.markdown(f"- {action}")
        if st.button("📄 Export Markdown Report"):
            report_md = agents['gap'].generate_report_markdown(result)
            st.download_button(
                label="Download Report", data=report_md,
                file_name="gap_analysis_report.md", mime="text/markdown"
            )

# ── Tab 3: Report Generator ───────────────────────────────────────────────────
with tab3:
    st.markdown("### Generate Compliance Reports")
    st.markdown("Create professional, client-ready compliance reports and roadmaps.")
    if "gap_result" not in st.session_state:
        st.info("⚠️ First run a Gap Analysis to generate a report.")
    else:
        gap_result = st.session_state.gap_result
        org_name = st.text_input("Organization name:", value="Client Organization")
        report_type = st.selectbox("Report type:", ["full", "executive", "technical"])
        if st.button("📊 Generate Report", type="primary", key="report_btn"):
            with st.spinner("🤖 Generating report..."):
                try:
                    report = agents['report'].generate_compliance_report(gap_result, org_name, report_type)
                    st.session_state.report_result = report
                except Exception as e:
                    st.error(f"Error: {e}")
        if "report_result" in st.session_state:
            report = st.session_state.report_result
            st.markdown("---")
            st.markdown(f"### {report.title}")
            with st.expander("📄 Executive Summary", expanded=True):
                st.markdown(report.executive_summary)
            with st.expander("📋 Current State"):
                st.markdown(report.current_state)
            with st.expander("🗺️ Implementation Roadmap"):
                st.markdown(f"**Duration:** {report.roadmap.total_duration}")
                st.markdown(f"**Budget:** {report.roadmap.total_budget}")
                for phase in report.roadmap.phases:
                    st.markdown(f"**{phase.name}** ({phase.duration})")
                    for task in phase.tasks:
                        st.markdown(f"- {task.get('name', '')}")
            if st.button("📥 Export Full Report (Markdown)"):
                full_report = agents['report'].export_to_markdown(report)
                st.download_button(
                    label="Download Full Report", data=full_report,
                    file_name=f"{org_name.replace(' ', '_')}_compliance_report.md",
                    mime="text/markdown"
                )

# ── Tab 4: Compliance Researcher ─────────────────────────────────────────────
with tab4:
    st.markdown("### Multi-Agent Compliance Research")
    st.markdown("Deep research on complex compliance topics using multiple specialized agents.")
    research_query = st.text_area("Research query:", height=100,
        placeholder="e.g., How do M-25-21 and M-25-22 requirements overlap for AI acquisition?")
    col1, col2 = st.columns(2)
    with col1:
        research_depth = st.selectbox("Research depth:", ["quick", "standard", "comprehensive"], index=2)
    with col2:
        focus_areas = st.multiselect("Focus areas:",
            ["Governance", "Acquisition", "Risk Management", "Safety Testing", "Documentation"])
    if st.button("🔬 Start Research", type="primary", key="research_btn"):
        if not research_query:
            st.warning("Please enter a research query.")
        else:
            with st.spinner("🔬 Conducting multi-agent research... (this may take a moment)"):
                try:
                    report = agents['research'].research(research_query, research_depth,
                        focus_areas if focus_areas else None)
                    st.session_state.research_result = report
                except Exception as e:
                    st.error(f"Error: {e}")
    if "research_result" in st.session_state:
        report = st.session_state.research_result
        st.markdown("---")
        st.markdown(f"**Confidence:** {report.confidence} | **Findings:** {len(report.findings)}")
        with st.expander("📝 Summary", expanded=True):
            st.markdown(report.summary)
        st.markdown("### 📊 Key Findings")
        for finding in sorted(report.findings, key=lambda x: x.relevance_score, reverse=True)[:10]:
            st.markdown(f"""
            <div class="citation-box">
                <strong>{finding.topic}</strong> (Relevance: {finding.relevance_score}/10)<br>
                {finding.finding}<br>
                <em>Source: {finding.source}</em> | Confidence: {finding.confidence}
            </div>
            """, unsafe_allow_html=True)
        if report.gaps:
            with st.expander("⚠️ Information Gaps"):
                for gap in report.gaps:
                    st.markdown(f"- {gap}")
        if report.recommendations:
            st.markdown("### 💡 Recommendations")
            for rec in report.recommendations:
                st.markdown(f"- {rec}")
        st.markdown("---")
        st.markdown("### 🔄 Policy Comparison")
        st.markdown("Compare two policies side-by-side:")
        col1, col2 = st.columns(2)
        with col1:
            policy1 = st.selectbox("Policy 1:", ["M-25-21", "M-25-22", "NIST AI RMF", "EO 14110"], key="p1")
        with col2:
            policy2 = st.selectbox("Policy 2:", ["M-25-22", "M-25-21", "NIST AI RMF", "EO 14110"], key="p2")
        compare_aspect = st.text_input("Specific aspect (optional):", placeholder="e.g., acquisition, governance")
        if st.button("Compare Policies"):
            with st.spinner("Comparing policies..."):
                comparison = agents['research'].compare_policies(policy1, policy2, compare_aspect or None)
                if "error" not in comparison:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("#### Similarities")
                        for sim in comparison.get("similarities", []):
                            st.markdown(f"- {sim}")
                    with col2:
                        st.markdown("#### Differences")
                        for diff in comparison.get("differences", []):
                            st.markdown(f"- {diff}")
                    if comparison.get("conflicts"):
                        st.markdown("#### ⚠️ Conflicts")
                        for conflict in comparison["conflicts"]:
                            st.markdown(f"**{conflict.get('topic', '')}:**")
                            st.markdown(f"- {policy1}: {conflict.get('policy1_view', '')}")
                            st.markdown(f"- {policy2}: {conflict.get('policy2_view', '')}")
                            st.markdown(f"*Resolution: {conflict.get('resolution', '')}*")

# ── Tab 5: Auto-Workflow ─────────────────────────────────────────────────────
with tab5:
    st.markdown("### 🤖 Autonomous Agentic Workflow")
    st.markdown(
        "Runs the full compliance pipeline automatically: "
        "Policy Analysis → Research → Gap Analysis → Report — with confidence-based routing."
    )

    mode = st.radio(
        "Intake mode:",
        ["Manual Input", "RFP / SAM.gov Document"],
        horizontal=True,
        key="workflow_mode"
    )

    st.markdown("---")

    if mode == "Manual Input":
        wf_client_name = st.text_input("Client / Organization name:",
            placeholder="e.g., Acme Federal IT LLC", key="wf_client")
        col1, col2 = st.columns(2)
        with col1:
            wf_org_desc = st.text_area("Organization description:", height=120,
                placeholder="e.g., 200-person DOD contractor supporting DHA and HHS...",
                key="wf_org")
        with col2:
            wf_practices = st.text_area("Current AI practices:", height=120,
                placeholder="e.g., No CAIO, 3 AI systems in prod, informal governance...",
                key="wf_practices")
        wf_requirements = st.multiselect(
            "Target requirements:",
            ["M-25-21", "M-25-22", "NIST AI RMF", "EO 14110", "DOD AI Strategy", "DHS AI Strategy"],
            default=["M-25-21", "M-25-22", "NIST AI RMF"],
            key="wf_reqs"
        )
        col3, col4 = st.columns(2)
        with col3:
            wf_report_type = st.selectbox("Report type:", ["full", "executive", "technical"], key="wf_rtype")
        with col4:
            wf_depth = st.selectbox("Research depth:", ["quick", "standard", "comprehensive"],
                index=1, key="wf_depth")

        run_disabled = not (wf_client_name and wf_org_desc and wf_practices)
        if st.button("🚀 Run Full Workflow", type="primary", key="wf_run", disabled=run_disabled):
            st.session_state.wf_running = True
            st.session_state.wf_result  = None
            st.session_state.wf_error   = None

            progress = st.progress(0, text="Initializing workflow...")
            log_box  = st.empty()

            try:
                orch = Orchestrator(api_key=api_key)

                progress.progress(10, text="⚙️ Step 1/5 — Classifying intake...")
                log_box.info("🏁 Workflow started. Running Policy Analyzer + Compliance Researcher in parallel...")

                result = asyncio.run(orch.run(
                    client_name=wf_client_name,
                    org_description=wf_org_desc,
                    current_practices=wf_practices,
                    target_requirements=wf_requirements,
                    report_type=wf_report_type,
                    research_depth=wf_depth,
                ))

                progress.progress(100, text="✅ Workflow complete!")
                st.session_state.wf_result = result

            except Exception as exc:
                progress.empty()
                st.session_state.wf_error = str(exc)

    else:  # RFP mode
        wf_client_name = st.text_input("Client name:", placeholder="e.g., Acme Federal IT", key="wf_rfp_client")
        wf_rfp_text = st.text_area(
            "Paste SAM.gov solicitation or RFP text:", height=200,
            placeholder="Paste the full solicitation text here...",
            key="wf_rfp_text"
        )
        wf_report_type = st.selectbox("Report type:", ["full", "executive", "technical"], key="wf_rfp_rtype")

        if st.button("🚀 Analyze RFP & Run Workflow", type="primary", key="wf_rfp_run",
                     disabled=not (wf_client_name and wf_rfp_text)):
            progress = st.progress(0, text="Parsing RFP document...")
            try:
                orch = Orchestrator(api_key=api_key)
                progress.progress(15, text="📄 RFP parsed. Launching agentic pipeline...")
                result = asyncio.run(orch.run_from_rfp(
                    client_name=wf_client_name,
                    rfp_text=wf_rfp_text,
                    report_type=wf_report_type,
                ))
                progress.progress(100, text="✅ Workflow complete!")
                st.session_state.wf_result = result
            except Exception as exc:
                progress.empty()
                st.session_state.wf_error = str(exc)

    # ── Results display ──────────────────────────────────────────────────────
    if st.session_state.get("wf_error"):
        st.error(f"Workflow failed: {st.session_state.wf_error}")

    if st.session_state.get("wf_result"):
        result = st.session_state.wf_result

        st.markdown("---")

        # Status banner
        if result.escalated:
            st.markdown(
                '<div class="workflow-escalated">⚠️ <strong>Escalated</strong> — Low confidence detected; '
                'deep comprehensive research was automatically triggered before continuing.</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="workflow-complete">✅ <strong>Workflow Complete</strong></div>',
                unsafe_allow_html=True
            )

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            score = result.gap_analysis.overall_score if result.gap_analysis else "N/A"
            st.metric("Compliance Score", f"{score}/100")
        with col2:
            critical = result.gap_analysis.critical_count if result.gap_analysis else "N/A"
            st.metric("Critical Gaps", critical)
        with col3:
            findings = len(result.research_report.findings) if result.research_report else "N/A"
            st.metric("Research Findings", findings)
        with col4:
            st.metric("Duration", f"{result.duration_seconds:.1f}s")

        # Workflow log
        with st.expander("🗒️ Workflow Log", expanded=False):
            st.code(
                f"Workflow ID: {result.workflow_id}\n"
                f"Client: {result.client_name}\n"
                f"Status: {result.status.value}\n"
                f"Escalated: {result.escalated}\n"
                f"Duration: {result.duration_seconds:.1f}s"
            )

        # Policy analysis
        if result.policy_analysis:
            with st.expander("📋 Policy Analysis", expanded=False):
                pa = result.policy_analysis
                confidence_class = f"confidence-{pa.confidence.lower()}"
                st.markdown(f"**Confidence:** <span class='{confidence_class}'>{pa.confidence}</span>",
                    unsafe_allow_html=True)
                st.markdown(pa.answer)

        # Research report
        if result.research_report:
            with st.expander("🔬 Research Report", expanded=False):
                rr = result.research_report
                st.markdown(rr.summary)
                for finding in sorted(rr.findings, key=lambda x: x.relevance_score, reverse=True)[:5]:
                    st.markdown(f'<div class="citation-box"><strong>{finding.topic}</strong> '
                        f'({finding.relevance_score}/10)<br>{finding.finding}</div>',
                        unsafe_allow_html=True)

        # Gap analysis
        if result.gap_analysis:
            with st.expander("🔍 Gap Analysis", expanded=True):
                ga = result.gap_analysis
                st.markdown(ga.summary)
                for gap in ga.gaps:
                    sc = f"gap-{gap.severity.value}"
                    st.markdown(
                        f'<div class="{sc}"><strong>{gap.id}</strong> — {gap.severity.value.upper()}<br>'
                        f'{gap.gap_description}</div>', unsafe_allow_html=True
                    )

        # Compliance report
        if result.compliance_report:
            cr = result.compliance_report
            with st.expander("📊 Compliance Report", expanded=True):
                st.markdown(f"### {cr.title}")
                st.markdown(cr.executive_summary)

            # Export
            full_md = agents['report'].export_to_markdown(cr)
            st.download_button(
                label="📥 Download Full Report (Markdown)",
                data=full_md,
                file_name=f"{result.client_name.replace(' ', '_')}_compliance_report.md",
                mime="text/markdown"
            )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280; font-size: 0.875rem;">
    <strong>Agents-Claude</strong> — Multi-Agent Federal AI Compliance Suite<br>
    Part of <a href="https://12thhouseai.com" target="_blank">12th House AI</a>
</div>
""", unsafe_allow_html=True)
