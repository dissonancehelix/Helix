"""
Sandbox / validation layer — MediaWiki parse and expandtemplates surfaces.

Uses official API actions only:
  - action=expandtemplates  →  expand template calls to wikitext
  - action=parse            →  full parser output (wikitext → HTML + sections)

Purpose:
  - Test a proposed template rewrite before committing
  - Compare before/after output to catch regressions
  - Validate whether a conditional/fallback behaves as expected
  - Detect changed output structure (headings, tables, infobox cells)

No HTML scraping as a primary source. Parser output is the ground truth here.
Never writes to Wikipedia.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from apps.language_pipeline import ENWIKI_API

_USER_AGENT = "HelixWikiOperator/1.0 (Research; User:Dissident93)"


@dataclass
class ValidationResult:
    """Result of a single parse or expandtemplates call."""
    input_wikitext: str
    expanded_wikitext: str | None    # from expandtemplates
    parsed_html: str | None          # from parse
    sections: list[str]              # section headings detected
    templates_used: list[str]        # templates expanded during parse
    errors: list[str]
    warnings: list[str]
    success: bool

    def summary(self) -> str:
        lines = [f"Success: {self.success}"]
        if self.errors:
            lines.append(f"Errors: {self.errors}")
        if self.warnings:
            lines.append(f"Warnings: {self.warnings}")
        if self.sections:
            lines.append(f"Sections: {self.sections}")
        if self.templates_used:
            lines.append(f"Templates used: {self.templates_used[:10]}")
        return "\n".join(lines)


@dataclass
class CompareResult:
    """Before/after comparison of two wikitext snippets through the parser."""
    before_result: ValidationResult
    after_result: ValidationResult
    html_changed: bool
    expanded_changed: bool
    sections_added: list[str]
    sections_removed: list[str]
    templates_added: list[str]
    templates_removed: list[str]
    risk_level: str    # "safe" | "review" | "risky"
    notes: list[str]

    def summary(self) -> str:
        lines = [
            f"HTML changed:     {self.html_changed}",
            f"Expanded changed: {self.expanded_changed}",
            f"Risk level:       {self.risk_level}",
        ]
        if self.sections_added:
            lines.append(f"Sections added:   {self.sections_added}")
        if self.sections_removed:
            lines.append(f"Sections removed: {self.sections_removed}")
        if self.templates_added:
            lines.append(f"Templates added:  {self.templates_added}")
        if self.templates_removed:
            lines.append(f"Templates removed:{self.templates_removed}")
        if self.notes:
            lines.append("Notes:")
            lines.extend(f"  - {n}" for n in self.notes)
        return "\n".join(lines)


class SandboxValidator:
    """
    Validates wikitext snippets and template changes using the MediaWiki API.

    Usage:
        sb = SandboxValidator()
        result = sb.expand("{{PAGENAME|foo}}")
        result = sb.parse("== Section ==\n{{Infobox person|name=Test}}")
        cmp    = sb.compare(old_wikitext, new_wikitext, title="Draft:Test")
    """

    def __init__(self, api_endpoint: str = ENWIKI_API):
        self.api = api_endpoint
        self.headers = {"User-Agent": _USER_AGENT}

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def expand(self, wikitext: str, title: str = "Sandbox") -> ValidationResult:
        """
        Run wikitext through action=expandtemplates.
        Returns expanded wikitext without full HTML parse overhead.
        Useful for checking template argument resolution, #if/#switch logic,
        fallback chains, and conditional output.
        """
        errors, warnings = [], []
        expanded = None
        try:
            data = self._api_post({
                "action": "expandtemplates",
                "text": wikitext,
                "title": title,
                "prop": "wikitext|warnings",
            })
            expanded = data.get("expandtemplates", {}).get("wikitext", "")
            raw_warnings = data.get("expandtemplates", {}).get("warnings", [])
            for w in (raw_warnings if isinstance(raw_warnings, list) else []):
                warnings.append(str(w))
            if "error" in data:
                errors.append(data["error"].get("info", str(data["error"])))
        except Exception as e:
            errors.append(str(e))

        return ValidationResult(
            input_wikitext=wikitext,
            expanded_wikitext=expanded,
            parsed_html=None,
            sections=[],
            templates_used=[],
            errors=errors,
            warnings=warnings,
            success=not errors,
        )

    def parse(self, wikitext: str, title: str = "Sandbox") -> ValidationResult:
        """
        Run wikitext through action=parse.
        Returns HTML output, section list, and templates used.
        Heavier than expand() but gives full parser output.
        """
        errors, warnings, sections, templates_used = [], [], [], []
        html = None
        try:
            data = self._api_post({
                "action": "parse",
                "text": wikitext,
                "title": title,
                "prop": "text|sections|templates|warnings",
                "disablelimitreport": "1",
            })
            parse_data = data.get("parse", {})
            html = parse_data.get("text", {}).get("*") or parse_data.get("text", "")
            sections = [
                s.get("line", "") for s in parse_data.get("sections", [])
            ]
            templates_used = [
                t.get("*", "") for t in parse_data.get("templates", [])
            ]
            raw_warnings = parse_data.get("warnings", {})
            for module, wdata in (raw_warnings.items() if isinstance(raw_warnings, dict) else []):
                warnings.append(f"{module}: {wdata.get('*', wdata)}")
            if "error" in data:
                errors.append(data["error"].get("info", str(data["error"])))
        except Exception as e:
            errors.append(str(e))

        return ValidationResult(
            input_wikitext=wikitext,
            expanded_wikitext=None,
            parsed_html=html,
            sections=sections,
            templates_used=templates_used,
            errors=errors,
            warnings=warnings,
            success=not errors,
        )

    def compare(
        self,
        before: str,
        after: str,
        title: str = "Sandbox",
        mode: str = "expand",   # "expand" | "parse"
    ) -> CompareResult:
        """
        Compare before/after wikitext through the parser.

        mode="expand"  is faster — checks template expansion only.
        mode="parse"   is more thorough — checks HTML, sections, templates.

        Risk classification:
          "safe"    — no output change detected
          "review"  — output changed but no structural diff (sections/templates same)
          "risky"   — sections or template set changed
        """
        if mode == "parse":
            r_before = self.parse(before, title)
            r_after  = self.parse(after,  title)
        else:
            r_before = self.expand(before, title)
            r_after  = self.expand(after,  title)

        exp_changed  = (r_before.expanded_wikitext or "") != (r_after.expanded_wikitext or "")
        html_changed = self._html_text(r_before) != self._html_text(r_after)

        secs_before = set(r_before.sections)
        secs_after  = set(r_after.sections)
        tmpl_before = set(r_before.templates_used)
        tmpl_after  = set(r_after.templates_used)

        secs_added    = sorted(secs_after  - secs_before)
        secs_removed  = sorted(secs_before - secs_after)
        tmpl_added    = sorted(tmpl_after  - tmpl_before)
        tmpl_removed  = sorted(tmpl_before - tmpl_after)

        notes: list[str] = []
        if not r_before.success:
            notes.append(f"Before had errors: {r_before.errors}")
        if not r_after.success:
            notes.append(f"After has errors: {r_after.errors}")
        if r_after.warnings and not r_before.warnings:
            notes.append(f"After introduced warnings: {r_after.warnings}")

        changed = exp_changed or html_changed
        structural = secs_added or secs_removed or tmpl_added or tmpl_removed
        if not changed:
            risk = "safe"
        elif structural:
            risk = "risky"
        else:
            risk = "review"

        return CompareResult(
            before_result=r_before,
            after_result=r_after,
            html_changed=html_changed,
            expanded_changed=exp_changed,
            sections_added=secs_added,
            sections_removed=secs_removed,
            templates_added=tmpl_added,
            templates_removed=tmpl_removed,
            risk_level=risk,
            notes=notes,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _api_post(self, params: dict) -> dict:
        params["format"] = "json"
        encoded = urllib.parse.urlencode(params).encode("utf-8")
        req = urllib.request.Request(
            self.api,
            data=encoded,
            headers={**self.headers, "Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))

    @staticmethod
    def _html_text(result: ValidationResult) -> str:
        """Strip HTML tags for text-level comparison."""
        if not result.parsed_html:
            return result.expanded_wikitext or ""
        return re.sub(r"<[^>]+>", "", result.parsed_html).strip()
