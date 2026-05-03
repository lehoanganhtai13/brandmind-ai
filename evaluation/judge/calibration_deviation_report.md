# Calibration Deviation Report — Step 4-bis Phase 2

**Golden labels source**: `evaluation/judge/golden_labels.json` (labeled by `claude-with-project-context` on 2026-05-04)
**Training transcripts** (used for calibration): brandmind_linh_r10_20260430, brandmind_linh_r12_20260502, brandmind_linh_r13_20260503
**Hold-out transcripts** (held back for Phase 4): brandmind_linh_phase_a_iso_v4_20260504_0246

Each cell counts (criterion × transcript) tuples where the production judge's verdict differs from golden in the named direction. ``aligned`` means agreement; the remaining columns name the disagreement kind.

### Judge: `claude-sonnet-4.6`

**Aggregate alignment with golden across training labels: 75.8%**

| Criterion | aligned | judge lenient (MET when golden=UNMET) | judge strict (UNMET when golden=MET) | other |
|-----------|---------|---------------------------------------|-------------------------------------|-------|
| M2-E1 | 3 | 0 | 0 | 0 |
| M2-S2 | 2 | 0 | 1 | 0 |
| P2-S2 | 3 | 0 | 0 | 0 |
| P3-E1 | 3 | 0 | 0 | 0 |
| P3-S3 | 3 | 0 | 0 | 0 |
| P4-E2 | 3 | 0 | 0 | 0 |
| P4-S3 | 3 | 0 | 0 | 0 |
| P4-S4 | 3 | 0 | 0 | 0 |
| Q1-S4 | 0 | 0 | 3 | 0 |
| Q3-S3 | 0 | 0 | 3 | 0 |
| Q4-E2 | 2 | 0 | 1 | 0 |

**Pattern**: total lenient = 0, total strict = 8, dominant deviation = strict

### Judge: `gemini-3.1-pro-preview`

**Aggregate alignment with golden across training labels: 51.5%**

| Criterion | aligned | judge lenient (MET when golden=UNMET) | judge strict (UNMET when golden=MET) | other |
|-----------|---------|---------------------------------------|-------------------------------------|-------|
| M2-E1 | 1 | 2 | 0 | 0 |
| M2-S2 | 1 | 2 | 0 | 0 |
| P2-S2 | 0 | 0 | 0 | 3 |
| P3-E1 | 2 | 1 | 0 | 0 |
| P3-S3 | 2 | 1 | 0 | 0 |
| P4-E2 | 1 | 2 | 0 | 0 |
| P4-S3 | 1 | 2 | 0 | 0 |
| P4-S4 | 1 | 2 | 0 | 0 |
| Q1-S4 | 3 | 0 | 0 | 0 |
| Q3-S3 | 3 | 0 | 0 | 0 |
| Q4-E2 | 2 | 1 | 0 | 0 |

**Pattern**: total lenient = 13, total strict = 0, dominant deviation = lenient

### Judge: `gpt-5.4`

**Aggregate alignment with golden across training labels: 66.7%**

| Criterion | aligned | judge lenient (MET when golden=UNMET) | judge strict (UNMET when golden=MET) | other |
|-----------|---------|---------------------------------------|-------------------------------------|-------|
| M2-E1 | 3 | 0 | 0 | 0 |
| M2-S2 | 2 | 0 | 1 | 0 |
| P2-S2 | 3 | 0 | 0 | 0 |
| P3-E1 | 2 | 1 | 0 | 0 |
| P3-S3 | 2 | 1 | 0 | 0 |
| P4-E2 | 2 | 1 | 0 | 0 |
| P4-S3 | 2 | 1 | 0 | 0 |
| P4-S4 | 2 | 1 | 0 | 0 |
| Q1-S4 | 0 | 0 | 3 | 0 |
| Q3-S3 | 1 | 0 | 2 | 0 |
| Q4-E2 | 3 | 0 | 0 | 0 |

**Pattern**: total lenient = 5, total strict = 6, dominant deviation = strict

## Cross-judge family pattern summary

| Criterion | claude lenient/strict | gemini lenient/strict | gpt lenient/strict |
|-----------|----------------------|---------------------|---|
| M2-E1 | 0/0 | 2/0 | 0/0 |
| M2-S2 | 0/1 | 2/0 | 0/1 |
| P2-S2 | 0/0 | 0/0 | 0/0 |
| P3-E1 | 0/0 | 1/0 | 1/0 |
| P3-S3 | 0/0 | 1/0 | 1/0 |
| P4-E2 | 0/0 | 2/0 | 1/0 |
| P4-S3 | 0/0 | 2/0 | 1/0 |
| P4-S4 | 0/0 | 2/0 | 1/0 |
| Q1-S4 | 0/3 | 0/0 | 0/3 |
| Q3-S3 | 0/3 | 0/0 | 0/2 |
| Q4-E2 | 0/1 | 1/0 | 0/0 |

## Phase 3 prompt-adjustment targeting hints

### `claude-sonnet-4.6`

Top lenient deviations (judge MET, golden UNMET):

Top strict deviations (judge UNMET, golden MET):
- `Q1-S4`: 3 strict labels
- `Q3-S3`: 3 strict labels
- `Q4-E2`: 1 strict labels

### `gemini-3.1-pro-preview`

Top lenient deviations (judge MET, golden UNMET):
- `M2-S2`: 2 lenient labels
- `P4-S3`: 2 lenient labels
- `P4-S4`: 2 lenient labels

Top strict deviations (judge UNMET, golden MET):

### `gpt-5.4`

Top lenient deviations (judge MET, golden UNMET):
- `P3-E1`: 1 lenient labels
- `P3-S3`: 1 lenient labels
- `P4-S3`: 1 lenient labels

Top strict deviations (judge UNMET, golden MET):
- `Q1-S4`: 3 strict labels
- `Q3-S3`: 2 strict labels
- `M2-S2`: 1 strict labels
