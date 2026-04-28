"""
wikipedia_editor_probe.py — Personal interest profiling via Wikipedia edit history
====================================================================================

Analyzes the Wikipedia edit record of Dissonance (Dissident93) as a ground-truth
behavioral corpus. 171,800 edits over 13.9 years reveal the actual structure of
the user's interests, expertise depth, and editorial style.

Key thesis: Concentrated, long-term Wikipedia editing on a topic is the highest-
confidence signal of genuine interest and expertise. An editor who makes 1,676 edits
to a single article knows that subject.

Analysis sections:
    1. User profile overview
    2. Topic pillar taxonomy — what are the actual knowledge domains?
    3. Expertise depth — which articles hit 500+ edits (deep expertise threshold)
    4. Quality class distribution — what quality levels does the editor target?
    5. Edit behavioral fingerprint — morphology, comment patterns, MOS literacy
    6. Helix cross-domain alignment — what does this mean for Helix's domain coverage?
    7. Temporal origin arc — where did this start?

Data source: domains/language/model/data/datasets/wikipedia_dissident93.json
Run: python domains/language/model/probes/wikipedia_editor_probe.py
"""
from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = next(
    p for p in Path(__file__).resolve().parents
    if (p / "MANIFEST.yaml").exists() and (p / "core").is_dir()
)
sys.path.insert(0, str(ROOT))

FIXTURE = ROOT / "domains" / "language" / "data" / "datasets" / "wikipedia_dissident93.json"

# Domain display names
DOMAIN_LABELS = {
    "nfl_commanders":  "NFL / Washington Commanders",
    "nfl_general":     "NFL (general)",
    "video_games":     "Video Games",
    "vgm_composers":   "VGM Composers",
    "esports_dota":    "Esports / Dota 2",
    "gaming_industry": "Gaming Industry / Platforms",
    "music_producer":  "Music (other)",
    "other":           "Other",
}

# Quality class ordering (high → low)
QUALITY_ORDER = ["FA", "GA", "B", "C", "List", None]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_fixture() -> dict:
    with open(FIXTURE, encoding="utf-8") as f:
        return json.load(f)


def classify_morphology(sizediff: int) -> str:
    """Classify an edit by its net byte effect."""
    if sizediff > 100:
        return "GENERATIVE"
    elif sizediff < -100:
        return "DISSOLUTIVE"
    else:
        return "CIRCULAR"


def parse_edit_velocity(contribs: list[dict]) -> dict:
    """Estimate edits-per-day and session patterns from recent contributions."""
    if not contribs:
        return {}
    timestamps = sorted(c["timestamp"] for c in contribs)
    first_ts = timestamps[0]
    last_ts  = timestamps[-1]

    def ts_hours(ts: str) -> float:
        from datetime import datetime
        dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
        return dt.timestamp() / 3600

    span_hours = ts_hours(last_ts) - ts_hours(first_ts)
    span_days  = span_hours / 24 if span_hours > 0 else 1.0

    return {
        "sample_size":    len(contribs),
        "span_days":      round(span_days, 1),
        "edits_per_day":  round(len(contribs) / span_days, 1),
        "first_edit":     first_ts,
        "last_edit":      last_ts,
    }


def extract_comment_vocabulary(contribs: list[dict]) -> dict:
    """Analyze edit summary language patterns."""
    comments = [c["comment"].lower() for c in contribs if c.get("comment")]
    if not comments:
        return {}

    all_words = []
    for c in comments:
        words = re.findall(r"[a-z]{3,}", c)
        all_words.extend(words)

    stopwords = {"the", "and", "for", "this", "with", "from", "that", "have",
                 "more", "into", "not", "but", "are", "was", "also", "here"}
    filtered = [w for w in all_words if w not in stopwords]
    freq = Counter(filtered).most_common(20)

    mos_refs = sum(1 for c in comments if "mos" in c or "mos:" in c)
    source_refs = sum(1 for c in comments
                      if any(url in c for url in ["commanders.com", "espn", "nfl.com",
                                                   "http", "www.", ".com"]))
    cleanup_ops = sum(1 for c in comments
                      if any(op in c for op in ["cleanup", "trim", "clean", "remove",
                                                 "update", "fix", "correct"]))

    avg_len = sum(len(c) for c in comments) / len(comments)

    return {
        "comment_count":   len(comments),
        "avg_length_chars": round(avg_len, 1),
        "top_terms":       freq,
        "mos_references":  mos_refs,
        "source_url_refs": source_refs,
        "cleanup_ops":     cleanup_ops,
    }


