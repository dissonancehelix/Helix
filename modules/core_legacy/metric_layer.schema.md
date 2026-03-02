# Metric Layer Schema
`metric_layer`:
- `eligible`: boolean
- `metric_kind`: string|null ("threshold_ratio", "margin", "rate_vs_rate", "distance_to_critical", "unknown")
- `control_parameter`: string|null
- `threshold_parameter`: string|null
- `normalization`: string|null
- `distance_value`: number|null
- `distance_definition`: string
- `units`: string|null
- `dimensionless`: boolean|null
- `provenance`:
  - `used_fields`: [string]
  - `assumptions`: [string]
  - `external_knowledge`: boolean
