# Cross-Language Normalization
All syntactical elements have been abstracted into pure topological geometries:
- `Fan-in` (Imports, Requires, Includes)
- `Fan-out` (Exports, Returns)
- `Nodes` (Functions, Methods, Classes)
- `Guards` (Asserts, Explicit Err Checks)
- `Exceptions` (Try/Catch, Pcall, Panic recovers)
- `Traces` (Decorators, Explicit ID tags, Structured TODOs)

These proxies allow structural comparisons between JS, Lua, Go, and Python independent of runtime semantics.
