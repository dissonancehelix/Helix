"""
WikiOperator — top-level entry point for the Wikipedia operator subsystem.

Ties together account_ingest, template_index, sandbox, pattern_library,
and issue_solver into a single coherent interface.

Operator account: Dissident93

Usage:
    from apps.language_pipeline.operator import WikiOperator

    op = WikiOperator()

    # Account / history
    account = op.account()
    print(account.template_summary.total_template_ns_edits)

    # Template work
    summary = op.inspect("Infobox NFL player")
    op.index(["Infobox NFL player", "Infobox person"])

    # Sandbox
    result = op.expand("{{#if:{{{name|}}}|{{{name|}}}|Unknown}}")
    cmp    = op.compare(old_wikitext, new_wikitext)

    # Pattern + issue solving
    patches = op.suggest(snippet)
    patch   = op.propose("parameter renders literal braces when absent", snippet)

    # Print full status
    op.status()

No live Wikipedia edits are performed.
"""
from __future__ import annotations

import json
from pathlib import Path

from apps.language_pipeline import OPERATOR_USERNAME
from apps.language_pipeline.account_ingest import AccountIngest, AccountIngestResult
from apps.language_pipeline.template_index import TemplateIndexer, TemplateRecord
from apps.language_pipeline.sandbox import SandboxValidator, ValidationResult, CompareResult
from apps.language_pipeline.pattern_library import PATTERN_LIBRARY, WikiPattern
from apps.language_pipeline.issue_solver import IssueSolver
from apps.language_pipeline.issue_solver.solver import PatchProposal, TemplateSummary
from apps.language_pipeline.pattern_mining import PatternMiner, MiningReport
from apps.language_pipeline.dossiers import DOSSIER_REGISTRY, TemplateFamilyDossier, find_dossiers_for_template
from apps.language_pipeline.rule_engine import RuleEngine
from apps.language_pipeline.patch_critic import PatchCritic, CritiqueResult
from apps.language_pipeline.corpus_ingest import CorpusIngestor
from apps.language_pipeline.gold_corpus import GoldCorpusIngestor, GoldCorpusReport
from apps.language_pipeline.template_families import TemplateFamilyIngestor, TemplateFamilyIngestReport
from apps.language_pipeline.solve_time import (
    SolveTimeReasoner, SolveTimeInput, SolveTimeResult,
)
from apps.language_pipeline.solve_time.rewrite_engine import (
    FamilyAwareRewriteEngine, FamilyPatchProposal, FamilyRewriteOption,
)


