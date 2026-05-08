"""
sovereign-legal CLI — Jurisdictional analysis toolkit.

Identify which jurisdiction a court operates in, translate terms across
jurisdictional layers, generate jurisdiction-challenging questions, and
classify court types.
"""

import json
import sys
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

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
        "patterns": [],
    },
    3: {
        "keywords": [
            "common law", "jury trial", "trial by jury", "habeas corpus",
            "due process", "precedent", "magna carta", "bill of rights",
            "the people", "freehold", "allodial", "oath", "affidavit",
            "injured party", "harmed party", "writ",
        ],
        "patterns": [],
    },
    2: {
        "keywords": [
            "pursuant to", "statute", "ilcs", "usc", "code",
            "best interest", "equitable", "court finds", "discretion",
            "petitioner", "respondent", "motion", "hearing", "ruling",
            "public policy", "section", "subsection", "supreme court rule",
        ],
        "patterns": [],
    },
    1: {
        "keywords": [
            "ucc", "uniform commercial", "debtor", "creditor",
            "settlement", "account", "garnishment", "arrears",
            "corporate", "admiralty", "maritime", "negotiable instrument",
            "commercial paper", "trust", "estate", "asset", "liability",
        ],
        "patterns": [],
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
# Black's Law translations (subset for CLI)
# ---------------------------------------------------------------------------

TRANSLATIONS = {
    "custody": {
        "common_english": "Having care of someone",
        "blacks_law": "Legal right to control and maintain a person; care awarded by a court",
        "natural_rights": "Stewardship of offspring — a natural duty, not a state-granted right",
        "commercial": "Possession of an asset; physical control of property or a person",
    },
    "child": {
        "common_english": "Young human being",
        "blacks_law": "A person under the age of majority; a ward of the state under court jurisdiction",
        "natural_rights": "Offspring — a living being connected by blood and nature to the parent",
        "commercial": "A dependent; a liability or asset on a balance sheet; a trust beneficiary",
    },
    "person": {
        "common_english": "A human being",
        "blacks_law": "A legal entity with rights and obligations; includes corporations",
        "natural_rights": "Man or woman — a living soul, flesh and blood; not a legal construct",
        "commercial": "PERSON — the corporate fiction, the ALL CAPS name on government documents",
    },
    "property": {
        "common_english": "Things you own",
        "blacks_law": "Real or personal property as defined by statute; subject to taxation",
        "natural_rights": "That which a man or woman holds by right of labor and nature",
        "commercial": "Commercial asset; subject to liens, encumbrances, UCC filings",
    },
    "title": {
        "common_english": "Ownership",
        "blacks_law": "Legal right to ownership as recognized by the state; legal vs equitable title",
        "natural_rights": "Natural dominion — authority over one's body, labor, and possessions",
        "commercial": "Certificate of ownership of a commercial asset; subject to liens",
    },
    "order": {
        "common_english": "A command",
        "blacks_law": "A directive of a court, enforceable by contempt",
        "natural_rights": "A request — no man has authority to command another absent consent",
        "commercial": "A commercial directive within an agreed framework",
    },
    "judgment": {
        "common_english": "A decision",
        "blacks_law": "Final determination of a court of competent jurisdiction",
        "natural_rights": "An opinion — carries no weight absent jurisdiction over the living man or woman",
        "commercial": "Settlement of accounts; final determination of debts between entities",
    },
    "court": {
        "common_english": "Place where justice happens",
        "blacks_law": "A tribunal established by law for the administration of justice",
        "natural_rights": "An assembly — where men and women resolve disputes by reason and evidence",
        "commercial": "A commercial venue for settlement of disputes between corporate entities",
    },
    "jurisdiction": {
        "common_english": "Authority over a matter",
        "blacks_law": "Power of a court to hear and decide a case; subject-matter + personal jurisdiction",
        "natural_rights": "Authority that exists only by consent — no man has inherent jurisdiction over another",
        "commercial": "Commercial jurisdiction created by contract — filing = accepting jurisdiction",
    },
    "consent": {
        "common_english": "Agreement",
        "blacks_law": "Voluntary agreement by a person of sufficient capacity; can be implied",
        "natural_rights": "Informed, voluntary, explicit agreement — cannot be coerced or presumed",
        "commercial": "Acceptance of terms; entering the court system = consenting to commercial jurisdiction",
    },
    "contract": {
        "common_english": "An agreement",
        "blacks_law": "A legally enforceable agreement with consideration",
        "natural_rights": "Meeting of minds — requires full disclosure, mutual benefit, voluntary participation",
        "commercial": "A commercial instrument; foundation of all commercial jurisdiction",
    },
    "guardian": {
        "common_english": "Protector",
        "blacks_law": "A person appointed by a court to manage the affairs of another",
        "natural_rights": "A protector by natural duty and love, not by state appointment",
        "commercial": "A trustee managing assets for a beneficiary; a commercial fiduciary role",
    },
    "parent": {
        "common_english": "Mother or father",
        "blacks_law": "Person with legal responsibility for a child; includes adoptive/step-parents",
        "natural_rights": "Mother or father — the one who gave life; the bond is beyond legal definition",
        "commercial": "Originator of a corporate entity; primary claimant to the 'asset'",
    },
    "domicile": {
        "common_english": "Where you live",
        "blacks_law": "True, fixed, permanent home; determines jurisdiction",
        "natural_rights": "Home — where a man or woman dwells by choice; not a legal construct",
        "commercial": "Registered address of a corporate entity; determines governing jurisdiction",
    },
    "residence": {
        "common_english": "Where you stay",
        "blacks_law": "A place where a person lives; may differ from domicile",
        "natural_rights": "The place where one currently sleeps — temporary, irrelevant to natural rights",
        "commercial": "Operating address of the corporate entity",
    },
    "citizen": {
        "common_english": "Member of a country",
        "blacks_law": "Person owing allegiance to a state, entitled to its protection",
        "natural_rights": "A free man or woman — not defined by allegiance to a state",
        "commercial": "Registered member of a corporate structure (the state as corporation)",
    },
    "subject": {
        "common_english": "One who is governed",
        "blacks_law": "One who owes allegiance to a sovereign and is governed by their laws",
        "natural_rights": "No man is subject to another absent consent",
        "commercial": "A party to a commercial arrangement; subject to the contract terms",
    },
    "sovereign": {
        "common_english": "Supreme authority",
        "blacks_law": "The supreme power in a state; in democracies, sovereignty resides in the people",
        "natural_rights": "Each man and woman is sovereign over themselves — self-governing",
        "commercial": "Not applicable — only parties to contracts, creditors, and debtors",
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
# Output formatting helpers
# ---------------------------------------------------------------------------

def output_as_json(data: dict) -> None:
    """Print data as formatted JSON."""
    console.print_json(json.dumps(data, indent=2, default=str))


def output_as_yaml(data: dict) -> None:
    """Print data as YAML."""
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

    # Determine dominant jurisdiction
    dominant = max(results.values(), key=lambda r: r["count"])

    if fmt == "json":
        output_as_json({"file": file, "layers": results, "dominant": dominant})
        return

    if fmt == "yaml":
        output_as_yaml({"file": file, "layers": results, "dominant": dominant})
        return

    # Table output
    console.print()
    console.print(Panel(
        f"[bold]Jurisdictional Analysis[/bold]\n{file}",
        style="bright_blue",
    ))

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
        title="Assessment",
        style=dom_color,
    ))

    # Suggest questions
    console.print()
    console.print("[bold]Suggested questions:[/bold]")
    for q in QUESTION_TEMPLATES[:3]:
        console.print(f"  [dim]>[/dim] {q.format(subject='this matter')}")
    console.print()


# ---------------------------------------------------------------------------
# sovereign translate
# ---------------------------------------------------------------------------

@main.command("translate")
@click.argument("term")
@click.option("--format", "fmt", type=click.Choice(["table", "json", "yaml"]), default="table")
def translate(term: str, fmt: str):
    """Show a legal term across all four jurisdictional layers.

    Translates between common English, Black's Law, natural rights,
    and commercial/admiralty definitions.
    """
    key = term.lower().strip()

    if key not in TRANSLATIONS:
        available = ", ".join(sorted(TRANSLATIONS.keys()))
        console.print(f"[red]Term '{term}' not found.[/red]")
        console.print(f"[dim]Available terms: {available}[/dim]")
        sys.exit(1)

    entry = TRANSLATIONS[key]

    data = {
        "term": key,
        "common_english": entry["common_english"],
        "blacks_law_statutory": entry["blacks_law"],
        "natural_rights": entry["natural_rights"],
        "commercial_admiralty": entry["commercial"],
    }

    if fmt == "json":
        output_as_json(data)
        return

    if fmt == "yaml":
        output_as_yaml(data)
        return

    # Rich table output
    console.print()
    console.print(Panel(
        f"[bold]{key.upper()}[/bold] — across four jurisdictional layers",
        style="bright_blue",
    ))

    table = Table(show_lines=True, expand=True)
    table.add_column("Jurisdiction", style="bold", width=22)
    table.add_column("Definition", ratio=1)

    table.add_row(
        "[bright_white]Common English[/bright_white]",
        entry["common_english"],
    )
    table.add_row(
        "[bright_yellow]Black's Law (Statutory)[/bright_yellow]",
        entry["blacks_law"],
    )
    table.add_row(
        "[bright_green]Natural Rights[/bright_green]",
        entry["natural_rights"],
    )
    table.add_row(
        "[bright_red]Commercial / Admiralty[/bright_red]",
        entry["commercial"],
    )

    console.print(table)
    console.print()
    console.print(
        "[dim]Using the wrong word accepts the wrong jurisdiction. "
        "Choose terms that maintain your standing in the highest applicable layer.[/dim]"
    )
    console.print()


# ---------------------------------------------------------------------------
# sovereign question
# ---------------------------------------------------------------------------

@main.command("question")
@click.argument("text")
@click.option("--format", "fmt", type=click.Choice(["table", "json", "yaml"]), default="table")
def question(text: str, fmt: str):
    """Generate jurisdiction-challenging questions from a statement or topic.

    Takes a statement, court order excerpt, or topic and produces questions
    designed to challenge jurisdiction, demand disclosure, and assert standing.
    """
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
        f"[bold]Jurisdiction-Challenging Questions[/bold]\n"
        f"Subject: [italic]{subject}[/italic]",
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
    """Classify the type of court based on a legal document.

    Analyzes language patterns to determine whether the court is operating
    as a banking/commercial court, congressional/statutory court, equity
    court, or common law court.
    """
    text = Path(file).read_text(errors="replace").lower()

    # Check for ALL CAPS names (strong commercial indicator)
    import re
    all_caps_names = re.findall(r'\b[A-Z]{2,}\s+[A-Z]{2,}\b', Path(file).read_text(errors="replace"))
    has_all_caps = len(all_caps_names) > 0

    results = {}
    for court_id, court_info in COURT_TYPES.items():
        found = [m for m in court_info["markers"] if m in text]
        score = len(found)
        if court_id == "banking" and has_all_caps:
            score += 3  # ALL CAPS names are a strong commercial indicator
        results[court_id] = {
            "type": court_info["label"],
            "layer": court_info["layer"],
            "score": score,
            "markers_found": found,
            "description": court_info["description"],
        }

    # Sort by score
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
    console.print(Panel(
        f"[bold]Court Type Classification[/bold]\n{file}",
        style="bright_blue",
    ))

    if has_all_caps:
        console.print(
            f"[bold bright_red]ALL CAPS names detected:[/bold bright_red] "
            f"{', '.join(all_caps_names[:5])}"
        )
        console.print("[dim]This is a strong indicator of commercial/admiralty jurisdiction.[/dim]")
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
        table.add_row(
            r["type"],
            f"[{color}]{r['layer']}[/{color}]",
            str(r["score"]),
            marker_list,
        )

    console.print(table)
    console.print()

    primary_color = LAYERS[primary["layer"]]["color"]
    console.print(Panel(
        f"[bold {primary_color}]Primary classification: {primary['type']}[/bold {primary_color}]\n"
        f"Layer {primary['layer']} — {LAYERS[primary['layer']]['name']}\n\n"
        f"[dim]{primary['description']}[/dim]",
        title="Assessment",
        style=primary_color,
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
