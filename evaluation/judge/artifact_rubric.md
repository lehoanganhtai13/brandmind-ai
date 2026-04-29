# Artifact Content Correctness Rubric (M-6.5)

A judge LLM scores each Phase 5 artifact against the rubric below.
For every criterion the judge returns one of `MET`, `UNMET`, or
`CANNOT_ASSESS`, plus an evidence quote and a one-sentence
explanation. Per-artifact verdict is `PASS` when at least 3 criteria
are `MET`; otherwise `FAIL`.

The judge sees both the artifact's extracted content and the recent
transcript context. The rubric tests *content correctness in the
context of THIS session* — not artifact aesthetics, length, or
formatting (those are handled by the M-4 structural check).

## Brand Key one-pager (image)

The Brand Key visual is judged by OCR-extracted text.

- **BK-1 — Insight match.** The Insight component on the image
  reflects the consumer insight discussed during Phase 1 of the
  transcript. UNMET when the on-image text reads as a generic
  insight that could fit any brand.
- **BK-2 — Discriminator/POD match.** The Discriminator (Point of
  Difference) on the image matches the POD agreed during Phase 2
  positioning. UNMET when the image shows a different POD or a
  table-stakes capability instead of a real differentiator.
- **BK-3 — Essence match.** The Brand Essence / Mantra on the image
  matches the essence agreed in Phase 2 (single Brand Mantra, no
  competing alternatives). UNMET when the image shows a different
  essence than the transcript's final agreement.
- **BK-4 — Target match.** The Target component reflects the
  audience the agent and user converged on, including the weekday
  / corporate / family segment when applicable.

## Strategy document (DOCX)

Judged by paragraph text extracted with python-docx.

- **DOC-1 — Problem statement match.** The Business Context section
  reproduces or paraphrases the Phase 0 problem statement that the
  agent and user agreed on, including specifics (location, budget
  tier, weekday traffic gap, etc.).
- **DOC-2 — Positioning consistency.** The Brand Positioning
  section uses the Phase 2 positioning statement and the agreed POD.
  No contradictions with the Brand Identity section.
- **DOC-3 — Identity continuity.** The Brand Identity section
  describes the personality, visual direction, and verbal tone that
  the agent and user converged on in Phase 3 — not a generic
  template.
- **DOC-4 — KPI / Roadmap alignment.** The Implementation Roadmap
  and KPI Framework sections reflect the budget tier stated in
  Phase 0 and the metrics discussed in Phase 5. Numbers are
  compatible with the budget (no enterprise-tier targets for a
  Starter budget).

## Executive presentation (PPTX)

Judged by slide titles and body text extracted with python-pptx.

- **PPT-1 — Flow logic.** Slide order tells a coherent
  problem → research → positioning → identity → execution → KPI
  story. UNMET when slides repeat or skip stages.
- **PPT-2 — No internal contradictions.** Across slides the deck
  does not present conflicting positioning, conflicting essence
  statements, or conflicting personality archetypes. UNMET when
  two slides give different values for the same brand attribute.
- **PPT-3 — Match to strategy doc.** The deck's positioning,
  identity, and KPI slides align with the same content in the DOCX
  (or in the transcript if the DOCX is absent).
- **PPT-4 — Actionable close.** The final 1-3 slides include
  concrete next-step content: roadmap, KPIs, investment summary,
  immediate actions. UNMET when the deck closes on rhetoric without
  concrete deliverables.

## KPI tracking spreadsheet (XLSX)

Judged by sheet rows × columns flattened from openpyxl.

- **KPI-1 — Metrics traceable.** Every metric listed in the sheet
  was mentioned or implied in the Phase 5 KPI discussion in the
  transcript. UNMET when the sheet contains generic template
  metrics not tied to this brand.
- **KPI-2 — Budget-realistic targets.** Target values respect the
  stated budget tier (Starter / Growth / Enterprise). UNMET when
  enterprise-scale targets appear under a Starter budget (e.g.
  "+500% Instagram followers" on 50-80M VND/month).
- **KPI-3 — Cadence present.** A review-frequency column or row is
  populated for each metric (weekly, monthly, quarterly).
- **KPI-4 — Baseline or honest marker.** Each metric carries a
  baseline value or an explicit "no data — measure pre-launch"
  marker. UNMET when targets appear without any baseline anchor
  (e.g. "+25%" with no current state).
