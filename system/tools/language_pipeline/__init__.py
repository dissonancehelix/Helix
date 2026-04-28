"""
model/domains/language/wikipedia — Wikipedia operator subsystem.

Operator account: Dissident93 (en.wikipedia.org, wikidata, commons)

Subsystems:
  account_ingest/   — wraps ingestion layer, extracts template-focused patterns
  template_index/   — fetches and indexes template source, TemplateData, /doc pages
  sandbox/          — MediaWiki parse/expandtemplates validation surface
  pattern_library/  — reusable wikitext/template patterns from operator edit history
  issue_solver/     — operator-facing tools (inspect, validate, compare, suggest)
  operator/         — top-level interface entry point

No live Wikipedia edits are performed by any module in this subsystem.
All write operations target local Helix artifacts only.
"""

OPERATOR_USERNAME = "Dissident93"
ENWIKI_API = "https://en.wikipedia.org/w/api.php"

