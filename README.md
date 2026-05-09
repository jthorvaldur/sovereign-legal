# sovereign-legal

Jurisdictional analysis toolkit -- identify which jurisdiction a court operates in, translate terms across the four-layer jurisdictional stack, and generate questions that challenge court authority.

## What it does

Maps the four-layer jurisdictional model (Natural Law > Common Law > Statutory/Equity > Commercial/Admiralty) and provides tools to analyze, translate, and challenge jurisdiction. Courts move between layers, often without disclosure. This toolkit makes those shifts visible.

## Installation

```bash
uv pip install -e .
```

## CLI usage

```bash
sovereign translate "custody"           # Show term across all 4 jurisdictional layers
sovereign question "motion to modify"   # Generate jurisdiction-challenging questions
sovereign identify-court filing.txt     # Classify court type from a legal document
sovereign analyze-jurisdiction order.pdf # Scan document for jurisdictional indicators
```

## Architecture

Part of the sovereign architecture triad:

```
sovereign-legal (jurisdictional strategy)
    |
    +-- dna-rights (natural rights assertions, biological standing)
    |
    +-- embedded-commands (communication analysis, influence engineering)
```

- **sovereign-legal** provides the jurisdictional questioning framework used by the other two
- **dna-rights** applies natural rights arguments grounded in the jurisdictional layers defined here
- **embedded-commands** uses jurisdictional context for audience calibration in legal communications
- **div_legal / caseledger** apply these tools to active case work

## Structure

```
sovereign-legal/
├── INTENT.md              # Governing document
├── pyproject.toml
├── data/translations.yaml # Term translations across jurisdictional layers
├── docs/                  # Framework documentation
├── html/                  # Self-contained HTML presentations
└── src/sovereign_legal/   # CLI toolkit
```

---

Managed by [policy-orchestrator](https://github.com/jthorvaldur/policy-orchestrator). Category: legal.

<!-- AUTO:footer -->
Managed by [policy-orchestrator](https://github.com/jthorvaldur/policy-orchestrator). Category: legal. 5 commits, last updated 40 minutes ago.
<!-- /AUTO:footer -->
