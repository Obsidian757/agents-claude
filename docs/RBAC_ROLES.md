# Enterprise AI System — RBAC Role Draft

This draft defines a baseline set of roles and access expectations for an enterprise AI platform that includes model management, data governance, safety, monitoring, and end-user workflows. Organizations should tailor the roles and responsibilities to their governance model and regulatory obligations.

## Role catalog

### 1) Platform Owner
**Purpose:** Executive accountability for the AI platform’s outcomes, risk posture, and investment.

**Typical responsibilities**
- Define business objectives and success metrics for AI adoption.
- Approve platform roadmap and risk appetite.
- Sponsor cross-functional governance decisions.

**Access scope**
- Read-only access to all dashboards and governance artifacts.
- Approval authority for role assignments to high-privilege roles (e.g., Security Admin).

---

### 2) AI Governance Lead
**Purpose:** Operational leadership of AI policy, compliance, and risk management.

**Typical responsibilities**
- Maintain AI policies, standards, and approval workflows.
- Coordinate audits and regulatory reporting.
- Review high-risk model deployments.

**Access scope**
- Read/write access to governance workflows, policy artifacts, and audit logs.
- Approval gates for high-risk deployments.

---

### 3) Security Administrator
**Purpose:** Security hardening, identity integration, and incident response.

**Typical responsibilities**
- Configure authentication, SSO, MFA, and key management.
- Maintain security controls and monitor threat indicators.
- Lead incident response and breach notification procedures.

**Access scope**
- Full access to security settings, secrets management, and incident tooling.
- Read-only access to model/usage analytics for threat monitoring.

---

### 4) Data Governance Steward
**Purpose:** Ensure data quality, lineage, and access controls for AI data assets.

**Typical responsibilities**
- Classify datasets and manage data retention policies.
- Approve access to sensitive data and enforce data minimization.
- Maintain data lineage documentation.

**Access scope**
- Read/write access to data catalogs, classification labels, and retention policies.
- Approval for dataset access requests.

---

### 5) Model Risk Manager
**Purpose:** Validate model risk, bias, robustness, and alignment to policy.

**Typical responsibilities**
- Define model risk assessments and acceptance criteria.
- Review bias, safety, and performance evaluations.
- Require remediation plans for risky models.

**Access scope**
- Read/write access to model risk assessments and evaluation reports.
- Approval for model promotion to production.

---

### 6) AI Platform Administrator
**Purpose:** Operate and maintain the AI platform infrastructure.

**Typical responsibilities**
- Manage compute resources, deployments, and service health.
- Configure platform-level integrations and quotas.
- Maintain backup, DR, and service reliability targets.

**Access scope**
- Full administrative access to platform settings and infrastructure.
- Limited access to customer data content (metadata only).

---

### 7) Model Developer
**Purpose:** Build, fine-tune, and evaluate AI models.

**Typical responsibilities**
- Create training pipelines and evaluate model performance.
- Document model cards, data sources, and training assumptions.
- Collaborate with risk and governance reviewers.

**Access scope**
- Read/write access to development environments, model registries, and evaluation tools.
- Access to approved datasets only (no policy overrides).

---

### 8) MLOps Engineer
**Purpose:** Automate deployment, monitoring, and lifecycle operations for models.

**Typical responsibilities**
- Build CI/CD pipelines for models and prompts.
- Configure monitoring and alerting for drift and performance.
- Manage rollback and versioning strategies.

**Access scope**
- Read/write access to deployment pipelines, monitoring tools, and model registry.
- No access to restricted datasets beyond what pipelines require.

---

### 9) Application Engineer
**Purpose:** Integrate AI capabilities into business applications.

**Typical responsibilities**
- Implement API integrations and prompt orchestration.
- Configure feature flags and experimentation.
- Define fallback behavior and user experience safeguards.

**Access scope**
- Read/write access to application integrations and sandbox environments.
- Read-only access to production telemetry.

---

### 10) Prompt Designer
**Purpose:** Curate prompts, tools, and workflows that align with policy.

**Typical responsibilities**
- Create prompt libraries and templates.
- Define system instructions and safety constraints.
- Collaborate with governance to validate prompt behavior.

**Access scope**
- Read/write access to prompt repositories and testing sandboxes.
- No direct access to production data.

---

### 11) Business Analyst
**Purpose:** Measure business impact and user outcomes from AI features.

**Typical responsibilities**
- Define success metrics and experiment plans.
- Analyze usage, cost, and adoption trends.
- Provide requirements for new AI capabilities.

**Access scope**
- Read-only access to analytics dashboards and aggregated usage data.

---

### 12) Support Specialist
**Purpose:** Provide user support and triage incidents related to AI outputs.

**Typical responsibilities**
- Respond to user tickets and gather reproducible cases.
- Escalate issues to engineering or risk teams.
- Communicate workarounds and resolutions.

**Access scope**
- Read-only access to user logs relevant to support cases.
- Limited access to content with privacy controls.

---

### 13) End User
**Purpose:** Consume AI capabilities for daily tasks.

**Typical responsibilities**
- Use AI features in accordance with policy and training.
- Report issues or unsafe outputs.

**Access scope**
- Access to approved AI applications and functionality only.

## Cross-cutting permission notes
- **Segregation of duties:** High-privilege roles (Security Admin, AI Platform Admin) should be separated from model approval roles (Model Risk Manager, Governance Lead).
- **Least privilege:** Grant access at the minimum scope required; avoid default access to sensitive datasets.
- **Auditability:** All role assignments and approvals should be logged and periodically reviewed.
- **Temporary access:** Use time-bound access for investigations and break-glass workflows.

## Example approval flow
1. Model Developer submits a model for review.
2. Model Risk Manager reviews evaluation reports and requests updates.
3. AI Governance Lead reviews policy alignment and grants deployment approval.
4. MLOps Engineer deploys the approved model to production.
5. Security Administrator and AI Platform Administrator monitor for incidents.
