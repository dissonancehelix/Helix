# Domain Mapping Table

| Domain | FanIn | CycleDensity | ValidationCoverage | ExceptionDensity |
|---|---|---|---|---|
| **Microservices** | Dependency concentration | Circular service calls | Circuit breakers/Monitoring | Unlogged timeouts |
| **Pub/Sub Systems** | Subscriber concentration | Cascading trigger loops | Schema checks | Dead letters silently dropped |
| **Financial Contagion**| Debt exposure | Insolvency cascade (Debt Loops) | Reserve Ratios (Capital Limits)| Unreported defaults |
