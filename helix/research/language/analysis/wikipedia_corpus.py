"""
Wikipedia Language Corpus Probe
core/probes/wiki_language_probe.py

Runs structural DCP-relevant analysis on 5 Wikipedia articles authored by the
user (Dissonance). The articles are treated as a high-quality formal corpus
under WP:NPOV and MOS constraints.

Key thesis: Wikipedia writing = "identity-preserving compression" under editorial
constraints. The lead section is a compressed trajectory of the full article.
This is a DCP event: full factual surface → editorial constraints → compressed lead.

Articles:
    - Chase_Young.pdf         (defensive end, Washington Commanders)
    - Jayden_Daniels.pdf      (QB, Washington Commanders)
    - Josh_Harris_(businessman).pdf (owner, Washington Commanders)
    - New_Commanders_Stadium.pdf    (stadium project)
    - Dota_2.pdf              (video game)

Metrics:
    - compression_ratio = lead_word_count / total_word_count
    - section_density   = word_count / section_count
    - GrammarPatterns extraction on lead and body
    - DCP trajectory: each section = one step,
      possibility_breadth = section_word_count / max_section_word_count
      (lead should be maximally dense = low breadth in DCP terms = compressed)

Usage:
    python -m applications.labs.wiki_language_probe
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Optional

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir()
)
sys.path.insert(0, str(ROOT))

import pypdf

from domains.self.analysis.trajectory import (
    TrajectoryEvent, TrajectoryLog,
    EVENT_SCHEMA_VERSION, LOG_SCHEMA_VERSION,
)
from domains.self.analysis.probes import (
    estimate_tension,
    estimate_post_collapse_narrowing,
    compute_qualification_status,
)
from domains.language.pattern_detection.grammar_patterns import GrammarPatterns
from domains.games.analysis.dcp import extract_dcp_event

DOCS_DIR = Path(r"C:/Users/dissonance/Desktop/Helix docs")

ARTICLES = [
    {"file": "Chase_Young.pdf",              "title": "Chase Young",               "subject": "sports"},
    {"file": "Jayden_Daniels.pdf",           "title": "Jayden Daniels",            "subject": "sports"},
    {"file": "Josh_Harris_(businessman).pdf","title": "Josh Harris (businessman)",  "subject": "business"},
    {"file": "New_Commanders_Stadium.pdf",   "title": "New Commanders Stadium",     "subject": "infrastructure"},
    {"file": "Dota_2.pdf",                   "title": "Dota 2",                    "subject": "gaming"},
]

# Patterns that suggest a section header in Wikipedia PDF extraction
# (all-caps lines, or lines that look like == Header == stripped)
_SECTION_HEADER_RE = re.compile(
    r'^(?:'
    r'[A-Z][A-Za-z\s\-&/]{3,50}$'           # Title-case standalone line
    r'|[A-Z\s]{4,50}$'                       # All-caps short line
    r')',
    re.MULTILINE,
)

_REFERENCES_MARKER_RE = re.compile(
    r'\b(?:References|Notes|External links|See also|Bibliography|Citations)\b',
    re.IGNORECASE,
)

_SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+')


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract all text from a PDF file."""
    reader = pypdf.PdfReader(str(pdf_path))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return " ".join(pages)


