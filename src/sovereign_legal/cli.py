"""
sovereign-legal CLI — Jurisdictional analysis toolkit.

Identify which jurisdiction a court operates in, translate terms across
jurisdictional layers, generate jurisdiction-challenging questions, and
classify court types.
"""

import json
import os
import re
import sys
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
TRANSLATIONS_FILE = DATA_DIR / "translations.yaml"

# ---------------------------------------------------------------------------
# Jurisdictional layer definitions
# ---------------------------------------------------------------------------

LAYERS = {
    4: {
        "name": "Natural Law / Divine Law",
        "short": "Natural",
        "color": "bright_green",
        "description": "Rights by nature — cannot be granted or revoked by the state.",
    },
    3: {
        "name": "Common Law",
        "short": "Common",
        "color": "bright_cyan",
        "description": "Rights by custom and precedent — trial by jury, habeas corpus, due process.",
    },
    2: {
        "name": "Statutory Law / Equity",
        "short": "Statutory",
        "color": "bright_yellow",
        "description": "Legislation and court rules — privileges defined by statute.",
    },
    1: {
        "name": "Commercial / Admiralty Law",
        "short": "Commercial",
        "color": "bright_red",
        "description": "Banking law, corporate fictions, UCC — contracts between entities.",
    },
}

# ---------------------------------------------------------------------------
# Jurisdiction markers for document analysis
# ---------------------------------------------------------------------------

JURISDICTION_MARKERS = {
    4: {
        "keywords": [
            "natural right", "god-given", "divine", "unalienable",
            "inherent right", "creator", "endowed", "flesh and blood",
            "living soul", "offspring", "natural law", "laws of nature",
            "bodily autonomy", "sacred",
        ],
    },
    3: {
        "keywords": [
            "common law", "jury trial", "trial by jury", "habeas corpus",
            "due process", "precedent", "magna carta", "bill of rights",
            "the people", "freehold", "allodial", "oath", "affidavit",
            "injured party", "harmed party", "writ",
        ],
    },
    2: {
        "keywords": [
            "pursuant to", "statute", "ilcs", "usc", "code",
            "best interest", "equitable", "court finds", "discretion",
            "petitioner", "respondent", "motion", "hearing", "ruling",
            "public policy", "section", "subsection", "supreme court rule",
        ],
    },
    1: {
        "keywords": [
            "ucc", "uniform commercial", "debtor", "creditor",
            "settlement", "account", "garnishment", "arrears",
            "corporate", "admiralty", "maritime", "negotiable instrument",
            "commercial paper", "trust", "estate", "asset", "liability",
        ],
    },
}

# ---------------------------------------------------------------------------
# Court type definitions
# ---------------------------------------------------------------------------

COURT_TYPES = {
    "banking": {
        "label": "Banking / Commercial Court",
        "layer": 1,
        "markers": [
            "all caps names", "division of assets", "settlement",
            "child support obligation", "garnishment", "arrears",
            "account", "maintenance", "alimony", "order to pay",
        ],
        "description": "Operates as a commercial venue settling debts between corporate fictions.",
    },
    "congressional": {
        "label": "Congressional / Statutory Court",
        "layer": 2,
        "markers": [
            "pursuant to", "the statute provides", "as defined in",
            "ilcs", "usc", "public policy", "legislative intent",
            "codified", "enacted",
        ],
        "description": "Applies legislation — codes, acts, and rules created by the legislature.",
    },
    "equity": {
        "label": "Equity Court",
        "layer": 2,
        "markers": [
            "best interest", "court's discretion", "equitable distribution",
            "this court finds it equitable", "balancing the factors",
            "modified circumstances", "no jury", "fairness",
        ],
        "description": "Judge has extraordinary discretion. No jury. Subjective standards.",
    },
    "common_law": {
        "label": "Common Law Court",
        "layer": 3,
        "markers": [
            "jury", "precedent", "common law", "harmed party",
            "injured party", "habeas corpus", "due process",
            "rights of the accused",
        ],
        "description": "Precedent-based, jury trial, rights-focused. Requires a harmed party.",
    },
}

