# INTENT.md

> **Version:** 0.1.0
> **Scope:** This repository only. Inherits from policy-orchestrator INTENT.md.
> **Audience:** Every agent — human, AI, or automated — that reads or writes in this repo.

---

## Prime Directive

Map the jurisdictional dimensions of legal reality and provide tools to operate across them.

This is the STRATEGIC layer. Not grammar analysis (that's words_quantum_legal). Not case management (that's div_legal). Not web presentation (that's morpheme-page). This repo answers one question: **which jurisdiction are you in, and how do you shift it?**

---

## 1. Operating Rules

**Jurisdiction first.** Every legal term, every court order, every procedural move exists within a jurisdictional context. Identify the jurisdiction before analyzing the content.

**Four layers, always.** The jurisdictional stack has four layers: Natural Law, Common Law, Statutory/Equity, Commercial/Admiralty. Every analysis must place the subject within this stack. Courts move between layers — often without disclosing it.

**Questions over statements.** In law, silence is consent. Statements accept jurisdiction; questions challenge it. Default to the interrogative form.

**Signal over noise.** Inherited from policy-orchestrator. Every output must be directly relevant, logically consistent, and actionable.

**Internal consistency.** Before producing work, verify it does not contradict the jurisdictional model, prior analysis, or existing conventions.

**No drift.** This repo covers jurisdictional analysis and strategy. If work begins to cover grammar/morphology (words_quantum_legal), case specifics (div_legal), or web rendering (morpheme-page) — stop. Redirect to the correct repo.

**Flag uncertainty.** State what is unknown. Name the assumption.

```
Uncertainty: [what is unknown]
Assumption: [what is being assumed]
Implication: [what breaks if the assumption is wrong]
```

---

## 2. Decision Principles

When choosing between designs, prefer — in order:

1. Precise over approximate (jurisdiction must be exact).
2. Explicit over implicit (name the jurisdiction, name the layer).
3. Composable over monolithic (each tool does one thing).
4. Auditable over opaque (every classification must cite its reasoning).
5. Question over statement (maintain standing by default).
6. Reversible over permanent (jurisdictional positions can shift).

---

## 3. Output Structure

Jurisdictional analysis:

```
Term/Order/Filing → Jurisdictional Layer → Rights at that Layer → Strategic Position → Questions to Ask
```

Court classification:

```
Document → Language Markers → Jurisdiction Indicators → Court Type → Authority Basis → Challenge Points
```

Every substantial output ends with:

```
Jurisdictional Position: [which layer, which standing]
```

or

```
Next Question: [what must be asked to shift or clarify jurisdiction]
```

---

## 4. Repo Boundaries

This repository must not become:

- A grammar or morphology tool (that's words_quantum_legal).
- A case management system (that's div_legal).
- A web publishing pipeline (that's morpheme-page).
- A general legal reference (focus is jurisdictional strategy).
- A repository of specific case documents (those belong in div_legal/caseledger).

Every file should answer:

```
Which jurisdictional layer does this address?
What strategic purpose does it serve?
How does it help identify or shift jurisdiction?
```

---

## 5. Agent Protocol

Applies to all AI assistants, code generators, and automated tooling:

- Read this file before acting.
- Identify the jurisdictional layer relevant to the task before producing output.
- Query vector databases (legal_docs_v2, case_docs) for context before answering from memory.
- Distinguish between jurisdictional layers in all analysis — never conflate them.
- Preserve the question-first methodology in generated text.
- Do not introduce secrets into tracked files.
- Do not duplicate functionality handled by another repo.
- Provide jurisdictional classification after changes.

---

## Override Mechanism

This INTENT inherits from policy-orchestrator's INTENT.md. Local rules extend but do not weaken the parent. Section 4 (Repo Boundaries) cannot be relaxed.

---
