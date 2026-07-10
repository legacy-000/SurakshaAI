# Data Gap Analysis - Suraksha AI

## Identified Gaps

| Gap ID | Missing Dataset | Impact | Mitigation |
|--------|----------------|--------|------------|
| GAP-01 | Cross-case person identifier | Network analysis uses fuzzy matching | 4-tier confidence system (exact/deterministic/probable/unresolved) |
| GAP-02 | Accused demographics (occupation, religion, caste) | Limited sociological cross-tabs | Use available AgeYear + GenderID only |
| GAP-03 | Financial transactions | R7 impossible | Interface stub with synthetic demo data |
| GAP-04 | Population denominators | Rate comparisons impossible | Raw counts only, explicitly noted |
| GAP-05 | Structured modus operandi | MO similarity uses text embeddings | Labeled as "text-based similarity" |

## Handling Strategy
- All gaps are explicitly documented in the UI
- Confidence indicators accompany every uncertain result
- "Correlation does not imply causation" banner displayed on all analytics