# ---------------------------------------------------------------------------
# Section printers
# ---------------------------------------------------------------------------

def section_profile(data: dict) -> None:
    u = data["user"]
    print("=" * 70)
    print("SECTION 1 — User Profile")
    print("=" * 70)
    years = u["active_years"]
    daily_avg = u["editcount"] / (years * 365)
    print(f"  Username:      Dissident93 (user ID {u['userid']})")
    print(f"  Registered:    {u['registration'][:10]}")
    print(f"  Total edits:   {u['editcount']:,} over {years} years")
    print(f"  Daily average: {daily_avg:.1f} edits/day")
    print(f"  User groups:   {', '.join(u['groups'][:3])}")
    print(f"  Gender:        {u['gender']}")
    print()
    print("  Group significance:")
    print("  extendedconfirmed — 500+ edits, 30+ days; trusted editor, can edit semi-protected articles")
    print("  rollbacker        — granted for demonstrated ability to identify and revert vandalism")
    print("  templateeditor    — can edit template-protected content; significant vetting required")


def section_taxonomy(data: dict) -> None:
    print("\n" + "=" * 70)
    print("SECTION 2 — Topic Pillar Taxonomy")
    print("=" * 70)

    pages = data["top_edited_pages"]

    # Aggregate by domain
    domain_edits: dict[str, int] = defaultdict(int)
    domain_articles: dict[str, list] = defaultdict(list)
    for p in pages:
        d = p["domain"]
        domain_edits[d] += p["edit_count"]
        domain_articles[d].append(p)

    total_edits = sum(p["edit_count"] for p in pages)
    total_user_edits = data["user"]["editcount"]

    print(f"\n  Top-50 article edits: {total_edits:,} of {total_user_edits:,} total ({100*total_edits/total_user_edits:.1f}%)")
    print(f"\n  {'Domain':<38} {'Articles':>8} {'Edits':>8} {'%':>6}")
    print("  " + "-" * 62)

    for domain, edits in sorted(domain_edits.items(), key=lambda x: -x[1]):
        label = DOMAIN_LABELS.get(domain, domain)
        n_articles = len(domain_articles[domain])
        pct = 100 * edits / total_edits
        print(f"  {label:<38} {n_articles:>8} {edits:>8,} {pct:>5.1f}%")

    # Show top articles per major domain
    print()
    for domain in ["nfl_commanders", "esports_dota", "video_games", "vgm_composers"]:
        label = DOMAIN_LABELS[domain]
        print(f"  {label}:")
        top = sorted(domain_articles[domain], key=lambda x: -x["edit_count"])[:5]
        for p in top:
            qc = p["quality_class"] or "?"
            print(f"    {p['edit_count']:>5}  [{qc}]  {p['page_title']}")
        print()


def section_expertise_depth(data: dict) -> None:
    print("=" * 70)
    print("SECTION 3 — Expertise Depth (500+ edit threshold)")
    print("=" * 70)

    pages = data["top_edited_pages"]
    deep = [p for p in pages if p["edit_count"] >= 500]
    mid  = [p for p in pages if 200 <= p["edit_count"] < 500]

    print(f"\n  Articles with 500+ edits (deep expertise): {len(deep)}")
    for p in sorted(deep, key=lambda x: -x["edit_count"]):
        qc = p["quality_class"] or "?"
        label = DOMAIN_LABELS.get(p["domain"], p["domain"])
        print(f"    {p['edit_count']:>5}  [{qc}]  {p['page_title']:<45}  ({label})")

    print(f"\n  Articles with 200–499 edits (strong interest): {len(mid)}")
    for p in sorted(mid, key=lambda x: -x["edit_count"]):
        qc = p["quality_class"] or "?"
        print(f"    {p['edit_count']:>5}  [{qc}]  {p['page_title']}")


