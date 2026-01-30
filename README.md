# 🤖 Agents-Claude — Federal AI Compliance Agents

AI-powered compliance agents built with **Anthropic Claude** for federal AI policy analysis and advisory.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Claude](https://img.shields.io/badge/Claude-Anthropic-orange.svg)](https://www.anthropic.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

This repository contains intelligent agents designed to assist with federal AI compliance tasks:

- **Policy Analyzer** — Analyze and interpret federal AI policies with citations
- **Gap Analyzer** — Compare organizational practices against requirements
- **Compliance Researcher** — Multi-agent research on compliance topics
- **Report Generator** — Create compliance reports and roadmaps

Built with Claude's advanced reasoning capabilities for accurate, reliable compliance guidance.

## 🏛️ Use Cases

- **Federal Prime Contractors** navigating M-25-21, M-25-22, NIST AI RMF
- **AI Compliance Consultants** conducting assessments and gap analyses
- **Federal Agencies** implementing AI governance frameworks
- **Legal Teams** reviewing AI contract compliance

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/Obsidian757/agents-claude.git
cd agents-claude

# Set up environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Install dependencies
pip install -r requirements.txt

# Run the Policy Analyzer
python src/agents/policy_analyzer.py

# Or launch the Streamlit interface
streamlit run src/app.py
```

## 📋 Prerequisites

- Python 3.10 or higher
- Anthropic API key ([get one here](https://console.anthropic.com/settings/keys))
- Optional: OpenAI API key (for embeddings)

## 🛠️ Agents

### Policy Analyzer

Analyze specific federal AI policies with step-by-step reasoning:

```python
from src.agents.policy_analyzer import PolicyAnalyzer

analyzer = PolicyAnalyzer()
result = analyzer.analyze(
    question="What are the Chief AI Officer requirements under M-25-21?",
    policy="M-25-21"
)

print(result.answer)
print(result.citations)
```

### Gap Analyzer

Compare your organization's practices against federal requirements:

```python
from src.agents.gap_analyzer import GapAnalyzer

analyzer = GapAnalyzer()
gaps = analyzer.analyze(
    current_practices=your_practices_document,
    requirements="M-25-22"
)

for gap in gaps:
    print(f"{gap.severity}: {gap.description}")
```

### Compliance Researcher

Multi-agent research for complex compliance questions:

```python
from src.agents.compliance_researcher import ComplianceResearcher

researcher = ComplianceResearcher()
report = researcher.research(
    topic="AI acquisition requirements for DOD contracts"
)

print(report.summary)
print(report.sources)
```

## 📁 Project Structure

```
agents-claude/
├── src/
│   ├── agents/              # Agent implementations
│   │   ├── policy_analyzer.py
│   │   ├── gap_analyzer.py
│   │   ├── compliance_researcher.py
│   │   └── report_generator.py
│   ├── tools/               # Tools for agents
│   │   ├── federal_policy_rag.py
│   │   ├── web_search.py
│   │   └── document_parser.py
│   ├── workflows/           # Multi-agent workflows
│   │   ├── compliance_assessment.py
│   │   └── implementation_roadmap.py
│   ├── utils/               # Utilities
│   │   └── config.py
│   ├── app.py              # Streamlit interface
│   └── cli.py              # Command-line interface
├── data/
│   ├── policies/           # Policy documents
│   └── templates/          # Report templates
├── tests/                  # Test suite
├── notebooks/              # Jupyter demos
├── docs/                   # Documentation
├── requirements.txt
├── .env.example
└── README.md
```

## 🔗 Integration with Federal-AI-Policy-RAG

These agents can integrate with your [federal-ai-policy-rag](https://github.com/Obsidian757/federal-ai-policy-rag) knowledge base:

```python
from src.tools.federal_policy_rag import FederalPolicyRAGTool

rag_tool = FederalPolicyRAGTool(
    vector_db_path="path/to/federal-ai-policy-rag/data/chroma_db"
)

# Use in any agent
analyzer = PolicyAnalyzer(tools=[rag_tool])
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific agent tests
pytest tests/test_policy_analyzer.py
```

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 🏛️ Related Projects

- [federal-ai-policy-rag](https://github.com/Obsidian757/federal-ai-policy-rag) — RAG-based policy Q&A tool
- [12th-house-ai](https://github.com/Obsidian757/12th-house-ai) — Federal AI compliance consulting website

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/Obsidian757/agents-claude/issues)
- **Email:** info@12thhouseai.com

---

*Built with 🤖 Claude by 12th House AI*