class WikiOperator:
    """
    Unified operator interface for Wikipedia/wikitext work.

    All state is lazy-loaded — instantiation is free.
    """

    def __init__(self, username: str = OPERATOR_USERNAME):
        self.username = username
        self._ingest   = AccountIngest(username)
        self._indexer  = TemplateIndexer()
        self._sandbox  = SandboxValidator()
        self._solver   = IssueSolver()
        self._miner    = PatternMiner()
        self._rules    = RuleEngine()
        self._critic   = PatchCritic()
        self._corpus           = CorpusIngestor()
        self._gold_corpus      = GoldCorpusIngestor()
        self._template_families = TemplateFamilyIngestor()
        self._reasoner         = SolveTimeReasoner()
        self._rewriter         = FamilyAwareRewriteEngine()
        self._account_cache: AccountIngestResult | None = None
        self._mining_cache: MiningReport | None = None

    # ------------------------------------------------------------------
    # Account / history
    # ------------------------------------------------------------------

    def account(self, force_refresh: bool = False) -> AccountIngestResult:
        """
        Load operator account data from the artifact cache.
        Use force_refresh=True to re-fetch from the live API (slow).
        """
        if self._account_cache is None or force_refresh:
            if force_refresh:
                self._account_cache = self._ingest.from_api()
            else:
                self._account_cache = self._ingest.from_artifact()
        return self._account_cache

    # ------------------------------------------------------------------
    # Template index
    # ------------------------------------------------------------------

    def inspect(self, template_name: str) -> TemplateSummary:
        """Fetch and summarize a template. Prints result."""
        summary = self._solver.inspect_template(template_name)
        print(summary.display())
        return summary

    def index(self, template_names: list[str], save: bool = True) -> list[TemplateRecord]:
        """
        Fetch and optionally cache a list of templates.
        Writes per-template JSON + master index to the template_index cache.
        """
        records = self._indexer.fetch_many(template_names)
        if save:
            for r in records:
                self._indexer.save(r)
            idx = self._indexer.save_index(records)
            print(f"[wiki] Index saved: {idx}")
        return records

    def load(self, template_name: str) -> TemplateRecord | None:
        """Load a previously cached template record without hitting the API."""
        return self._indexer.load_cached(template_name)

    # ------------------------------------------------------------------
    # Sandbox / validation
    # ------------------------------------------------------------------

    def expand(self, wikitext: str, title: str = "Sandbox") -> ValidationResult:
        """Expand wikitext through action=expandtemplates."""
        result = self._sandbox.expand(wikitext, title)
        print(result.summary())
        return result

    def parse(self, wikitext: str, title: str = "Sandbox") -> ValidationResult:
        """Full parse through action=parse (heavier, returns HTML + sections)."""
        result = self._sandbox.parse(wikitext, title)
        print(result.summary())
        return result

    def compare(
        self,
        before: str,
        after: str,
        title: str = "Sandbox",
        mode: str = "expand",
    ) -> CompareResult:
        """Compare before/after wikitext. Returns risk classification."""
        cmp = self._sandbox.compare(before, after, title=title, mode=mode)
        print(cmp.summary())
        return cmp

    # ------------------------------------------------------------------
    # Pattern library + issue solver
    # ------------------------------------------------------------------

    def explain(self, snippet: str) -> str:
        """Explain what a wikitext snippet does in plain terms."""
        result = self._solver.explain_template_logic(snippet)
        print(result)
        return result

    def suggest(self, snippet: str) -> list[PatchProposal]:
        """Suggest safe rewrites for a snippet based on the pattern library."""
        proposals = self._solver.suggest_safe_rewrite(snippet)
        if not proposals:
            print("[wiki] No matching patterns found in library.")
        for p in proposals:
            print()
            print(p.display())
        return proposals

    def propose(
        self,
        issue_description: str,
        snippet: str = "",
        template_name: str = "",
    ) -> PatchProposal:
        """Propose a patch in the operator's style for a described issue."""
        patch = self._solver.propose_patch(issue_description, snippet, template_name)
        print(patch.display())
        return patch

    def patterns(self) -> None:
        """Print the full pattern library index."""
        print(f"Pattern library — {len(PATTERN_LIBRARY)} patterns\n")
        for p in PATTERN_LIBRARY:
            print(f"  [{p.risk.upper():6s}] {p.id:35s}  {p.name}")

    # ------------------------------------------------------------------
    # Phase 2 — pattern mining, dossiers, rules, patch critic
    # ------------------------------------------------------------------

    def mine(self, save: bool = True) -> MiningReport:
        """Mine edit history for recurring patterns. Reads artifact cache."""
        if self._mining_cache is None:
            self._mining_cache = self._miner.mine()
        if save:
            path = self._miner.save(self._mining_cache)
            print(f"[wiki] Mining report saved: {path}")
        print(self._mining_cache.display_summary())
        return self._mining_cache

    def dossier(self, family_id_or_template: str) -> None:
        """Print a template family dossier by family_id (nfl/vg/blp) or template name."""
        # Try direct family lookup first
        d = DOSSIER_REGISTRY.get(family_id_or_template.lower())
        if d is None:
            # Try by template name
            matches = find_dossiers_for_template(family_id_or_template)
            if not matches:
                print(f"[wiki] No dossier found for '{family_id_or_template}'. "
                      f"Available: {list(DOSSIER_REGISTRY.keys())}")
                return
            d = matches[0]
        print(d.display())

    def dossiers(self) -> None:
        """List all available template family dossiers."""
        for fid, d in DOSSIER_REGISTRY.items():
            print(f"  {fid:8s}  {d.family_name}  ({len(d.member_templates)} templates)")

    def rules(self, context: str = "", tags: list[str] | None = None) -> None:
        """Check rules for a context. tags: ['nfl', 'blp', 'vg']."""
        if not context:
            # List all policies
            from apps.language_pipeline.rule_engine.rules import _RULES
            policies: dict[str, int] = {}
            for r in _RULES:
                policies[r.policy_code] = policies.get(r.policy_code, 0) + 1
            for policy, count in sorted(policies.items()):
                print(f"  {policy:20s} {count} rules")
            return
        result = self._rules.check(context, tags=tags)
        print(result.display())

    def critique(
        self,
        before: str,
        after: str,
        context: str = "",
        tags: list[str] | None = None,
        template_name: str = "",
    ) -> CritiqueResult:
        """Run the patch critic on a before/after pair."""
        result = self._critic.critique(
            before, after,
            context=context, tags=tags,
            template_name=template_name,
            run_sandbox=False,
        )
        print(result.display())
        return result

    def ingest_gold_corpus(self) -> GoldCorpusReport:
        """
        Phase 1.2 — fetch the live gold article corpus + rule pages + operator profile.
        Builds article dossiers, archetypes, authorial patterns, rule crosswalk,
        and template-family prep. Saves all artifacts to domains/language/tools/wikimedia/.
        """
        from apps.language_pipeline.gold_corpus.ingestor import ALL_TITLES
        print(f"[wiki] Ingesting gold corpus ({len(ALL_TITLES)} pages)...")
        report = self._gold_corpus.run()
        print(f"  Fetched: {report.fetch_summary['ok']} ok, "
              f"{report.fetch_summary['errors']} errors, "
              f"{report.fetch_summary['total_wikitext_chars']:,} chars")
        print(f"  Dossiers built: {len(report.dossiers)}")
        written = self._gold_corpus.save(report)
        print("[wiki] Artifacts saved:")
        for name, path in written.items():
            print(f"  {path.name}")
        return report

    def ingest_template_families(self) -> TemplateFamilyIngestReport:
        """
        Phase 1.3 — live-fetch template families from the gold corpus priority queue.
        Builds per-family dossiers with param inventory, alias maps, fragility analysis,
        and article / policy crosswalks.
        Saves six artifacts to domains/language/tools/wikimedia/.
        """
        from apps.language_pipeline.template_families.extractor import load_prep_data, build_priority_queue
        prep = load_prep_data()
        queue = build_priority_queue(prep)
        core_count = sum(1 for e in queue if e["tier"] == "core")
        print(f"[wiki] Template family ingest: {len(queue)} templates in queue "
              f"({core_count} core)...")
        report = self._template_families.run()
        written = self._template_families.save(report)
        print(f"  Families built: {len(report.families)}")
        print(f"  Templates fetched: {report.fetch_summary.get('templates_fetched', 0)} "
              f"(ok={report.fetch_summary.get('ok', 0)}, "
              f"errors={report.fetch_summary.get('errors', 0)})")
        print("[wiki] Artifacts saved:")
        for name, path in written.items():
            print(f"  {path.name}")
        return report

    def ingest_corpus(self) -> None:
        """
        Fetch the operator profile (User:Dissident93) and the targeted rule corpus
        (MOS:VG, WP:NFL, MOS:Biography, MOS, WP:GNG) from the live Wikipedia API.
        Saves structured artifacts to domains/language/tools/wikimedia/.
        """
        print("[wiki] Ingesting operator profile...")
        profile = self._corpus.ingest_profile()
        print(f"  User:Dissident93 — {profile.wikitext and len(profile.wikitext) or 0} chars")
        print(f"  Domains: {profile.editing_domains}")

        print("[wiki] Ingesting rule corpus (5 pages)...")
        rules = self._corpus.ingest_rules()
        for r in rules:
            status = "OK" if not r.fetch_error else f"ERROR: {r.fetch_error}"
            print(f"  [{r.policy_code}] {status} — {len(r.key_statements)} key statements")

        written = self._corpus.save_all(profile, rules)
        print("\n[wiki] Artifacts saved:")
        for key, path in written.items():
            print(f"  {key:25s} {path.name}")

    def validate(self, wikitext: str, tags: list[str] | None = None) -> None:
        """Validate a snippet: sandbox + anti-patterns + rules."""
        result = self._solver.validate_snippet(wikitext, tags=tags)
        print(f"Verdict: {result['verdict']}")
        sb = result["sandbox"]
        if sb.errors:
            print(f"Sandbox errors: {sb.errors}")
        if sb.warnings:
            print(f"Sandbox warnings: {sb.warnings}")
        aps = result["anti_patterns"]
        if aps:
            print(f"Anti-patterns ({len(aps)}):")
            for ap in aps:
                print(f"  [{ap.severity}] {ap.name}")
        rc = result["rule_check"]
        if rc.verdict != "clear":
            print(f"Rules ({rc.verdict}):")
            for r in rc.hard_blocks + rc.soft_concerns:
                print(f"  [{r.policy_code}] {r.name}")

    # ------------------------------------------------------------------
    # Phase 1.4 — Solve-time reasoning
    # ------------------------------------------------------------------

    def solve(
        self,
        snippet: str = "",
        template_name: str = "",
        before: str = "",
        after: str = "",
        context: str = "",
        article_title: str = "",
        tags: list[str] | None = None,
        run_sandbox: bool = True,
    ) -> SolveTimeResult:
        """
        Full solve-time diagnostic.

        Produces a structured SolveTimeResult with three separate truth layers:
          rule_truth       — what the policies say
          mechanical_truth — what the code actually does (sandbox-backed)
          operator_truth   — how the operator usually handles this

        All operations are advisory-only. No Wikipedia edits.
        """
        inp = SolveTimeInput(
            template_name=template_name,
            snippet=snippet,
            before=before,
            after=after,
            context=context,
            article_title=article_title,
            tags=tags or [],
            run_sandbox=run_sandbox,
        )
        result = self._reasoner.inspect_issue(inp)
        print(result.display())
        return result

    def inspect_issue(
        self,
        snippet: str = "",
        template_name: str = "",
        context: str = "",
        article_title: str = "",
    ) -> SolveTimeResult:
        """
        Structured issue diagnostic (compact view). Wrapper around solve().
        Use for quick diagnose-in-place without a before/after patch.
        """
        return self.solve(
            snippet=snippet,
            template_name=template_name,
            context=context,
            article_title=article_title,
            run_sandbox=bool(snippet),
        )

    def find_family(self, template_or_snippet: str) -> None:
        """Print the template family for a template name or wikitext snippet."""
        result = self._reasoner.find_related_family(template_or_snippet)
        print(f"Family     : {result['family_id']}")
        print(f"Policies   : {', '.join(result['policy_codes'])}")
        print(f"Fragile params: {', '.join(result['fragile_params']) or 'none identified'}")

    def resolve_rules(
        self,
        context: str,
        archetype_hint: str = "",
        tags: list[str] | None = None,
    ) -> None:
        """
        Resolve rule precedence for a context, printing the three-truth rule layer.
        Optionally anchor to an explicit archetype (e.g. 'athlete_biography_nfl').
        """
        rule_truth = self._reasoner.resolve_rule_priority(
            context, archetype_hint=archetype_hint, tags=tags
        )
        print(rule_truth.display())

    def match_operator_patterns(self, snippet: str) -> None:
        """
        Find operator-style matches for a snippet.
        Shows both library patterns and mined history patterns separately.
        """
        result = self._reasoner.find_operator_style_matches(
            SolveTimeInput(snippet=snippet)
        )
        print(result.display())

    # ------------------------------------------------------------------
    # Phase 1.5 — Family-aware rewrite engine
    # ------------------------------------------------------------------

    def rewrite(
        self,
        snippet: str,
        family_id: str = "",
        archetype: str = "",
        context: str = "",
        tags: list[str] | None = None,
    ) -> FamilyPatchProposal:
        """
        Suggest family-safe rewrites for a snippet.

        Filters and ranks candidates by:
          family compatibility → mechanical safety → policy fit → operator style

        Advisory-only. No Wikipedia edits.
        """
        proposal = self._rewriter.suggest_family_safe_rewrite(
            snippet=snippet,
            family_id=family_id,
            archetype=archetype,
            context=context,
            tags=tags,
        )
        print(proposal.display())
        return proposal

    def propose_patch(
        self,
        issue_description: str,
        snippet: str = "",
        template_name: str = "",
        family_id: str = "",
        archetype: str = "",
        tags: list[str] | None = None,
    ) -> FamilyPatchProposal:
        """
        Propose a family-aware patch for a described issue.

        Upgrade of the Phase 2 propose_patch: outputs include family reasoning,
        preserved behaviors, family-specific risks, and concrete validation steps.
        Advisory-only. No Wikipedia edits.
        """
        proposal = self._rewriter.propose_family_patch(
            issue_description=issue_description,
            snippet=snippet,
            template_name=template_name,
            family_id=family_id,
            archetype=archetype,
            tags=tags,
        )
        print(proposal.display())
        return proposal

    def rank_rewrites(
        self,
        snippet: str,
        family_id: str = "",
        context: str = "",
    ) -> None:
        """
        Rank all candidate rewrite options for a snippet, showing family compat and score.
        """
        options = self._rewriter.rank_rewrite_options(
            snippet=snippet,
            family_id=family_id,
            context=context,
        )
        if not options:
            print("[wiki] No matching rewrite candidates found.")
            return
        print(f"Rewrite ranking — {len(options)} candidate(s):\n")
        for opt in options:
            compat_label = f"[{opt.family_compat.upper():6s}]"
            print(
                f"  {compat_label} [{opt.patch_class:22s}] "
                f"score={opt.rank_score:2d}  {opt.pattern_name}"
            )
            if opt.family_reasoning:
                print(f"             {opt.family_reasoning[:90]}")

    def family_validation(
        self,
        family_id: str = "",
        snippet: str = "",
    ) -> None:
        """
        Print family-specific validation steps for a family or snippet.
        """
        steps = self._rewriter.get_family_validation_advice(
            family_id=family_id,
            snippet=snippet,
        )
        detected = family_id or "auto-detected"
        print(f"Family validation steps [{detected}]:")
        for step in steps:
            print(f"  · {step}")

    def compare_patches(
        self,
        snippet: str,
        candidates: list[str],
        family_id: str = "",
        context: str = "",
    ) -> None:
        """
        Compare multiple proposed rewrites of the same snippet against the family.
        Each item in candidates is a concrete after-text string.
        """
        options = self._rewriter.compare_family_safe_patches(
            snippet=snippet,
            candidates=candidates,
            family_id=family_id,
            context=context,
        )
        print(f"Patch comparison — {len(options)} candidate(s):\n")
        for opt in options:
            print(f"  [{opt.family_compat.upper():6s}] [{opt.patch_class:22s}] "
                  f"score={opt.rank_score:2d}  {opt.pattern_name}")
            if opt.notes:
                for n in opt.notes:
                    print(f"    ! {n}")

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def status(self) -> None:
        """Print a summary of the operator subsystem state."""
        print("=" * 60)
        print(f"WikiOperator — {self.username}")
        print("=" * 60)

        # Account
        try:
            acct = self.account()
            ts = acct.template_summary
            print(f"\nAccount ({acct.username})")
            print(f"  Total edits tracked : {acct.total_edits:,}")
            print(f"  By project          : {acct.by_project}")
            print(f"  Template-ns edits   : {ts.total_template_ns_edits:,}")
            print(f"  Infobox edits       : {ts.total_infobox_edits:,}")
            if ts.top_templates_edited:
                top3 = ts.top_templates_edited[:3]
                print(f"  Top templates       : {[t['title'] for t in top3]}")
        except FileNotFoundError:
            print("\nAccount: no artifact cache found — run account(force_refresh=True)")

        # Template index
        idx_path = (
            Path(__file__).resolve().parents[1]
            / "data" / "template_index"
            / "template_index.json"
        )
        if idx_path.exists():
            with open(idx_path, encoding="utf-8") as f:
                idx = json.load(f)
            print(f"\nTemplate index      : {idx.get('total', 0)} templates cached")
        else:
            print("\nTemplate index      : empty (run index([...]) to populate)")

        # Pattern library
        print(f"\nPattern library     : {len(PATTERN_LIBRARY)} patterns")
        safe_count   = sum(1 for p in PATTERN_LIBRARY if p.risk == "safe")
        review_count = sum(1 for p in PATTERN_LIBRARY if p.risk == "review")
        risky_count  = sum(1 for p in PATTERN_LIBRARY if p.risk == "risky")
        print(f"  safe={safe_count}  review={review_count}  risky={risky_count}")

        # Phase 2 additions
        from apps.language_pipeline.anti_patterns import ANTI_PATTERN_LIBRARY
        print(f"\nAnti-pattern library: {len(ANTI_PATTERN_LIBRARY)} entries")
        print(f"Dossiers            : {list(DOSSIER_REGISTRY.keys())}")
        print("\nSandbox             : ready (live API)")
        print("=" * 60)