def section_quality_class(data: dict) -> None:
    print("\n" + "=" * 70)
    print("SECTION 4 — Quality Class Distribution")
    print("=" * 70)

    pages = data["top_edited_pages"]
    by_class: dict[str, list] = defaultdict(list)
    for p in pages:
        qc = p["quality_class"] or "unassessed"
        by_class[qc].append(p)

    total_edits = sum(p["edit_count"] for p in pages)

    print(f"\n  {'Class':<12} {'Articles':>8} {'Total edits':>12} {'%':>6}  Interpretation")
    print("  " + "-" * 75)
    class_order = ["FA", "GA", "B", "C", "List", "unassessed"]
    interp = {
        "FA": "Featured Article — Wikipedia's highest quality",
        "GA": "Good Article — reviewed, sourced, well-written",
        "B": "B-class — mostly complete but not formally reviewed",
        "C": "C-class — incomplete but readable",
        "List": "List article",
        "unassessed": "Not yet assessed",
    }
    for qc in class_order:
        arts = by_class.get(qc, [])
        if not arts:
            continue
        edits = sum(p["edit_count"] for p in arts)
        pct = 100 * edits / total_edits
        print(f"  {qc:<12} {len(arts):>8} {edits:>12,} {pct:>5.1f}%  {interp[qc]}")

    # High-quality attractor
    high_q_classes = {"FA", "GA"}
    high_q_edits = sum(p["edit_count"] for p in pages if p["quality_class"] in high_q_classes)
    print(f"\n  FA+GA combined: {100*high_q_edits/total_edits:.1f}% of top-50 article edits")
    print("  → The editor concentrates work on high-quality or quality-bound articles.")


