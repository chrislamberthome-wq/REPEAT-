# Five-target discovery outreach package

**Status:** `NOT_CONTACTED` for every target  
**Market:** AI assurance / verification / evidence infrastructure  
**Geography:** U.S.-first; included non-U.S. targets where strategically relevant  
**Purpose:** Discovery only. This document tests whether the underlying evidence, provenance, verification, auditability, or claimed-state-transition problem exists. It is not a sales pitch.

## Scope and evidence guardrails

- The targets below were selected from publicly available material describing AI evaluation, standards, assurance, risk governance, provenance, or evidence practices.
- A public contact route means an official contact form, program mailbox, mailing list, or other openly documented route. No private email addresses, assumed relationships, or scraped personal contact data are included.
- “Problem hypothesis” is explicitly a hypothesis, not a claim about the target’s internal pain.
- REPEAT is described only as an architecture for deterministic evidence records, canonicalization, receipts, verification, and fail-closed/auditable state transitions. This package does **not** claim that REPEAT is proven, commercially validated, production-ready, or a solution for any target.
- Source pages and roles should be rechecked immediately before outreach; organizational roles and contact routes can change.

---

## 1. National Institute of Standards and Technology (NIST) — Center for AI Standards and Innovation / AI Resource Center

- **Target organization:** [NIST Center for AI Standards and Innovation (CAISI)](https://www.nist.gov/caisi), with the [NIST AI Resource Center (AIRC)](https://airc.nist.gov/).
- **Specific person / role:** CAISI program leadership or the AIRC program/contact team. The role is preferred over naming an individual unless the current NIST page identifies a relevant person at the time of contact.
- **Public contact route:** [NIST contact page](https://www.nist.gov/about-nist/contact-us); [AIRC contact page](https://airc.nist.gov/contact-us). Route the inquiry to the CAISI/AIRC program rather than to an unverified individual address.
- **Why this target — evidence-based:** NIST publishes the [AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework), maintains AI standards and measurement/evaluation work, and describes CAISI as part of its AI standards, testing, and evaluation mission. These are direct public signals that evidence quality, repeatability, measurement, and assessment artifacts matter to the organization’s work.
- **Problem hypothesis:** **Hypothesis:** AI testing and risk-management programs may need a durable way to bind an evaluation claim to its inputs, model/version, procedure, verifier, timestamp, and disposition so that another party can reproduce or audit the claim later.
- **Discovery opening:** “Your AI RMF and evaluation work treats measurement and evidence as operational concerns. We are studying whether teams need more deterministic, independently verifiable records for claims about an AI system’s state or evaluation result.”
- **What to ask:**
  1. Which evaluation or risk-management claims are hardest to reproduce or independently audit after the fact?
  2. What minimum provenance must travel with a test result for it to be useful across organizations?
  3. Where do current standards leave implementation ambiguity around receipts, canonical records, or verifier failure?
- **What not to claim:** Do not say NIST endorses REPEAT, that REPEAT implements the AI RMF, or that REPEAT satisfies a NIST requirement.
- **Evidence sources:** [NIST CAISI](https://www.nist.gov/caisi); [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework); [NIST AI measurement and evaluation](https://www.nist.gov/ai-measurement-and-evaluation).
- **REPEAT relevance:** Descriptively, REPEAT’s deterministic canonical JSON and receipt rules could be a concrete object for discussing how evidence records are normalized and independently checked; whether that is useful in NIST contexts is the discovery question.
- **Outreach status:** `NOT_CONTACTED`

---

## 2. METR — Model Evaluation and Threat Research

- **Target organization:** [METR](https://metr.org/), a nonprofit research organization focused on evaluating advanced AI systems and risks.
- **Specific person / role:** Beth Barnes, publicly identified by METR as a founder/executive leader; if the page changes, address the **model-evaluation research lead** role instead.
- **Public contact route:** [METR contact page](https://metr.org/contact/) and the public channels listed there. Use the organization’s route; do not infer a personal email address.
- **Why this target — evidence-based:** METR publicly describes work on evaluating advanced AI capabilities and risks, including task-based evaluations and research intended to make capability/risk claims more measurable. That creates a direct relevance to evidence provenance and reproducibility.
- **Problem hypothesis:** **Hypothesis:** Evaluation results may be difficult to compare or audit when task definitions, harness versions, model snapshots, environment state, grader behavior, and interpretation are distributed across artifacts or change over time.
- **Discovery opening:** “We are looking for evaluation teams willing to describe where an evaluation claim loses provenance between task execution and publication—not to propose a product or assume the problem exists.”
- **What to ask:**
  1. Which parts of an evaluation run must be frozen to make a result independently replayable?
  2. How do you represent a change in task, harness, grader, model snapshot, or environment without obscuring the prior claim?
  3. What would make a result receipt useful to a skeptical external reviewer?
- **What not to claim:** Do not claim REPEAT improves METR’s evaluations, provides safety evidence, or has been tested by METR.
- **Evidence sources:** [METR home](https://metr.org/); [METR research](https://metr.org/research/); [METR evaluations](https://metr.org/). Confirm the named person and current contact route on the official site before sending.
- **REPEAT relevance:** REPEAT’s evidence-object, canonicalization, hash receipt, and verifier/NACK concepts are descriptive examples of mechanisms that might help preserve evaluation lineage; fit and sufficiency remain untested.
- **Outreach status:** `NOT_CONTACTED`

---

## 3. MLCommons — AI Safety / AI Risk and Reliability community

- **Target organization:** [MLCommons](https://mlcommons.org/), especially its AI safety, benchmarking, and reliability activities.
- **Specific person / role:** The current **AI safety or benchmarking working-group chair/lead**, selected from the official MLCommons leadership or working-group pages at the time of outreach. Do not guess a personal address if no current named lead is published.
- **Public contact route:** [MLCommons contact page](https://mlcommons.org/contact/) and the public working-group/community routes linked from the site.
- **Why this target — evidence-based:** MLCommons organizes public benchmarks and measurement communities for machine learning, and its stated work concerns comparable, transparent performance measurement. A benchmark ecosystem is a plausible environment for provenance and evidence-integrity questions.
- **Problem hypothesis:** **Hypothesis:** Benchmark claims can become difficult to compare when submissions, datasets, code, hardware/software environments, scoring logic, and exception handling are not represented as one verifiable chain of evidence.
- **Discovery opening:** “We are researching the evidence layer around benchmark claims: what must be recorded so a result remains attributable, comparable, and reviewable after the submission pipeline changes?”
- **What to ask:**
  1. Which benchmark artifacts are mandatory today, and which are most often missing or difficult to validate?
  2. How are benchmark revisions and corrected results linked to the original published state?
  3. Would a machine-verifiable receipt help reviewers distinguish a changed result from a new result?
- **What not to claim:** Do not claim MLCommons uses, needs, endorses, or would adopt REPEAT.
- **Evidence sources:** [MLCommons](https://mlcommons.org/); [MLCommons benchmarks](https://mlcommons.org/benchmarks/); [MLCommons contact](https://mlcommons.org/contact/).
- **REPEAT relevance:** REPEAT can be shown as a descriptive design for canonical evidence and explicit state transitions around benchmark artifacts, without asserting that it meets MLCommons’ governance or technical requirements.
- **Outreach status:** `NOT_CONTACTED`

---

## 4. Credo AI — AI governance and assurance platform

- **Target organization:** [Credo AI](https://www.credo.ai/), an AI governance company.
- **Specific person / role:** Navrina Singh, publicly identified by Credo AI as founder/CEO; alternatively the current **product or AI governance lead** listed on Credo AI’s official team/contact pages.
- **Public contact route:** [Credo AI contact page](https://www.credo.ai/contact-us). Use the general inquiry route and address the request to AI governance/evidence infrastructure.
- **Why this target — evidence-based:** Credo AI publicly describes governance capabilities involving policy, controls, risk management, and documentation for AI systems. Those public materials indicate a concrete intersection with auditability and evidence of governance decisions.
- **Problem hypothesis:** **Hypothesis:** Governance teams may have difficulty proving which policy/control assessment applied to which model or deployment state, especially when evidence is collected from multiple systems and updated continuously.
- **Discovery opening:** “We are comparing how AI-governance platforms preserve evidence for a control decision as a model moves through assessment, approval, monitoring, and remediation.”
- **What to ask:**
  1. What is the smallest evidence bundle that makes a governance decision defensible to an internal or external reviewer?
  2. How do you distinguish a changed control result from a new assessment, and preserve both states?
  3. Which evidence-integrity or provenance gaps remain even when governance workflows are documented?
- **What not to claim:** Do not say REPEAT integrates with Credo AI, satisfies a regulatory obligation, or replaces Credo AI’s governance platform.
- **Evidence sources:** [Credo AI governance](https://www.credo.ai/); [Credo AI platform](https://www.credo.ai/platform); [Credo AI contact](https://www.credo.ai/contact-us). Confirm the current named person/role on the official site before outreach.
- **REPEAT relevance:** REPEAT’s receipt and claimed-state-transition concepts provide a neutral vocabulary for discussing evidence lineage; they are not presented as a validated implementation of Credo AI workflows.
- **Outreach status:** `NOT_CONTACTED`

---

## 5. VeritasChain Standards Organization / IETF Verifiable AI Provenance Framework

- **Target organization:** [VeritasChain Standards Organization](https://veritaschain.org/) and the related [IETF Verifiable AI Provenance Framework Internet-Draft](https://www.ietf.org/archive/id/draft-kamimura-vap-framework-00.html).
- **Specific person / role:** T. Kamimura, listed as author/contact for the IETF draft; engage in the capacity of **framework author and provenance-standards contributor**. The draft’s author information is the source of truth for the current route.
- **Public contact route:** The author contact and discussion mechanisms listed in the [IETF Datatracker draft record](https://datatracker.ietf.org/doc/draft-kamimura-vap-framework/), or the official VeritasChain contact route. Use only the address or list route displayed there.
- **Why this target — evidence-based:** The public draft explicitly addresses verifiable AI provenance and evidentiary AI decision trails. This is the closest thematic match in the package to evidence integrity and cross-organizational auditability.
- **Problem hypothesis:** **Hypothesis:** Provenance frameworks may need sharper interoperability rules for canonical serialization, receipt calculation, verifier behavior, and the distinction between an asserted state and an independently verified state.
- **Discovery opening:** “We found a public provenance framework that addresses verifiable AI decision trails. We are testing whether the lower-level receipt and verifier semantics are sufficiently concrete for independent implementations to agree byte-for-byte.”
- **What to ask:**
  1. Which provenance fields must be canonicalized for two independent implementations to produce the same evidence identity?
  2. How should a verifier represent NACK, missing evidence, supersession, and later correction?
  3. Where should a provenance standard stop, leaving implementation choices to the deploying organization?
- **What not to claim:** Do not imply IETF standardization, adoption, endorsement, or interoperability of REPEAT; an Internet-Draft is not by itself an IETF standard.
- **Evidence sources:** [IETF VAP draft](https://www.ietf.org/archive/id/draft-kamimura-vap-framework-00.html); [IETF Datatracker record](https://datatracker.ietf.org/doc/draft-kamimura-vap-framework/); [VeritasChain](https://veritaschain.org/). Verify that the draft and contact details remain current before outreach.
- **REPEAT relevance:** REPEAT’s public specification includes deterministic canonicalization, SHA-256 receipts, and fail-closed verifier behavior. These are discussion artifacts for standards discovery, not claims of conformance or superiority.
- **Outreach status:** `NOT_CONTACTED`

---

## Suggested tracking fields

When a target responds, append—not overwrite—the record with: `date_contacted`, `route_used`, `respondent_role`, `problem_confirmed` (`yes` / `no` / `unclear`), `exact_problem_language`, `existing_workaround`, `evidence_artifacts_named`, `follow_up`, and `source_links`. Keep claims tied to the respondent’s words or public evidence.
