# sovereign-legal

> Read `INTENT.md` first. It is the root authority for all work in this repo.

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