# ---------------------------------------------------------------------------
# Question templates
# ---------------------------------------------------------------------------

QUESTION_TEMPLATES = [
    "Under what specific authority does this court claim jurisdiction over {subject}?",
    "Has jurisdiction been established by consent? If so, when was that consent given?",
    "Is this court operating under common law, equity, statutory, or commercial jurisdiction?",
    "Does this court acknowledge rights that exist beyond its authority to grant or revoke?",
    "By what authority does this court claim power over the natural bond between parent and offspring?",
    "Is the name on that document the name of a living man/woman, or a corporate fiction?",
    "Where is the contract that establishes this court's jurisdiction?",
    "If this court operates in equity, when did I consent to waive my common law right to a jury trial?",
    "What are the outer limits of this court's jurisdiction?",
    "Is this proceeding treating {subject} as a commercial transaction? If so, where is the contract?",
]

# ---------------------------------------------------------------------------
# Term database (YAML-backed, LLM-expandable)
# ---------------------------------------------------------------------------

def load_translations() -> dict:
    """Load translations from YAML data file."""
    if TRANSLATIONS_FILE.exists():
        return yaml.safe_load(TRANSLATIONS_FILE.read_text()) or {}
    return {}


def save_translations(db: dict) -> None:
    """Write translations back to YAML, preserving the header comment."""
    header = (
        "# translations.yaml — Jurisdictional term database\n"
        "# Each term has definitions across 4 layers.\n"
        "# New terms are generated by LLM and appended here.\n"
        "# Source: sovereign-legal conceptual framework "
        "(Black's Law + natural rights + commercial/admiralty)\n\n"
    )
    TRANSLATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRANSLATIONS_FILE.write_text(
        header + yaml.dump(db, default_flow_style=False, sort_keys=False, allow_unicode=True)
    )


