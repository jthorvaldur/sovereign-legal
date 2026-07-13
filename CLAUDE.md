# sovereign-legal

## What this repo does

Jurisdictional analysis toolkit. Maps the four-layer jurisdictional stack (Natural Law, Common Law, Statutory/Equity, Commercial/Admiralty), translates legal terms across jurisdictions, identifies what kind of court is operating, and generates jurisdiction-challenging questions.

This is NOT grammar analysis — that's words_quantum_legal. This is the STRATEGIC layer: which jurisdiction is the court operating in, and how do you shift it?

## How it connects to other repos

| Repo | Relationship |
|------|-------------|
| `words_quantum_legal` | Language layer — morpheme analysis, Black's Law parsing. sovereign-legal uses its output for jurisdictional classification. |
| `div_legal` | Active case data — documents, filings, timelines. sovereign-legal provides jurisdictional analysis of those documents. |
| `morpheme-page` | Web presentation — renders sovereign-legal analysis for public display. |
| `caseledger` | Document corpus — 1.7M vectors of legal documents. sovereign-legal queries this for pattern matching. |
| `policy-orchestrator` | Governance hub — sovereign-legal follows its INTENT.md and policy framework. |

## CLI commands

```bash
sovereign analyze-jurisdiction FILE    # scan court order for jurisdictional markers (Layer 1-4)
sovereign translate TERM               # show term across all 4 jurisdictional layers
sovereign question TEXT                # generate jurisdiction-challenging questions from a statement
sovereign identify-court FILE          # classify court type (banking/congressional/equity/statutory)
```

All commands support `--format table|json|yaml` output.

## Key directories

- `INTENT.md` — root authority for this repo
- `docs/` — the jurisdictional model, translations, frameworks
- `src/sovereign_legal/` — CLI and analysis tools
- `.control/repo.yaml` — policy-orchestrator contract

## Vector DB access

Query these collections for context before answering questions:

### Port 6333 (main Qdrant)
- `legal_docs_v2` (244K points) — emails, PDFs, filings, financial statements
- `fact_registry` (167 points) — classified facts with confidence levels

### Port 7333 (caseledger Qdrant)
- `case_docs` (1.7M points) — full legal document corpus with hybrid search

```bash
# Quick search from policy-orchestrator
cd ~/GitHub/policy-orchestrator && uv run devctl search "jurisdiction" --limit 5

# Direct Qdrant query
curl -s -X POST http://localhost:6333/collections/legal_docs_v2/points/scroll \
  -H 'Content-Type: application/json' \
  -d '{"limit": 5, "with_payload": true, "with_vector": false}' | python3 -m json.tool
```

## Rules for agents working in this repo

1. Read `INTENT.md` before acting. Identify the jurisdictional layer before producing output.
2. Never commit .env or secret files.
3. Query vector databases for context before answering from memory.
4. Distinguish between jurisdictional layers — never conflate Natural Law rights with Statutory privileges.
5. Default to questions over statements in generated legal text.
6. Flag uncertainty using the INTENT.md template.
7. Every file must answer: Which jurisdictional layer does this address? What strategic purpose does it serve?

---

## Repo intent (folded from INTENT.md, 2026-07-12)

# INTENT.md


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
