# core/tools/

Cross-domain operational tools live here: workspace sensors, shared runners,
tool registry, and utilities that do not belong to one domain.

Before adding a new script, read `core/tools/TOOL_INDEX.yaml` and reuse an
existing entrypoint if one already owns the job.

## Tool Ownership

- Shared infrastructure stays in `core/tools/`.
- Domain-owned workflows live in `domains/<domain>/tools/`.
- Generated output lands in the owning domain capsule or a cross-domain lab.
- Reports are review artifacts, not canon.

## Tool Roles

- `canonical`: the normal entrypoint for a workflow.
- `stage_helper`: a narrow helper called by a canonical pipeline or used for one stage.
- `legacy`: preserved for compatibility or reference; avoid for new work.
- `one_off_archive`: historical or seed script; do not extend unless deliberately resurrecting it.

## Rules

1. Tools produce evidence, proposals, reports, or derived artifacts. They do not redefine canon.
2. Original dumps belong under `archive/raw/`.
3. Normalized and derived domain artifacts belong under `domains/<domain>/data/`.
4. Reports belong under `domains/<domain>/reports/`, `labs/reports/`, or `core/reports/` for core sensors.
5. Any writeback to an external app requires identity, diff, backup, rollback, evidence, and explicit operator approval.
6. If a workflow is a pipeline of helpers, document the pipeline here instead of adding another top-level script.

## First Tools To Check

- Workspace audit: `workstation_bridge`
- Boundary check: `boundary_check`
- Domain pipelines: see each `domains/<domain>/tools/` folder and `TOOL_INDEX.yaml`.
