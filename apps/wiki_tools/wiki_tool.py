"""
wiki_tool.py — Wikipedia operator CLI.

Wraps domains/language/wikipedia/operator for command-line use.
No live Wikipedia edits. Read-only.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from domains.language.wikipedia.operator import WikiOperator


def main() -> None:
    op = WikiOperator()

    if len(sys.argv) < 2:
        op.status()
        print()
        print("Commands:")
        print("  status                          — system overview")
        print("  account                         — edit history summary")
        print("  mine                            — mine edit history for patterns")
        print("  ingest-corpus                   — fetch operator profile + rule corpus from Wikipedia")
        print("  ingest-gold                     — fetch gold article corpus + dossiers (Phase 1.2)")
        print("  ingest-templates                — fetch template families from gold corpus (Phase 1.3)")
        print("  patterns                        — list pattern library")
        print("  dossiers                        — list template family dossiers")
        print("  dossier  <family|template>      — print a dossier")
        print("  rules    [context]              — check rules for a context")
        print("  resolve-rules <context>         — rule precedence with archetype awareness (Phase 1.4)")
        print("  inspect  <template>             — fetch + summarize a template")
        print("  index    <template> [...]       — fetch + cache templates")
        print("  expand   <wikitext>             — expandtemplates sandbox")
        print("  explain  <wikitext>             — explain wikitext logic")
        print("  suggest  <wikitext>             — suggest rewrites from pattern library")
        print("  validate <wikitext>             — sandbox + anti-patterns + rules")
        print("  solve    <wikitext>             — full solve-time diagnostic (Phase 1.4)")
        print("  inspect-issue <wikitext>        — quick issue diagnostic (Phase 1.4)")
        print("  find-family <template|snippet>  — identify template family (Phase 1.4)")
        print("  match-patterns <snippet>        — operator pattern match (Phase 1.4)")
        print("  rewrite  <snippet>              — family-safe rewrite suggestions (Phase 1.5)")
        print("  propose  <issue description>    — family-aware patch proposal (Phase 1.5)")
        print("  rank-rewrites <snippet>         — rank all rewrite options by family (Phase 1.5)")
        print("  family-validation [family]      — family-specific validation steps (Phase 1.5)")
        return

    cmd = sys.argv[1].lower()

    if cmd == "status":
        op.status()

    elif cmd == "account":
        acct = op.account()
        ts = acct.template_summary
        print(f"User          : {acct.username}")
        print(f"Total edits   : {acct.total_edits:,}")
        print(f"By project    : {acct.by_project}")
        print(f"Template-ns   : {ts.total_template_ns_edits:,}")
        print(f"Infobox edits : {ts.total_infobox_edits:,}")
        if ts.top_templates_edited:
            print("Top templates:")
            for t in ts.top_templates_edited[:10]:
                print(f"  {t['edits']:>5}  {t['title']}")

    elif cmd == "patterns":
        op.patterns()

    elif cmd == "inspect" and len(sys.argv) >= 3:
        op.inspect(" ".join(sys.argv[2:]))

    elif cmd == "index" and len(sys.argv) >= 3:
        op.index(sys.argv[2:])

    elif cmd == "expand" and len(sys.argv) >= 3:
        op.expand(" ".join(sys.argv[2:]))

    elif cmd == "explain" and len(sys.argv) >= 3:
        op.explain(" ".join(sys.argv[2:]))

    elif cmd == "suggest" and len(sys.argv) >= 3:
        op.suggest(" ".join(sys.argv[2:]))

    elif cmd == "mine":
        op.mine()

    elif cmd == "ingest-corpus":
        op.ingest_corpus()

    elif cmd == "ingest-gold":
        op.ingest_gold_corpus()

    elif cmd == "ingest-templates":
        op.ingest_template_families()

    elif cmd == "dossiers":
        op.dossiers()

    elif cmd == "dossier" and len(sys.argv) >= 3:
        op.dossier(" ".join(sys.argv[2:]))

    elif cmd == "rules":
        context = " ".join(sys.argv[2:]) if len(sys.argv) >= 3 else ""
        op.rules(context)

    elif cmd == "validate" and len(sys.argv) >= 3:
        op.validate(" ".join(sys.argv[2:]))

    # ------------------------------------------------------------------
    # Phase 1.4 — Solve-time reasoning commands
    # ------------------------------------------------------------------

    elif cmd == "solve" and len(sys.argv) >= 3:
        # Full three-truth diagnostic on a snippet
        op.solve(snippet=" ".join(sys.argv[2:]))

    elif cmd == "inspect-issue" and len(sys.argv) >= 3:
        # Quick diagnostic without patch
        op.inspect_issue(snippet=" ".join(sys.argv[2:]))

    elif cmd == "find-family" and len(sys.argv) >= 3:
        op.find_family(" ".join(sys.argv[2:]))

    elif cmd == "resolve-rules" and len(sys.argv) >= 3:
        op.resolve_rules(" ".join(sys.argv[2:]))

    elif cmd == "match-patterns" and len(sys.argv) >= 3:
        op.match_operator_patterns(" ".join(sys.argv[2:]))

    # ------------------------------------------------------------------
    # Phase 1.5 — Family-aware rewrite engine
    # ------------------------------------------------------------------

    elif cmd == "rewrite" and len(sys.argv) >= 3:
        op.rewrite(snippet=" ".join(sys.argv[2:]))

    elif cmd == "propose" and len(sys.argv) >= 3:
        op.propose_patch(issue_description=" ".join(sys.argv[2:]))

    elif cmd == "rank-rewrites" and len(sys.argv) >= 3:
        op.rank_rewrites(snippet=" ".join(sys.argv[2:]))

    elif cmd == "family-validation":
        family_id = sys.argv[2] if len(sys.argv) >= 3 else ""
        op.family_validation(family_id=family_id)

    else:
        print(f"[wiki] Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