def section_behavioral_fingerprint(data: dict) -> None:
    print("\n" + "=" * 70)
    print("SECTION 5 — Edit Behavioral Fingerprint")
    print("=" * 70)

    contribs = data["recent_contributions"]
    ns_data   = data["namespace_sample"]

    # Morphology distribution
    morphs = Counter(classify_morphology(c["sizediff"]) for c in contribs)
    total  = len(contribs)
    print(f"\n  Edit morphology (recent {total} edits):")
    for m in ["GENERATIVE", "CIRCULAR", "DISSOLUTIVE"]:
        n = morphs.get(m, 0)
        bar = "█" * (n // 2)
        print(f"    {m:<15} {n:>3} ({100*n/total:4.1f}%)  {bar}")

    # Net bytes
    net_added   = ns_data["net_bytes_added"]
    net_removed = ns_data["net_bytes_removed"]
    net         = ns_data["net_bytes_change"]
    print(f"\n  Net bytes ({ns_data['period']}, n={ns_data['sample_size']}):")
    print(f"    Added:    +{net_added:,}")
    print(f"    Removed:  -{net_removed:,}")
    print(f"    Net:       {net:+,}  (near-zero = CIRCULAR maintenance attractor)")

    # Namespace distribution
    dist = ns_data["distribution"]
    print(f"\n  Namespace distribution (same period, n={ns_data['sample_size']}):")
    for ns_name, count in sorted(dist.items(), key=lambda x: -x[1]):
        pct = 100 * count / ns_data["sample_size"]
        ns_label = ns_name.split("_", 1)[1] if "_" in ns_name else ns_name
        print(f"    {ns_label:<20} {count:>4} ({pct:4.1f}%)")

    # Edit velocity
    vel = parse_edit_velocity(contribs)
    print(f"\n  Edit velocity (recent sample):")
    print(f"    {vel['sample_size']} edits over {vel['span_days']} days = {vel['edits_per_day']} edits/day")

    # Comment register
    vocab = extract_comment_vocabulary(contribs)
    print(f"\n  Edit comment register:")
    print(f"    Average length: {vocab['avg_length_chars']} chars (terse; median Wikipedia comment ~30 chars)")
    print(f"    MOS references: {vocab['mos_references']} (Manual of Style citations in summaries)")
    print(f"    Source URL refs: {vocab['source_url_refs']}")
    print(f"    Cleanup ops:    {vocab['cleanup_ops']} (cleanup/trim/remove/fix)")
    print(f"\n  Top comment terms: {[t for t, _ in vocab['top_terms'][:12]]}")

    # Minor edits ratio
    minor_count = sum(1 for c in contribs if c.get("minor"))
    print(f"\n  Minor edits: {minor_count}/{total} ({100*minor_count/total:.0f}%)")
    top_flag    = sum(1 for c in contribs if c.get("top"))
    print(f"  \"Top\" edits (currently live): {top_flag}/{total} ({100*top_flag/total:.0f}%)")


def section_helix_alignment(data: dict) -> None:
    print("\n" + "=" * 70)
    print("SECTION 6 — Helix Cross-Domain Alignment")
    print("=" * 70)

    pages = data["top_edited_pages"]
    overlap = data["helix_cross_domain_overlap"]

    music_pages = overlap["music_domain"]
    games_pages = overlap["games_domain"]

    print("\n  Articles in top-50 that overlap with Helix music domain:")
    for title in music_pages:
        page = next((p for p in pages if p["page_title"] == title), None)
        if page:
            print(f"    {page['edit_count']:>5} edits  [{page['quality_class'] or '?'}]  {title}")
        else:
            print(f"    (recent edit, not in top-50)     {title}")

    print("\n  Articles in top-50 that overlap with Helix games domain:")
    for title in games_pages:
        page = next((p for p in pages if p["page_title"] == title), None)
        if page:
            print(f"    {page['edit_count']:>5} edits  [{page['quality_class'] or '?'}]  {title}")

    # VGM composer articles that Helix tracks for S3K + music domain
    vgm_helix_overlap = [
        "Yasunori Mitsuda", "Yoko Shimomura", "Nobuo Uematsu",
        "Motoi Sakuraba", "Yuzo Koshiro", "Koichi Sugiyama", "Koji Kondo",
    ]
    vgm_total = sum(p["edit_count"] for p in pages if p["page_title"] in vgm_helix_overlap)
    print(f"\n  VGM composer articles total edits: {vgm_total:,}")
    print("  These composers are tracked in the Helix music domain codex.")
    print("  The S3K analysis already cross-references Yuzo Koshiro (SMPS lineage),")
    print("  Yoko Shimomura, and Nobuo Uematsu as calibration context.")

    print()
    print("  Sega article (FA) — 331 edits:")
    print("  The Sega Wikipedia article is Featured Article quality. This edit")
    print("  investment validates the S3K research context: the editor knows Sega")
    print("  corporate history at FA depth, not just Sonic-specific knowledge.")

    print()
    print("  Helix domain mapping from Wikipedia edit corpus:")
    mapping = {
        "music":    ["Sega", "Sonic Mania", "Yasunori Mitsuda", "Nobuo Uematsu",
                     "Yoko Shimomura", "Motoi Sakuraba", "Yuzo Koshiro",
                     "Koichi Sugiyama", "Koji Kondo", "Masayoshi Soken"],
        "games":    ["Dota 2", "The International (all years)", "Elden Ring",
                     "Dark Souls series", "Hidetaka Miyazaki", "FromSoftware",
                     "Persona 5", "Trails series", "OG (esports)"],
        "language": ["(editorial work itself = language domain practice)"],
        "cognition":["(Wikipedia editorial policy navigation = constraint satisfaction)"],
    }
    for domain, articles in mapping.items():
        print(f"    core/engine/{domain}: {', '.join(articles[:4])}{'...' if len(articles) > 4 else ''}")


def section_temporal_arc(data: dict) -> None:
    print("\n" + "=" * 70)
    print("SECTION 7 — Temporal Origin Arc")
    print("=" * 70)

    first = data["first_edits"]
    print("\n  First Wikipedia edits (May–June 2012):")
    for e in first:
        label = DOMAIN_LABELS.get(e["domain"], e["domain"])
        print(f"    {e['timestamp'][:10]}  {e['title']:<35}  [{label}]")

    print()
    print("  Arc interpretation:")
    print("  2012:        VGM composers + video games exclusively")
    print("               First edit: Motoaki Takenouchi (game composer)")
    print("               Origin interest: game music ← matches S3K research")
    print()
    print("  ~2014–2016:  Games expand. Dota 2 becomes a major focus (~1,585 edits).")
    print("               Persona 5, Zelda BotW, Rocket League accumulating.")
    print("               The International coverage begins.")
    print()
    print("  ~2019–2020:  Washington Commanders become the heaviest single pillar.")
    print("               Jayden Daniels (1,676), Josh Harris (1,329),")
    print("               Washington Commanders (1,143) overtake Dota 2 (1,585).")
    print()
    print("  2026:        All three pillars run concurrently.")
    print("               Same-day edits (2026-03-29): Masayoshi Soken (VGM) →")
    print("               Commanders roster → Dark Souls (games).")
    print("               The original 2012 interest (VGM) persists alongside new ones.")
    print()
    print("  Structural invariant:")
    print("  The interest set EXPANDS but does not REPLACE. VGM composers from 2012")
    print("  are still edited in 2026. This is an additive interest architecture,")
    print("  not a sequential displacement pattern.")


def section_summary(data: dict) -> None:
    print("\n" + "=" * 70)
    print("SUMMARY — Dissonance / Dissident93 Interest Profile")
    print("=" * 70)

    pages = data["top_edited_pages"]
    total_top50 = sum(p["edit_count"] for p in pages)

    print(f"""
  Wikipedia record: {data['user']['editcount']:,} edits over {data['user']['active_years']} years
  User class: extendedconfirmed + rollbacker + templateeditor

  Primary knowledge pillars (by editorial depth):
    1. Washington Commanders / NFL
       — Jayden Daniels, Josh Harris, Chase Young, Washington Commanders,
         New Commanders Stadium, Ron Rivera, 2024 season + roster players
       — Pattern: tracks every roster move, ownership development, stadium project

    2. Video Games (broad)
       — Persona 5, Elden Ring/Dark Souls, Trails series, Zelda BotW,
         Rocket League, Stardew Valley, Witcher 3, Mario Odyssey, PUBG
       — Quality focus: GA is the dominant class (most deeply edited game articles are GA)

    3. Dota 2 / Esports
       — Dota 2 itself (1,585 edits), The International history (all years),
         OG esports, Artifact
       — Likely overlap with active Dota 2 player history

    4. Video Game Music Composers (origin domain)
       — Yasunori Mitsuda, Nobuo Uematsu, Yoko Shimomura, Motoi Sakuraba,
         Yuzo Koshiro, Koichi Sugiyama, Koji Kondo, Masayoshi Soken
       — Origin: first edits in 2012 were VGM composers
       — Direct overlap with Helix music domain research

    5. Gaming Industry / Platforms
       — Sega (FA — highest quality), Steam (GA), Nintendo EP&D, Switch games
       — Sega FA authorship validates depth of S3K research context

  Edit style signature:
    — Net-neutral bytes (CIRCULAR maintenance attractor)
    — Terse, MOS-literate, source-URL-referencing comments
    — High "top" rate (edits stick; not reverted)
    — 77% mainspace, 16% templates

  Helix alignment:
    — music domain: Sega, Sonic Mania, 8 VGM composer articles
    — games domain: Dota 2, From Software games, Persona 5, esports history
    — The Wikipedia record confirms Helix's domain coverage is NOT arbitrary;
      it maps directly to where Dissonance has real, demonstrated expertise.
""")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading Wikipedia user fixture...")
    data = load_fixture()
    print(f"  User: {data['user']['name']}  ({data['user']['editcount']:,} total edits)")
    print(f"  Top pages: {len(data['top_edited_pages'])}  |  Recent contribs: {len(data['recent_contributions'])}")
    print()

    section_profile(data)
    section_taxonomy(data)
    section_expertise_depth(data)
    section_quality_class(data)
    section_behavioral_fingerprint(data)
    section_helix_alignment(data)
    section_temporal_arc(data)
    section_summary(data)

    print("=" * 70)
    print("Done.")


if __name__ == "__main__":
    main()