def generate_translation(term: str) -> dict | None:
    """Use Claude to generate a 4-layer translation for an unknown term."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic
        client = anthropic.Anthropic()
    except Exception:
        return None

    system = (
        "You are a jurisdictional language analyst. You translate legal terms "
        "across four jurisdictional layers:\n\n"
        "1. Common English — plain meaning as understood by ordinary people\n"
        "2. Black's Law / Statutory — meaning in statutory law, Black's Law Dictionary\n"
        "3. Natural Rights — meaning in natural law (rights by nature, not state grant; "
        "Locke, Blackstone, biological reality)\n"
        "4. Commercial / Admiralty — meaning in commercial/banking/UCC/admiralty law "
        "(corporate fictions, contracts, debts)\n\n"
        "Key principle: using the wrong word accepts the wrong jurisdiction. "
        "Each definition should be 1-2 sentences, substantive, and show HOW "
        "the meaning shifts across jurisdictions.\n\n"
        "Respond ONLY with valid YAML (no markdown fences, no commentary) in this exact format:\n"
        "common_english: ...\n"
        "blacks_law: ...\n"
        "natural_rights: ...\n"
        "commercial: ..."
    )

    console.print(f"[dim]Generating translation for '[/dim][bold]{term}[/bold][dim]'...[/dim]")

    try:
        resp = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            system=system,
            messages=[{"role": "user", "content": f"Translate the term: {term}"}],
        )
        text = resp.content[0].text.strip()
        # Strip markdown fences if present
        text = re.sub(r'^```\w*\n?', '', text)
        text = re.sub(r'\n?```$', '', text)
        entry = yaml.safe_load(text)
        if isinstance(entry, dict) and all(
            k in entry for k in ("common_english", "blacks_law", "natural_rights", "commercial")
        ):
            return entry
    except Exception as e:
        console.print(f"[red]Generation failed: {e}[/red]")

    return None


# ---------------------------------------------------------------------------
# Output formatting helpers
# ---------------------------------------------------------------------------

def output_as_json(data: dict) -> None:
    console.print_json(json.dumps(data, indent=2, default=str))


def output_as_yaml(data: dict) -> None:
    console.print(yaml.dump(data, default_flow_style=False, sort_keys=False))


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(version="0.1.0", prog_name="sovereign")
def main():
    """Sovereign Legal — Jurisdictional analysis toolkit.

    Identify which jurisdiction a court operates in, translate terms across
    jurisdictional layers, generate jurisdiction-challenging questions, and
    classify court types.

    Four-layer model: Natural Law > Common Law > Statutory/Equity > Commercial/Admiralty.
    """
    pass


# ---------------------------------------------------------------------------
# sovereign translate
# ---------------------------------------------------------------------------

@main.command("translate")
@click.argument("term")
@click.option("--format", "fmt", type=click.Choice(["table", "json", "yaml"]), default="table")
@click.option("--no-generate", is_flag=True, help="Don't generate missing terms via LLM.")
def translate(term: str, fmt: str, no_generate: bool):
    """Show a legal term across all four jurisdictional layers.

    Translates between common English, Black's Law, natural rights,
    and commercial/admiralty definitions. Unknown terms are generated
    by LLM and saved to the term database.
    """
    db = load_translations()
    key = term.lower().strip()
    generated = False

    if key not in db:
        if no_generate:
            available = ", ".join(sorted(db.keys()))
            console.print(f"[red]Term '{term}' not found.[/red]")
            console.print(f"[dim]Available: {available}[/dim]")
            console.print("[dim]Remove --no-generate to auto-generate via LLM.[/dim]")
            sys.exit(1)

        entry = generate_translation(key)
        if entry is None:
            available = ", ".join(sorted(db.keys()))
            console.print(f"[red]Term '{term}' not found and generation failed.[/red]")
            console.print(f"[dim]Available: {available}[/dim]")
            console.print("[dim]Check ANTHROPIC_API_KEY is set.[/dim]")
            sys.exit(1)

        db[key] = entry
        save_translations(db)
        generated = True

    entry = db[key]

    data = {
        "term": key,
        "common_english": entry["common_english"],
        "blacks_law_statutory": entry["blacks_law"],
        "natural_rights": entry["natural_rights"],
        "commercial_admiralty": entry["commercial"],
    }

    if fmt == "json":
        data["generated"] = generated
        output_as_json(data)
        return

    if fmt == "yaml":
        data["generated"] = generated
        output_as_yaml(data)
        return

    # Rich table output
    console.print()
    title = f"[bold]{key.upper()}[/bold] — across four jurisdictional layers"
    if generated:
        title += "  [dim italic](generated & saved)[/dim italic]"
    console.print(Panel(title, style="bright_blue"))

    table = Table(show_lines=True, expand=True)
    table.add_column("Jurisdiction", style="bold", width=22)
    table.add_column("Definition", ratio=1)

    table.add_row("[bright_white]Common English[/bright_white]", entry["common_english"])
    table.add_row("[bright_yellow]Black's Law (Statutory)[/bright_yellow]", entry["blacks_law"])
    table.add_row("[bright_green]Natural Rights[/bright_green]", entry["natural_rights"])
    table.add_row("[bright_red]Commercial / Admiralty[/bright_red]", entry["commercial"])

    console.print(table)
    console.print()
    console.print(
        "[dim]Using the wrong word accepts the wrong jurisdiction. "
        "Choose terms that maintain your standing in the highest applicable layer.[/dim]"
    )
    if generated:
        console.print(f"[dim]Term saved to {TRANSLATIONS_FILE.name} ({len(db)} terms in database).[/dim]")
    console.print()


# ---------------------------------------------------------------------------
# sovereign analyze-jurisdiction
# ---------------------------------------------------------------------------

@main.command("analyze-jurisdiction")
@click.argument("file", type=click.Path(exists=True))
@click.option("--format", "fmt", type=click.Choice(["table", "json", "yaml"]), default="table")
def analyze_jurisdiction(file: str, fmt: str):
    """Scan a court order or legal document for jurisdictional markers.

    Classifies the document across all four jurisdictional layers (Natural,
    Common, Statutory, Commercial) and reports which markers were found.
    """
    text = Path(file).read_text(errors="replace").lower()

    results = {}
    for layer_num in sorted(LAYERS.keys(), reverse=True):
        layer_info = LAYERS[layer_num]
        markers = JURISDICTION_MARKERS[layer_num]
        found = [kw for kw in markers["keywords"] if kw in text]
        results[layer_num] = {
            "layer": layer_num,
            "name": layer_info["name"],
            "markers_found": found,
            "count": len(found),
            "total_possible": len(markers["keywords"]),
        }

    dominant = max(results.values(), key=lambda r: r["count"])

    if fmt == "json":
        output_as_json({"file": file, "layers": results, "dominant": dominant})
        return
    if fmt == "yaml":
        output_as_yaml({"file": file, "layers": results, "dominant": dominant})
        return

    console.print()
    console.print(Panel(f"[bold]Jurisdictional Analysis[/bold]\n{file}", style="bright_blue"))

    table = Table(title="Layer Analysis", show_lines=True)
    table.add_column("Layer", style="bold", width=8)
    table.add_column("Jurisdiction", width=28)
    table.add_column("Markers Found", width=8, justify="center")
    table.add_column("Keywords Detected", width=50)

    for layer_num in sorted(results.keys(), reverse=True):
        r = results[layer_num]
        layer_info = LAYERS[layer_num]
        color = layer_info["color"]
        marker_list = ", ".join(r["markers_found"][:8]) if r["markers_found"] else "none"
        if len(r["markers_found"]) > 8:
            marker_list += f" (+{len(r['markers_found']) - 8} more)"
        table.add_row(
            f"[{color}]{layer_num}[/{color}]",
            f"[{color}]{r['name']}[/{color}]",
            f"[{color}]{r['count']}/{r['total_possible']}[/{color}]",
            marker_list,
        )

    console.print(table)
    console.print()

    dom_color = LAYERS[dominant["layer"]]["color"]
    console.print(Panel(
        f"[bold {dom_color}]Dominant jurisdiction: Layer {dominant['layer']} — {dominant['name']}[/bold {dom_color}]\n"
        f"[dim]{LAYERS[dominant['layer']]['description']}[/dim]",
        title="Assessment", style=dom_color,
    ))
    console.print()
    console.print("[bold]Suggested questions:[/bold]")
    for q in QUESTION_TEMPLATES[:3]:
        console.print(f"  [dim]>[/dim] {q.format(subject='this matter')}")
    console.print()


# ---------------------------------------------------------------------------
# sovereign question
# ---------------------------------------------------------------------------

@main.command("question")
@click.argument("text")
@click.option("--format", "fmt", type=click.Choice(["table", "json", "yaml"]), default="table")
def question(text: str, fmt: str):
    """Generate jurisdiction-challenging questions from a statement or topic."""
    subject = text.strip()

    questions = {
        "jurisdiction": [
            f"Under what specific authority does this court claim jurisdiction over {subject}?",
            f"Has jurisdiction over {subject} been established by informed, voluntary consent?",
            f"Is this court operating under common law, equity, statutory, or commercial jurisdiction with respect to {subject}?",
        ],
        "disclosure": [
            f"For the record, what is the jurisdictional basis for any order concerning {subject}?",
            f"Does this court acknowledge rights regarding {subject} that exist beyond its authority?",
            f"Where is the contract that grants this court jurisdiction over {subject}?",
        ],
        "standing": [
            f"Am I not a living man/woman with natural rights regarding {subject}?",
            f"Is {subject} a matter of natural law, beyond the jurisdiction of any court of equity?",
            f"Have I not reserved all rights regarding {subject}, waiving none?",
        ],
    }

    if fmt == "json":
        output_as_json({"subject": subject, "questions": questions})
        return
    if fmt == "yaml":
        output_as_yaml({"subject": subject, "questions": questions})
        return

    console.print()
    console.print(Panel(
        f"[bold]Jurisdiction-Challenging Questions[/bold]\nSubject: [italic]{subject}[/italic]",
        style="bright_blue",
    ))
    for category, qlist in questions.items():
        console.print(f"\n[bold bright_cyan]{category.upper()}[/bold bright_cyan]")
        for q in qlist:
            console.print(f"  [dim]>[/dim] {q}")
    console.print()
    console.print(
        "[dim]Questions assert jurisdiction; statements accept it. "
        "The one who asks controls the conversation.[/dim]"
    )
    console.print()


# ---------------------------------------------------------------------------
# sovereign identify-court
# ---------------------------------------------------------------------------

@main.command("identify-court")
@click.argument("file", type=click.Path(exists=True))
@click.option("--format", "fmt", type=click.Choice(["table", "json", "yaml"]), default="table")
def identify_court(file: str, fmt: str):
    """Classify the type of court based on a legal document."""
    raw = Path(file).read_text(errors="replace")
    text = raw.lower()

    all_caps_names = re.findall(r'\b[A-Z]{2,}\s+[A-Z]{2,}\b', raw)
    has_all_caps = len(all_caps_names) > 0

    results = {}
    for court_id, court_info in COURT_TYPES.items():
        found = [m for m in court_info["markers"] if m in text]
        score = len(found)
        if court_id == "banking" and has_all_caps:
            score += 3
        results[court_id] = {
            "type": court_info["label"],
            "layer": court_info["layer"],
            "score": score,
            "markers_found": found,
            "description": court_info["description"],
        }

    ranked = sorted(results.values(), key=lambda r: r["score"], reverse=True)
    primary = ranked[0]

    if fmt == "json":
        output_as_json({
            "file": file,
            "all_caps_names": all_caps_names[:5] if has_all_caps else [],
            "classification": ranked,
            "primary": primary,
        })
        return
    if fmt == "yaml":
        output_as_yaml({
            "file": file,
            "all_caps_names": all_caps_names[:5] if has_all_caps else [],
            "classification": ranked,
            "primary": primary,
        })
        return

    console.print()
    console.print(Panel(f"[bold]Court Type Classification[/bold]\n{file}", style="bright_blue"))

    if has_all_caps:
        console.print(
            f"[bold bright_red]ALL CAPS names detected:[/bold bright_red] "
            f"{', '.join(all_caps_names[:5])}"
        )
        console.print("[dim]Strong indicator of commercial/admiralty jurisdiction.[/dim]")
        console.print()

    table = Table(title="Court Type Scores", show_lines=True)
    table.add_column("Court Type", style="bold", width=30)
    table.add_column("Layer", width=8, justify="center")
    table.add_column("Score", width=8, justify="center")
    table.add_column("Markers Found", width=40)

    for r in ranked:
        layer_info = LAYERS[r["layer"]]
        color = layer_info["color"]
        marker_list = ", ".join(r["markers_found"][:6]) if r["markers_found"] else "none"
        table.add_row(r["type"], f"[{color}]{r['layer']}[/{color}]", str(r["score"]), marker_list)

    console.print(table)
    console.print()

    primary_color = LAYERS[primary["layer"]]["color"]
    console.print(Panel(
        f"[bold {primary_color}]Primary classification: {primary['type']}[/bold {primary_color}]\n"
        f"Layer {primary['layer']} — {LAYERS[primary['layer']]['name']}\n\n"
        f"[dim]{primary['description']}[/dim]",
        title="Assessment", style=primary_color,
    ))
    console.print()
    console.print("[bold]Key question to ask:[/bold]")
    console.print(
        f"  [dim]>[/dim] Under what authority does this court operate — "
        f"and has that authority been established by informed consent?"
    )
    console.print()


if __name__ == "__main__":
    main()