def split_lead_and_sections(text: str) -> dict:
    """
    Split article text into lead/intro and body sections.

    Strategy:
        - Lead = text before the first recognized section header
          (or first 400 words if no header found)
        - Body sections = remaining text split at headers
        - References = everything after the References marker (excluded)

    Returns:
        {
            'full_text': str,
            'lead': str,
            'sections': list[dict{'name': str, 'text': str}],
            'references_excluded': bool,
        }
    """
    # Strip references section
    ref_match = _REFERENCES_MARKER_RE.search(text)
    if ref_match:
        body_text = text[:ref_match.start()].strip()
        refs_excluded = True
    else:
        body_text = text.strip()
        refs_excluded = False

    lines = body_text.split("\n")

    # Find first plausible section header (after at least 100 words of lead)
    lead_lines = []
    sections: list[dict] = []
    current_section_name = ""
    current_section_lines: list[str] = []
    in_lead = True
    lead_word_count = 0

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_lead:
                lead_lines.append("")
            else:
                current_section_lines.append("")
            continue

        # Detect section header: short line (< 60 chars), mostly alpha, after we have enough lead
        is_header = (
            lead_word_count >= 80
            and len(stripped) < 60
            and len(stripped) > 3
            and not stripped.endswith(".")
            and not stripped.endswith(",")
            and not re.search(r'\d{4}', stripped)  # not a date line
            and re.match(r'^[A-Z]', stripped)       # starts with capital
            and stripped.count(" ") < 8             # short phrase
        )

        if in_lead:
            if is_header:
                in_lead = False
                current_section_name = stripped
                current_section_lines = []
            else:
                lead_lines.append(line)
                lead_word_count += len(stripped.split())
        else:
            if is_header:
                # Save previous section
                if current_section_lines:
                    sections.append({
                        "name": current_section_name,
                        "text": "\n".join(current_section_lines).strip(),
                    })
                current_section_name = stripped
                current_section_lines = []
            else:
                current_section_lines.append(line)

    # Save last section
    if current_section_lines:
        sections.append({
            "name": current_section_name,
            "text": "\n".join(current_section_lines).strip(),
        })

    lead_text = "\n".join(lead_lines).strip()

    # Fallback: if no sections found, use first 30% as lead
    if not sections:
        words = body_text.split()
        split_pt = max(50, len(words) // 4)
        lead_text = " ".join(words[:split_pt])
        remaining = " ".join(words[split_pt:])
        sections = [{"name": "Body", "text": remaining}]

    return {
        "full_text":            body_text,
        "lead":                 lead_text,
        "sections":             sections,
        "references_excluded":  refs_excluded,
    }


def word_count(text: str) -> int:
    return len(text.split())


def sentence_count(text: str) -> int:
    sentences = _SENTENCE_SPLIT_RE.split(text.strip())
    return len([s for s in sentences if len(s.split()) >= 3])


def type_token_ratio(text: str) -> float:
    """Lexical diversity: unique words / total words."""
    tokens = re.findall(r"\b[a-z]+\b", text.lower())
    if not tokens:
        return 0.0
    return round(len(set(tokens)) / len(tokens), 4)


def avg_sentence_length(text: str) -> float:
    """Mean words per sentence."""
    sentences = [s for s in _SENTENCE_SPLIT_RE.split(text.strip()) if len(s.split()) >= 3]
    if not sentences:
        return 0.0
    return round(sum(len(s.split()) for s in sentences) / len(sentences), 2)


def analyze_article(article_meta: dict) -> dict:
    """Parse one article PDF and compute all structural metrics."""
    path = DOCS_DIR / article_meta["file"]
    if not path.exists():
        return {"error": f"File not found: {path}", **article_meta}

    raw_text = extract_pdf_text(path)
    split    = split_lead_and_sections(raw_text)

    lead_text = split["lead"]
    sections  = split["sections"]
    full_text = split["full_text"]

    lead_wc   = word_count(lead_text)
    total_wc  = word_count(full_text)
    n_sects   = max(1, len(sections))

    # Section word counts
    section_wcs = [word_count(s["text"]) for s in sections]
    body_wc     = sum(section_wcs)

    compression_ratio = round(lead_wc / max(1, total_wc), 4)
    section_density   = round(total_wc / n_sects, 1)

    # Grammar patterns on lead vs body
    grammar_lead = GrammarPatterns(language="english").extract([lead_text])
    body_texts   = [s["text"] for s in sections if s["text"].strip()]
    grammar_body = GrammarPatterns(language="english").extract(body_texts) if body_texts else {}

    # Type-token ratios (density proxy)
    ttr_lead = type_token_ratio(lead_text)
    ttr_body = type_token_ratio(" ".join(body_texts))
    ttr_full = type_token_ratio(full_text)

    # Avg sentence lengths
    asl_lead = avg_sentence_length(lead_text)
    asl_body = avg_sentence_length(" ".join(body_texts))

    # Subordination ratio (lead vs body): higher = more embedding = more compression
    lead_sub_coord = grammar_lead.get("clause_types", {}).get("sub_to_coord", 0.0) if grammar_lead else 0.0
    body_sub_coord = grammar_body.get("clause_types", {}).get("sub_to_coord", 0.0) if grammar_body else 0.0

    return {
        "title":             article_meta["title"],
        "file":              article_meta["file"],
        "subject":           article_meta["subject"],
        # Counts
        "total_words":       total_wc,
        "lead_words":        lead_wc,
        "body_words":        body_wc,
        "n_sections":        n_sects,
        "lead_sentences":    sentence_count(lead_text),
        # Compression metrics
        "compression_ratio": compression_ratio,    # lower = more compressed lead
        "section_density":   section_density,      # words per section
        # Lexical
        "ttr_lead":          ttr_lead,             # type-token ratio of lead
        "ttr_body":          ttr_body,
        "ttr_full":          ttr_full,
        # Sentence structure
        "avg_sentence_length_lead": asl_lead,
        "avg_sentence_length_body": asl_body,
        # Clause embedding (subordination as compression proxy)
        "sub_to_coord_lead": lead_sub_coord,
        "sub_to_coord_body": body_sub_coord,
        # Raw data
        "sections":          sections,
        "lead_text":         lead_text,
        "body_texts":        body_texts,
        "grammar_lead":      grammar_lead,
        "grammar_body":      grammar_body,
    }


def build_article_trajectory(analysis: dict) -> Optional[TrajectoryLog]:
    """
    Build a TrajectoryLog for one article.

    Each section = one step.
    Lead = step 0 (the "pre-collapse" compressed state).
    Body sections = steps 1..N.

    possibility_breadth = section_word_count / max_section_word_count
    (lead should be low breadth = compressed; body sections = higher breadth)
    constraint_proxy = normalized section index (early sections more constrained
                       by editorial lead compression)

    The "compression event" = transition from lead to body.
    """
    if "error" in analysis:
        return None

    lead_text = analysis["lead_text"]
    sections  = analysis["sections"]

    all_steps = [{"name": "Lead", "text": lead_text}] + [
        {"name": s["name"], "text": s["text"]}
        for s in sections
        if s["text"].strip()
    ]

    if len(all_steps) < 2:
        return None

    wcs = [word_count(s["text"]) for s in all_steps]
    max_wc = max(wcs) if wcs else 1

    events: list[TrajectoryEvent] = []
    breadth_series: list[float]    = []
    collapse_step: Optional[int]   = None

    for step_idx, step_data in enumerate(all_steps):
        wc = wcs[step_idx]
        # Lead is compressed (low breadth relative to body sections)
        breadth    = max(0.0, min(1.0, wc / max_wc))
        constraint = max(0.0, min(1.0, 1.0 - step_idx / max(1, len(all_steps) - 1)))

        breadth_series.append(breadth)
        tension = estimate_tension(breadth_series)

        # Collapse = first body section (transition from compressed lead to full elaboration)
        is_collapse = (step_idx == 1)
        if is_collapse:
            collapse_step = step_idx

        morphology_str: Optional[str] = None
        if is_collapse:
            # The body sections expand from the compressed lead → DISSOLUTIVE
            # (possibility-space *opens* back up after lead compression)
            morphology_str = "DISSOLUTIVE"

        ttr  = type_token_ratio(step_data["text"])
        asl  = avg_sentence_length(step_data["text"])

        events.append(TrajectoryEvent(
            step                = step_idx,
            possibility_breadth = round(breadth, 4),
            constraint_proxy    = round(constraint, 4),
            tension_proxy       = round(tension, 4),
            state_summary       = {
                "section_name":   step_data["name"],
                "word_count":     wc,
                "ttr":            ttr,
                "avg_sent_len":   asl,
                "is_lead":        (step_idx == 0),
                "constraint_class": "internal",
                "fixture":        "wiki_article",
            },
            collapse_flag       = is_collapse,
            collapse_morphology = morphology_str,
            schema_version      = EVENT_SCHEMA_VERSION,
        ))

    if collapse_step is not None:
        pcn = estimate_post_collapse_narrowing(breadth_series, collapse_step)
        events[collapse_step].post_collapse_narrowing = pcn

    qualification = compute_qualification_status(
        has_possibility_proxy = True,
        has_constraint_proxy  = True,
        has_tension_proxy     = any(e.tension_proxy > 0 for e in events),
        has_collapse_proxy    = collapse_step is not None,
        has_post_collapse     = (collapse_step is not None and
                                 events[collapse_step].post_collapse_narrowing is not None),
    )

    title = analysis["title"]
    return TrajectoryLog(
        fixture_id           = "wiki_article",
        fixture_type         = "Wikipedia Article Structural Probe",
        run_id               = f"wiki_article_{title.lower().replace(' ', '_')}",
        seed                 = hash(title) % (2**31),
        config               = {
            "title":             title,
            "subject":           analysis["subject"],
            "n_sections":        analysis["n_sections"],
            "total_words":       analysis["total_words"],
            "compression_ratio": analysis["compression_ratio"],
        },
        events               = events,
        collapse_step        = collapse_step,
        final_morphology     = "DISSOLUTIVE",
        qualification_status = qualification,
        schema_version       = LOG_SCHEMA_VERSION,
    )


def print_comparison_table(analyses: list[dict]) -> None:
    """Print comparison table across all 5 articles."""
    valid = [a for a in analyses if "error" not in a]
    if not valid:
        print("No valid analyses.")
        return

    print(f"\n{'='*100}")
    print("=== WIKIPEDIA ARTICLE STRUCTURAL COMPARISON ===")
    print(f"{'='*100}")
    print(
        f"  {'Article':<32} {'Words':>6} {'Lead':>5} {'Sects':>5} "
        f"{'Compress':>9} {'SectDens':>9} {'TTR-Lead':>9} {'TTR-Body':>9} "
        f"{'ASL-Lead':>9} {'ASL-Body':>9} {'Sub/Coord-L':>12}"
    )
    print(
        f"  {'-'*32} {'-'*6} {'-'*5} {'-'*5} "
        f"{'-'*9} {'-'*9} {'-'*9} {'-'*9} "
        f"{'-'*9} {'-'*9} {'-'*12}"
    )
    for a in valid:
        print(
            f"  {a['title']:<32} {a['total_words']:>6} {a['lead_words']:>5} "
            f"{a['n_sections']:>5} {a['compression_ratio']:>9.4f} "
            f"{a['section_density']:>9.1f} {a['ttr_lead']:>9.4f} "
            f"{a['ttr_body']:>9.4f} {a['avg_sentence_length_lead']:>9.2f} "
            f"{a['avg_sentence_length_body']:>9.2f} "
            f"{a['sub_to_coord_lead']:>12.4f}"
        )

    print("\n  Notes:")
    print("    Compress = lead_words / total_words (lower = more compressed lead)")
    print("    SectDens = total_words / n_sections")
    print("    TTR      = type-token ratio (lexical diversity)")
    print("    ASL      = avg sentence length in words")
    print("    Sub/Coord-L = subordinator/coordinator ratio in lead (higher = more embedded)")


def print_dcp_comparison(analyses: list[dict], traj_pairs: list[tuple]) -> None:
    """Print DCP scores for each article trajectory."""
    print(f"\n{'='*70}")
    print("=== WIKIPEDIA ARTICLE DCP SCORES ===")
    print(f"{'='*70}")
    print(f"  {'Article':<32} {'DCP':>7} {'Qual':<15} {'Collapse':>9} {'Morph':<18}")
    print(f"  {'-'*32} {'-'*7} {'-'*15} {'-'*9} {'-'*18}")

    for a, (log, dcp) in zip(analyses, traj_pairs):
        if "error" in a or log is None:
            print(f"  {a['title']:<32}  -- SKIPPED --")
            continue
        score = dcp.domain_metadata.get("dcp_composite", 0.0)
        print(
            f"  {a['title']:<32} {score:>7.4f} {dcp.qualification_status():<15} "
            f"{str(log.collapse_step):>9} {str(log.final_morphology):<18}"
        )


def print_compression_interpretation(analyses: list[dict]) -> None:
    """Print the DCP compression interpretation for each article."""
    print(f"\n{'='*70}")
    print("=== IS THE LEAD A GENUINE COMPRESSION EVENT? ===")
    print(f"{'='*70}")
    print(
        "  Hypothesis: Wikipedia lead = identity-preserving compression.\n"
        "  Evidence: lead should show HIGH lexical density (high TTR),\n"
        "  LONG sentence structures (high ASL), HIGH subordination,\n"
        "  relative to body sections.\n"
    )

    for a in analyses:
        if "error" in a:
            print(f"  [{a['title']}] SKIPPED: {a['error']}")
            continue

        ttr_delta  = a["ttr_lead"] - a["ttr_body"]
        asl_delta  = a["avg_sentence_length_lead"] - a["avg_sentence_length_body"]
        sub_delta  = a["sub_to_coord_lead"] - a["sub_to_coord_body"]

        # Evidence score: positive = lead is denser than body (supports compression thesis)
        evidence_count = sum([ttr_delta > 0, asl_delta > 0, sub_delta > 0])
        verdict = {3: "STRONG", 2: "MODERATE", 1: "WEAK", 0: "NO"}.get(evidence_count, "?")

        print(
            f"  [{a['title']}]"
            f" TTR Δ={ttr_delta:+.4f}  ASL Δ={asl_delta:+.2f}  Sub/Coord Δ={sub_delta:+.4f}"
            f"  →  {verdict} compression evidence ({evidence_count}/3 signals)"
        )


def main() -> None:
    print("Analyzing 5 Wikipedia articles as formal corpus...")
    print(f"Docs directory: {DOCS_DIR}")
    print()

    analyses = []
    for art in ARTICLES:
        print(f"  Parsing: {art['file']}...")
        a = analyze_article(art)
        if "error" in a:
            print(f"    ERROR: {a['error']}")
        else:
            print(
                f"    {a['total_words']:,} words | {a['n_sections']} sections | "
                f"lead={a['lead_words']} words | compression={a['compression_ratio']:.4f}"
            )
        analyses.append(a)

    # Build trajectories and DCP events
    traj_pairs = []
    for a in analyses:
        log = build_article_trajectory(a)
        if log is None:
            traj_pairs.append((None, None))
        else:
            dcp = extract_dcp_event(log)
            traj_pairs.append((log, dcp))

    print_comparison_table(analyses)
    print_dcp_comparison(analyses, traj_pairs)
    print_compression_interpretation(analyses)

    # Section-level detail for the most compressed article
    valid_analyses = [(a, i) for i, a in enumerate(analyses) if "error" not in a]
    if valid_analyses:
        most_compressed = min(valid_analyses, key=lambda x: x[0]["compression_ratio"])
        a_mc, idx_mc    = most_compressed
        print(f"\n{'='*70}")
        print(f"=== SECTION DETAIL: {a_mc['title']} (most compressed lead) ===")
        print(f"{'='*70}")
        for s in a_mc["sections"][:8]:
            wc  = word_count(s["text"])
            ttr = type_token_ratio(s["text"])
            asl = avg_sentence_length(s["text"])
            print(f"  [{s['name'][:30]:<30}] {wc:>5} words | TTR={ttr:.4f} | ASL={asl:.1f}")

    print(f"\nDone. {len([a for a in analyses if 'error' not in a])}/5 articles analyzed.")


if __name__ == "__main__":
    main()
